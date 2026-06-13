"""LangGraph StateGraph for the Marketing Agent (AF-044).

Graph topology (13 nodes):

  ingest_input
       │
  [router: fatal? → error_handler]
       │
  analyse_brand
       │
  [parallel fan-out: 6 generators run concurrently]
  generate_landing_page  ||  generate_seo_blogs      ||  generate_product_hunt_kit
  generate_social_posts  ||  generate_email_sequences ||  generate_visual_assets
       │
  parallel_join  (barrier — waits for all 6)
       │
  hallucination_check
       │
  [router: passed? → LCC | retry? → fan-out | exhausted? → error_handler]
       │
  launch_control_center  (HITL — 30-min timeout)
       │
  [router: approved/partial → schedule | rejected/timeout → error_handler]
       │
  schedule_posts
       │
  render_gtm_report → END

  error_handler → END  (terminal error sink)

Standalone usage (no platform needed):
    from app.agents.marketing.graph import build_marketer_graph
    import asyncio, json

    graph = build_marketer_graph()
    fixture = json.load(open("tests/fixtures/mock_products/shipfast.json"))
    result = asyncio.run(graph.ainvoke({
        **fixture,
        "approval_status": "approved",   # auto-approve for testing
        "errors": [],
        "llm_tokens_used": 0,
        "images_generated": 0,
    }))
    print(result["gtm_report_markdown"][:500])
"""

from __future__ import annotations

import logging

from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from app.agents.marketing.nodes.analyse_brand import analyse_brand
from app.agents.marketing.nodes.error_handler import error_handler
from app.agents.marketing.nodes.generate_email_sequences import generate_email_sequences
from app.agents.marketing.nodes.generate_landing_page import generate_landing_page
from app.agents.marketing.nodes.generate_product_hunt_kit import generate_product_hunt_kit
from app.agents.marketing.nodes.generate_seo_blogs import generate_seo_blogs
from app.agents.marketing.nodes.generate_social_posts import generate_social_posts
from app.agents.marketing.nodes.generate_visual_assets import generate_visual_assets
from app.agents.marketing.nodes.hallucination_check import hallucination_check
from app.agents.marketing.nodes.ingest_input import ingest_input
from app.agents.marketing.nodes.launch_control_center import launch_control_center
from app.agents.marketing.nodes.parallel_join import parallel_join
from app.agents.marketing.nodes.render_gtm_report import render_gtm_report
from app.agents.marketing.nodes.schedule_posts import schedule_posts
from app.agents.marketing.routers import (
    route_after_hallucination,
    route_after_hitl,
    route_after_ingest,
)
from app.agents.marketing.state import MarketerState

logger = logging.getLogger(__name__)


def build_marketer_graph() -> CompiledStateGraph:
    """Build and compile the Marketing Agent StateGraph.

    Returns a compiled LangGraph graph ready for .ainvoke() or .astream().
    """
    builder = StateGraph(MarketerState)

    # ---- Add all 13 nodes ----------------------------------------
    builder.add_node("ingest_input", ingest_input)
    builder.add_node("analyse_brand", analyse_brand)

    # 6 parallel generators
    builder.add_node("generate_landing_page", generate_landing_page)
    builder.add_node("generate_seo_blogs", generate_seo_blogs)
    builder.add_node("generate_product_hunt_kit", generate_product_hunt_kit)
    builder.add_node("generate_social_posts", generate_social_posts)
    builder.add_node("generate_email_sequences", generate_email_sequences)
    builder.add_node("generate_visual_assets", generate_visual_assets)

    builder.add_node("parallel_join", parallel_join)
    builder.add_node("hallucination_check", hallucination_check)
    builder.add_node("launch_control_center", launch_control_center)
    builder.add_node("schedule_posts", schedule_posts)
    builder.add_node("render_gtm_report", render_gtm_report)
    builder.add_node("error_handler", error_handler)

    # ---- Edges: START → ingest_input -------------------------------
    builder.add_edge(START, "ingest_input")

    # ---- ingest_input → analyse_brand or error_handler -------------
    builder.add_conditional_edges(
        "ingest_input",
        route_after_ingest,
        {"analyse_brand": "analyse_brand", "error_handler": "error_handler"},
    )

    # ---- analyse_brand → parallel fan-out (6 generators) ----------
    builder.add_edge("analyse_brand", "generate_landing_page")
    builder.add_edge("analyse_brand", "generate_seo_blogs")
    builder.add_edge("analyse_brand", "generate_product_hunt_kit")
    builder.add_edge("analyse_brand", "generate_social_posts")
    builder.add_edge("analyse_brand", "generate_email_sequences")
    builder.add_edge("analyse_brand", "generate_visual_assets")

    # ---- All 6 generators → parallel_join (barrier) ---------------
    builder.add_edge("generate_landing_page", "parallel_join")
    builder.add_edge("generate_seo_blogs", "parallel_join")
    builder.add_edge("generate_product_hunt_kit", "parallel_join")
    builder.add_edge("generate_social_posts", "parallel_join")
    builder.add_edge("generate_email_sequences", "parallel_join")
    builder.add_edge("generate_visual_assets", "parallel_join")

    # ---- parallel_join → hallucination_check -----------------------
    builder.add_edge("parallel_join", "hallucination_check")

    # ---- hallucination_check → LCC | re-generate | error -----------
    builder.add_conditional_edges(
        "hallucination_check",
        route_after_hallucination,
        {
            "launch_control_center": "launch_control_center",
            "generate_landing_page": "generate_landing_page",  # retry loop
            "error_handler": "error_handler",
        },
    )

    # ---- launch_control_center → schedule or error -----------------
    builder.add_conditional_edges(
        "launch_control_center",
        route_after_hitl,
        {
            "schedule_posts": "schedule_posts",
            "error_handler": "error_handler",
        },
    )

    # ---- schedule_posts → render_gtm_report → END ------------------
    builder.add_edge("schedule_posts", "render_gtm_report")
    builder.add_edge("render_gtm_report", END)

    # ---- Terminal: error_handler → END ----------------------------
    builder.add_edge("error_handler", END)

    return builder.compile()
