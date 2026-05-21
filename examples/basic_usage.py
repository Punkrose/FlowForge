"""
FlowForge - Basic Usage Example

Demonstrates how to use the FlowForge class to automate a browser task
from a natural language description.
"""

import asyncio
import os


async def main() -> None:
    """Run a simple browser automation task."""
    from flowforge import FlowForge

    # Initialize with your LLM API credentials
    engine = FlowForge(
        api_key=os.environ.get("OPENAI_API_KEY", "your-api-key-here"),
        base_url=os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1"),
        model=os.environ.get("OPENAI_MODEL", "gpt-4o"),
    )

    # Define the task in natural language
    task = """
    Go to https://news.ycombinator.com and extract the titles of the
    top 5 stories on the front page.
    """

    print("Starting FlowForge task...")
    print(f"Task: {task.strip()}\n")

    # Run the task
    result = await engine.run(
        task_description=task,
        headless=True,
        max_steps=10,
        timeout_seconds=120,
    )

    # Display results
    print("=" * 60)
    print(f"Task ID:    {result.task_id}")
    print(f"Status:     {result.status.value}")
    print(f"Steps:      {result.steps_completed}/{len(result.steps)} completed")
    print(f"Duration:   {result.total_duration_ms:.0f}ms" if result.total_duration_ms else "")
    print("=" * 60)

    print("\nStep Details:")
    for step in result.steps:
        icon = "✓" if step.status.value == "completed" else "✗"
        print(f"  {icon} [{step.action}] {step.description}")
        if step.result:
            print(f"    → {step.result[:200]}")
        if step.error:
            print(f"    ✗ Error: {step.error}")

    if result.summary:
        print(f"\nSummary:\n{result.summary}")

    if result.screenshots:
        print(f"\nScreenshots saved:")
        for path in result.screenshots:
            print(f"  📷 {path}")


def run_sync_example() -> None:
    """Synchronous usage example (for non-async scripts)."""
    from flowforge import FlowForge

    engine = FlowForge(
        api_key=os.environ.get("OPENAI_API_KEY", "your-api-key-here"),
    )

    # Use run_sync() for synchronous code
    result = engine.run_sync(
        task_description="Go to https://example.com and take a screenshot",
        headless=True,
    )
    print(f"Result: {result.status.value}")


if __name__ == "__main__":
    asyncio.run(main())
