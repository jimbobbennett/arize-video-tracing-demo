"""Manually trace a Gemini video transcription in Arize AX."""

import json
import os
import time

from arize.otel import register
from google import genai
from opentelemetry.trace import Status, StatusCode


MODEL = "gemini-3.8-flash"
VIDEO_PATH = "assets/video-demo.mp4"
VIDEO_URL = (
    "https://raw.githubusercontent.com/"
    "jimbobbennett/arize-video-tracing-demo/main/assets/video-demo.mp4"
)
PROMPT = "Create a timestamped transcript of this video. Include only spoken words."
SESSION_ID = "manual-video-transcription-demo"


def wait_until_active(client: genai.Client, uploaded_file):
    """Wait for Gemini's asynchronous video processing to finish."""
    while uploaded_file.state.name == "PROCESSING":
        time.sleep(2)
        uploaded_file = client.files.get(name=uploaded_file.name)
    if uploaded_file.state.name != "ACTIVE":
        raise RuntimeError(f"Gemini file processing failed: {uploaded_file.state.name}")
    return uploaded_file


def main() -> None:
    tracer_provider = register(
        space_id=os.environ["ARIZE_SPACE_ID"],
        api_key=os.environ["ARIZE_API_KEY"],
        project_name=os.environ.get("ARIZE_PROJECT_NAME", "gemini-video-transcription-demo"),
    )
    tracer = tracer_provider.get_tracer(__name__)
    client = genai.Client()
    uploaded_file = None
    captured_input = {
        "model": MODEL,
        "contents": [
            {
                "role": "user",
                "parts": [
                    {"text": PROMPT},
                    {
                        "message_content.video": {
                            "video.mime_type": "video/mp4",
                            "video.url": VIDEO_URL,
                        }
                    },
                ],
            }
        ],
    }

    try:
        with tracer.start_as_current_span("video_transcription") as pipeline_span:
            pipeline_span.set_attribute("openinference.span.kind", "CHAIN")
            pipeline_span.set_attribute("input.mime_type", "application/json")
            pipeline_span.set_attribute("input.value", json.dumps(captured_input))
            pipeline_span.set_attribute("session.id", SESSION_ID)

            uploaded_file = wait_until_active(client, client.files.upload(file=VIDEO_PATH))

            with tracer.start_as_current_span("gemini.generate_content") as llm_span:
                llm_span.set_attribute("openinference.span.kind", "LLM")
                llm_span.set_attribute("llm.provider", "google")
                llm_span.set_attribute("llm.system", "google")
                llm_span.set_attribute("llm.model_name", MODEL)
                llm_span.set_attribute("session.id", SESSION_ID)
                llm_span.set_attribute("input.mime_type", "application/json")
                llm_span.set_attribute("input.value", json.dumps(captured_input))
                llm_span.set_attribute(
                    "llm.input_messages.0.message.role", "user"
                )
                llm_span.set_attribute(
                    "llm.input_messages.0.message.contents.0.message_content.type",
                    "text",
                )
                llm_span.set_attribute(
                    "llm.input_messages.0.message.contents.0.message_content.text",
                    PROMPT,
                )
                llm_span.set_attribute(
                    "llm.input_messages.0.message.contents.1.message_content.type",
                    "video",
                )
                llm_span.set_attribute(
                    "llm.input_messages.0.message.contents.1.message_content.video",
                    json.dumps(
                        {
                            "video.mime_type": "video/mp4",
                            "video.url": VIDEO_URL,
                        }
                    ),
                )

                response = client.models.generate_content(
                    model=MODEL,
                    contents=[PROMPT, uploaded_file],
                )
                transcript = response.text
                llm_span.set_attribute("output.mime_type", "text/plain")
                llm_span.set_attribute("output.value", transcript)
                llm_span.set_attribute(
                    "llm.output_messages.0.message.role", "assistant"
                )
                llm_span.set_attribute(
                    "llm.output_messages.0.message.contents.0.message_content.type",
                    "text",
                )
                llm_span.set_attribute(
                    "llm.output_messages.0.message.contents.0.message_content.text",
                    transcript,
                )
                llm_span.set_status(Status(StatusCode.OK))

            pipeline_span.set_attribute("output.mime_type", "text/plain")
            pipeline_span.set_attribute("output.value", transcript)
            pipeline_span.set_status(Status(StatusCode.OK))
            print(transcript)
    finally:
        if uploaded_file is not None:
            client.files.delete(name=uploaded_file.name)
        tracer_provider.force_flush()
        tracer_provider.shutdown()


if __name__ == "__main__":
    main()
