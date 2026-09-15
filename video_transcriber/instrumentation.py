"""Configure Arize AX and OpenInference before Google ADK is imported."""

import os

from arize.otel import register
from openinference.instrumentation.google_adk import GoogleADKInstrumentor


tracer_provider = register(
    space_id=os.environ["ARIZE_SPACE_ID"],
    api_key=os.environ["ARIZE_API_KEY"],
    project_name=os.environ.get("ARIZE_PROJECT_NAME", "gemini-video-transcription-demo"),
)

# Automatically emits CHAIN, AGENT, and LLM spans for every ADK run.
GoogleADKInstrumentor().instrument(tracer_provider=tracer_provider)
