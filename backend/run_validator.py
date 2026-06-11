import asyncio
from langgraph.checkpoint.memory import MemorySaver
from app.orchestrator.engine import OrchestratorEngine
from app.orchestrator.graph import build_run_graph

async def main():
    # Initialize engine in-memory (no database required)
    engine = OrchestratorEngine()
    engine._graph = build_run_graph(MemorySaver())
    
    idea = "A revolutionary AI-driven platform that automates startup idea validation, market research, and MVP generation."
    print(f"Submitting idea: '{idea}'...")
    
    # Start the run
    run_id = await engine.create_run(
        organization_id="00000000-0000-0000-0000-000000000000",
        workspace_id="00000000-0000-0000-0000-000000000000",
        idea_text=idea
    )
    print(f"\nRun created! ID: {run_id}")
    
    # Get the state to check the generated research report
    state = await engine.get_run_state(run_id)
    print("\n==================================================")
    print("        STRATEGY OUTPUT / RESEARCH REPORT         ")
    print("==================================================")
    print(state.get("strategy_output"))
    print("==================================================")

if __name__ == "__main__":
    asyncio.run(main())
