"""ADK agent and callback that supplements its auto-instrumented LLM span."""

import json

from opentelemetry import trace

from google.adk.agents import Agent


REPOSITORY = "jimbobbennett/arize-video-tracing-demo"
PUBLIC_VIDEO_URL = (
    f"https://raw.githubusercontent.com/{REPOSITORY}/main/assets/video-demo.mp4"
)


async def add_public_video_url(*, callback_context, llm_request):
    """Attach the stable public URL to ADK's active auto-instrumented LLM span.

    ADK invokes `before_model_callback` inside its `call_llm` span. The
    OpenInference ADK instrumentor owns that span; this callback only supplies
    the video field that the current instrumentor does not yet derive from an
    ADK `file_data` part.
    """
    # The instrumentor puts a system instruction at message index 0 when ADK
    # supplies one, then enumerates request contents after it.
    message_offset = int(bool(llm_request.config and llm_request.config.system_instruction))
    for message_index, content in enumerate(llm_request.contents or [], message_offset):
        for content_index, part in enumerate(content.parts or []):
            file_data = part.file_data
            if file_data and (file_data.mime_type or "").startswith("video/"):
                span = trace.get_current_span()
                attribute_prefix = (
                    f"llm.input_messages.{message_index}.message.contents."
                    f"{content_index}.message_content"
                )
                span.set_attribute(f"{attribute_prefix}.type", "video")
                span.set_attribute(
                    f"{attribute_prefix}.video",
                    json.dumps(
                        {
                            "video.mime_type": "video/mp4",
                            "video.url": PUBLIC_VIDEO_URL,
                        }
                    ),
                )
                return None
    return None


root_agent = Agent(
    name="video_transcriber",
    model="gemini-3.8-flash",
    description="Creates a timestamped transcript from a video.",
    instruction="Create a timestamped transcript. Include only spoken words.",
    before_model_callback=add_public_video_url,
)
