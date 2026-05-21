"""
FlowForge API Server Example

Shows how to start the FastAPI server and interact with it via HTTP.

Usage:
    # Start the server
    python examples/api_server.py

    # Or use uvicorn directly
    uvicorn flowforge.api.server:app --host 0.0.0.0 --port 8080

    # Create a task via curl
    curl -X POST http://localhost:8080/api/tasks \\
         -H "Content-Type: application/json" \\
         -d '{"task": "Go to https://example.com and take a screenshot"}'
"""

import os
import sys


def main() -> None:
    """Start the FlowForge API server."""
    # Ensure environment variables are set
    required = ["FLOWFORGE_API_KEY", "OPENAI_API_KEY"]
    if not any(os.environ.get(k) for k in required):
        print("Warning: No LLM API key found. Set FLOWFORGE_API_KEY or OPENAI_API_KEY.")
        print("  export FLOWFORGE_API_KEY=sk-...")
        print()

    # Ensure CloakBrowser / Playwright is available
    try:
        import playwright_core  # noqa: F401
    except ImportError:
        print("Note: playwright-core not installed. Install with:")
        print("  pip install playwright-core")
        print("  playwright install chromium")
        print()

    print("Starting FlowForge API server on http://0.0.0.0:8080")
    print("API docs available at: http://localhost:8080/docs")
    print("Press Ctrl+C to stop.")
    print()

    import uvicorn

    uvicorn.run(
        "flowforge.api.server:app",
        host="0.0.0.0",
        port=8080,
        log_level="info",
    )


if __name__ == "__main__":
    main()
