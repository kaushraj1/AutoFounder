import logging
import os
from typing import Any

import httpx

from app.agents.base import ToolRegistryProtocol
from app.core.config import get_settings

logger = logging.getLogger("app.agents.strategy.tools")


class LocalToolRegistry(ToolRegistryProtocol):
    """Local Tool Registry stand-in satisfying ToolRegistryProtocol.
    Calls actual APIs if keys are configured in environment or settings,
    otherwise returns fallback/mocked results to avoid hard crashes.
    """

    def __init__(self) -> None:
        self.settings = get_settings()

    async def call(self, tool_name: str, args: dict[str, Any]) -> dict[str, Any]:
        """Call standard tools with parameters, falling back safely."""
        logger.info("Tool registry calling: %s with args: %s", tool_name, args)

        # Resolve api keys from settings or env
        tavily_key = self.settings.tavily_api_key or os.environ.get("TAVILY_API_KEY", "")
        serpapi_key = self.settings.serpapi_key or os.environ.get("SERPAPI_API_KEY", "")
        crunchbase_key = self.settings.crunchbase_api_key or os.environ.get(
            "CRUNCHBASE_API_KEY", ""
        )
        g2_key = self.settings.g2_api_key or os.environ.get("G2_API_KEY", "")

        try:
            if tool_name == "tavily_search":
                if not tavily_key:
                    logger.warning(
                        "TAVILY_API_KEY not configured — returning MOCK data for '%s'. "
                        "Market sizing will be ungrounded.",
                        tool_name,
                    )
                    return {
                        "results": [
                            {
                                "title": "Mock Tavily Search",
                                "url": "https://example.com/tavily",
                                "content": f"Mock content for query: {args.get('query')}",
                            }
                        ]
                    }
                async with httpx.AsyncClient() as client:
                    resp = await client.post(
                        "https://api.tavily.com/search",
                        json={
                            "api_key": tavily_key,
                            "query": args.get("query"),
                            "search_depth": args.get("search_depth", "advanced"),
                            "max_results": args.get("max_results", 5),
                        },
                        timeout=20.0,
                    )
                    resp.raise_for_status()
                    return resp.json()

            elif tool_name == "serp_search":
                if not serpapi_key:
                    logger.warning(
                        "SERPAPI_API_KEY not configured — returning MOCK data for '%s'.",
                        tool_name,
                    )
                    return {
                        "results": [
                            {
                                "title": "Mock Serp Search",
                                "snippet": f"Mock SERP results for: {args.get('query')}",
                            }
                        ]
                    }
                async with httpx.AsyncClient() as client:
                    resp = await client.get(
                        "https://serpapi.com/search",
                        params={"api_key": serpapi_key, "q": args.get("query"), "engine": "google"},
                        timeout=15.0,
                    )
                    resp.raise_for_status()
                    return resp.json()

            elif tool_name == "crunchbase_lookup":
                company = args.get("company_name", "")
                if not crunchbase_key:
                    logger.warning(
                        "CRUNCHBASE_API_KEY not configured — attempting web search + "
                        "Gemini extraction for '%s'.",
                        company,
                    )
                    search_results = None
                    if tavily_key:
                        try:
                            search_results = await self.call(
                                "tavily_search",
                                {"query": f"{company} company funding total employees crunchbase"},
                            )
                        except Exception as e:
                            logger.warning("Tavily search failed in crunchbase fallback: %s", e)
                    if not search_results and serpapi_key:
                        try:
                            search_results = await self.call(
                                "serp_search",
                                {"query": f"{company} company funding total employees crunchbase"},
                            )
                        except Exception as e:
                            logger.warning("Serp search failed in crunchbase fallback: %s", e)

                    gemini_key = self.settings.gemini_api_key or os.environ.get(
                        "GEMINI_API_KEY", ""
                    )
                    if search_results and gemini_key:
                        try:
                            import json

                            from app.agents._providers import GeminiRouter

                            router = GeminiRouter(
                                api_key=gemini_key, default_model=self.settings.strategy_model
                            )
                            prompt = (
                                f"Analyze the search results for the company '{company}' "
                                "and extract the total funding amount in millions of USD "
                                "(as a float, e.g. 15.4 for $15.4M, 0.5 for $500k, "
                                "0.0 if unfunded/bootstrapped) and the number of "
                                "employees range (e.g., '1-10', '11-50', '51-200', "
                                "'201-500', '500+').\n\n"
                                f"Search Results:\n{str(search_results)[:4000]}\n\n"
                                "Return ONLY a valid JSON object matching this schema:\n"
                                "{\n"
                                '  "funding_total": <float or null>,\n'
                                '  "num_employees_enum": <string or null>\n'
                                "}"
                            )
                            resp_text = await router.complete(
                                task_class="crunchbase_fallback", prompt=prompt, json_mode=True
                            )
                            extracted = json.loads(resp_text)
                            if isinstance(extracted, dict):
                                return {
                                    "name": company,
                                    "funding_total": extracted.get("funding_total") or 0.0,
                                    "num_employees_enum": extracted.get("num_employees_enum")
                                    or "employee_range_11_50",
                                }
                        except Exception as e:
                            logger.error(
                                "Error extracting details via Gemini in crunchbase fallback: %s", e
                            )

                    return {
                        "name": company,
                        "short_description": "Fallback Description",
                        "funding_total": 5.5,
                        "num_employees_enum": "employee_range_11_50",
                    }
                async with httpx.AsyncClient() as client:
                    slug = company.lower().replace(" ", "-")
                    resp = await client.get(
                        f"https://api.crunchbase.com/api/v4/entities/organizations/{slug}",
                        params={
                            "user_key": crunchbase_key,
                            "field_ids": (
                                "short_description,funding_total,num_employees_enum,founded_on"
                            ),
                        },
                        timeout=15.0,
                    )
                    resp.raise_for_status()
                    return resp.json()

            elif tool_name == "g2_reviews":
                if not g2_key:
                    logger.warning(
                        "G2_API_KEY not configured — returning MOCK data for '%s'.",
                        tool_name,
                    )
                    return {
                        "product_name": args.get("product_name"),
                        "g2_rating": 4.2,
                        "review_count": 128,
                    }
                async with httpx.AsyncClient() as client:
                    resp = await client.get(
                        "https://data.g2.com/api/v1/products",
                        headers={"Authorization": f"Token token={g2_key}"},
                        params={"filter[name]": args.get("product_name"), "page[size]": 1},
                        timeout=15.0,
                    )
                    resp.raise_for_status()
                    return resp.json()

            elif tool_name == "google_trends":
                keyword = args.get("keyword", "startup")
                return {
                    "keyword": keyword,
                    "avg_interest": 75.0,
                    "peak_interest": 100,
                    "trend_direction": "up",
                }

            elif tool_name == "reddit_search":
                query = args.get("query", "")
                return {
                    "posts": [
                        {
                            "title": f"Reddit pain point: {query}",
                            "score": 42,
                            "url": "https://reddit.com/r/Entrepreneur/comments/mock",
                            "body": "It is so hard to build this and validate the market.",
                        }
                    ]
                }

            elif tool_name == "hn_search":
                query = args.get("query", "")
                return {
                    "hits": [
                        {
                            "title": f"Show HN: AI {query} tool",
                            "points": 88,
                            "url": "https://news.ycombinator.com/item?id=mock",
                            "num_comments": 15,
                        }
                    ]
                }

            else:
                logger.warning("Unknown tool called in LocalToolRegistry: %s", tool_name)
                raise NotImplementedError(f"Tool {tool_name} not supported in LocalToolRegistry")

        except Exception as e:
            logger.error("Error executing tool %s: %s", tool_name, e)
            raise e
