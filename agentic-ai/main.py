"""
K8S Agentic AI Service — Main Application Module.

FastAPI application entry point for the Kubernetes monitoring
AI platform. Provides health checks, Gemini connectivity tests,
and the CPU analysis agent endpoint.
"""

import logging
import sys
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator

from fastapi import FastAPI, HTTPException

from config.settings import get_settings
from schemas.cpu_schema import CPURequest, CPUResponse
from schemas.correlation.correlation_output import CorrelationOutput
from services.llm_service import get_llm
from services.bootstrap_agents import initialize_registry
from agents.cpu_agent import run_cpu_agent
from services.global_bus import event_bus

# Routers
from routers.knowledge_router import router as knowledge_router
from routers.approval_router import router as approval_router

# ---------------------------------------------------------------------------
# Logging Configuration
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[logging.StreamHandler(sys.stdout)],
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Application Lifespan
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Manage application startup and shutdown events.

    On startup:
        - Loads and validates settings.
        - Logs configuration summary.
    On shutdown:
        - Logs graceful shutdown message.
    """
    # --- Startup ---
    logger.info("=" * 60)
    logger.info("  K8S Agentic AI Service — Starting Up")
    logger.info("=" * 60)

    settings = get_settings()
    logger.info("Model        : %s", settings.MODEL_NAME)
    logger.info("Host         : %s", settings.HOST)
    logger.info("Port         : %d", settings.PORT)
    logger.info("API Key Set  : %s", "Yes" if settings.GOOGLE_API_KEY else "NO — set GOOGLE_API_KEY in .env")
    logger.info("=" * 60)

    # Initialize Agents
    initialize_registry()

    # Start Phase 18 Event Bus
    await event_bus.start()

    yield

    # --- Shutdown ---
    logger.info("K8S Agentic AI Service — Shutting down gracefully.")
    await event_bus.stop()


# ---------------------------------------------------------------------------
# FastAPI Application
# ---------------------------------------------------------------------------
app = FastAPI(
    title="K8S Agentic AI Service",
    description=(
        "An Agentic AI platform for Kubernetes monitoring and analysis. "
        "Uses Google Gemini, LangGraph, and LangChain to provide intelligent "
        "CPU analysis and actionable recommendations for Kubernetes pods."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

# Include Routers
app.include_router(knowledge_router)
app.include_router(approval_router)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------
@app.get(
    "/",
    summary="Root",
    description="Returns a simple status message confirming the service is running.",
    tags=["General"],
)
async def root() -> dict[str, str]:
    """Return a service status message."""
    return {"message": "K8S Agentic AI Service Running"}


@app.get(
    "/health",
    summary="Health Check",
    description="Returns the health status of the service.",
    tags=["General"],
)
async def health_check() -> dict[str, str]:
    """Return the health status of the service."""
    return {"status": "healthy"}


@app.get(
    "/test-gemini",
    summary="Test Gemini Connection",
    description="Sends a test prompt to the Gemini LLM and returns the response.",
    tags=["Diagnostics"],
)
async def test_gemini() -> dict[str, str]:
    """
    Test the Gemini LLM connection.

    Sends 'Hello' to the configured Gemini model and returns its response.
    Useful for verifying that the API key is valid and the model is reachable.
    """
    logger.info("Testing Gemini LLM connection...")

    try:
        llm = get_llm()
        response = llm.invoke("Hello")
        gemini_reply: str = response.content

        logger.info("Gemini test successful.")
        return {"response": gemini_reply}

    except RuntimeError as exc:
        logger.error("Gemini test failed: %s", exc)
        raise HTTPException(
            status_code=503,
            detail=f"Gemini LLM is not available: {exc}",
        ) from exc
    except Exception as exc:
        logger.error("Unexpected error during Gemini test: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"An unexpected error occurred: {exc}",
        ) from exc


@app.post(
    "/cpu",
    response_model=CPUResponse,
    summary="CPU Analysis",
    description="Runs the CPU analysis agent for a specified Kubernetes pod.",
    tags=["Agents"],
)
async def cpu_analysis(request: CPURequest) -> CPUResponse:
    """
    Execute the CPU analysis agent.

    Accepts a namespace and pod name, runs the full CPU analysis
    pipeline (collect → analyze → recommend), and returns the result.

    Args:
        request: The CPU analysis request containing namespace and pod_name.

    Returns:
        CPUResponse with status and analysis message.
    """
    logger.info(
        "Received CPU analysis request: namespace='%s', pod_name='%s'.",
        request.namespace,
        request.pod_name,
    )

    try:
        result: dict[str, Any] = run_cpu_agent(
            namespace=request.namespace,
            pod_name=request.pod_name,
        )

        logger.info("CPU analysis completed with status: '%s'.", result["status"])

        return CPUResponse(
            status=result["status"],
            message=result["message"],
        )

    except Exception as exc:
        logger.error(
            "CPU analysis endpoint failed: %s", exc, exc_info=True,
        )
        raise HTTPException(
            status_code=500,
            detail=f"CPU analysis failed: {exc}",
        ) from exc


@app.post(
    "/correlate",
    response_model=CorrelationOutput,
    summary="Event Correlation Analysis",
    description=(
        "Runs the full multi-signal Event Correlation Engine for a specified "
        "Kubernetes pod. Combines CPU, Memory, Disk, Network, Log, and "
        "Kubernetes Event signals to identify the most probable incident type "
        "and root cause."
    ),
    tags=["Agents"],
)
async def correlate_analysis(request: CPURequest) -> CorrelationOutput:
    """
    Execute the Event Correlation Engine.

    Accepts a namespace and pod name, runs the full pipeline
    (metric_collector → correlation → analyzer → …), and returns
    the CorrelationOutput from the shared state.

    Args:
        request: The CPU analysis request containing namespace and pod_name.

    Returns:
        CorrelationOutput with incident_type, root_cause, confidence_score,
        correlated_events, and correlation_summary.
    """
    logger.info(
        "Received correlation request: namespace='%s', pod_name='%s'.",
        request.namespace,
        request.pod_name,
    )

    try:
        from graph.cpu_graph import build_cpu_graph
        from schemas.cpu_state import CPUState, InputState

        cpu_graph = build_cpu_graph()
        initial_state = CPUState(
            inputs=InputState(
                pod_name=request.pod_name,
                namespace=request.namespace,
            )
        )

        result_state: CPUState = cpu_graph.invoke(initial_state)

        logger.info(
            "Correlation completed: incident=%s confidence=%.2f source=%s",
            result_state.correlation_output.incident_type.value,
            result_state.correlation_output.confidence_score,
            result_state.correlation_output.source.value,
        )

        return result_state.correlation_output

    except Exception as exc:
        logger.error(
            "Correlation endpoint failed: %s", exc, exc_info=True,
        )
        raise HTTPException(
            status_code=500,
            detail=f"Correlation analysis failed: {exc}",
        ) from exc


# ---------------------------------------------------------------------------
# Direct Execution
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn

    _settings = get_settings()
    uvicorn.run(
        "main:app",
        host=_settings.HOST,
        port=_settings.PORT,
        reload=True,
    )
