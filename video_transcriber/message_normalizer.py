"""Normalize the exported ADK video request without changing Gemini's request."""

import json

from opentelemetry.sdk.trace import ReadableSpan, SpanProcessor
from opentelemetry.trace import Span


class VideoMessageNormalizer(SpanProcessor):
    """Replace an exported Gemini file-data part with a public video object."""

    def on_start(self, span: Span, parent_context=None) -> None:
        pass

    def on_end(self, span: ReadableSpan) -> None:
        attributes = span._attributes
        if attributes.get("openinference.span.kind") != "LLM":
            return

        video_json = next(
            (
                value
                for key, value in attributes.items()
                if key.endswith("message_content.video") and isinstance(value, str)
            ),
            None,
        )
        if video_json is None:
            return

        try:
            video = json.loads(video_json)
            request = json.loads(attributes["input.value"])
        except (KeyError, TypeError, json.JSONDecodeError):
            return

        replaced_video = False
        for content in request.get("contents", []):
            for index, part in enumerate(content.get("parts", [])):
                file_data = part.get("file_data")
                if isinstance(file_data, dict) and str(file_data.get("mime_type", "")).startswith("video/"):
                    content["parts"][index] = {"message_content.video": video}
                    replaced_video = True

        if replaced_video:
            attributes["input.value"] = json.dumps(request)

    def shutdown(self) -> None:
        pass

    def force_flush(self, timeout_millis: int = 30000) -> bool:
        return True
