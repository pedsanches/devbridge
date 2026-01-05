import logging

from mcp.server.fastmcp import FastMCP

# Initialize FastMCP
mcp = FastMCP("DevBridge Internal Tools")
logger = logging.getLogger("mcp_server")


@mcp.tool()
def check_privacy(text: str) -> str:
    """
    Check text for PII using the project's Presidio configuration.
    Returns the redacted text and a report of what was found.
    """
    # Import locally to avoid circular imports during startup if any
    try:
        from presidio_analyzer import AnalyzerEngine
        from presidio_anonymizer import AnonymizerEngine

        analyzer = AnalyzerEngine()
        anonymizer = AnonymizerEngine()

        results = analyzer.analyze(
            text=text, language="en"
        )  # Defaulting to en for simplicity in MVP

        anonymized_result = anonymizer.anonymize(text=text, analyzer_results=results)

        found_entities = [r.entity_type for r in results]

        return f"Redacted: {anonymized_result.text}\nFound: {found_entities}"
    except ImportError:
        return "Error: Presidio dependencies not found in environment."
    except Exception as e:
        return f"Error running Presidio: {str(e)}"


@mcp.tool()
async def simulate_translation(diff: str, _context: str = "") -> str:
    """
    Simulate the 'Technical -> Business' translation agent on a given diff.
    Useful for testing prompt changes without triggering webhooks.
    """
    # In a real implementation, we would import the actual agent graph.
    # For this MVP, we will simulate the behavior or import the service if available.
    try:
        # Placeholder for actual agent import
        # from app.agents.translator import translate_diff
        # result = await translate_diff(diff, context)

        # Simulating response for now to prove connectivity
        return f"""
        [SIMULATION MODE]
        Based on the diff provided:
        '{diff[:100]}...'

        Analysis:
        This change appears to be a refactor of the backend auth logic.

        Business Value:
        Increases system security and maintainability, potentially reducing future login bugs.
        """
    except Exception as e:
        return f"Error during simulation: {str(e)}"


if __name__ == "__main__":
    mcp.run()
