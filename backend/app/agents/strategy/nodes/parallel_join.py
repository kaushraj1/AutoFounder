import logging
from typing import Any

from app.agents.strategy.schema import StrategistState

logger = logging.getLogger("app.agents.strategy.parallel_join")


async def parallel_join(state: StrategistState) -> dict[str, Any]:
    """Synchronization barrier for parallel research branches."""
    logger.info("Parallel research join node reached for run_id: %s", state.run_id)
    return {}
