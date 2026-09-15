"""Upload the bundled video, run the ADK agent, and print Gemini's transcript."""

import asyncio
from pathlib import Path
import time

# Must precede every Google ADK import.
from video_transcriber import instrumentation
from video_transcriber.agent import root_agent

from google.adk.runners import InMemoryRunner
from google.genai import Client, types


VIDEO_PATH = Path(__file__).parent / "assets" / "video-demo.mp4"
PROMPT = "Create a timestamped transcript of this video. Include only spoken words."


def wait_until_active(client: Client, uploaded_file):
    """Wait for Gemini's asynchronous video processing to finish."""
    while uploaded_file.state.name == "PROCESSING":
        time.sleep(2)
        uploaded_file = client.files.get(name=uploaded_file.name)
    if uploaded_file.state.name != "ACTIVE":
        raise RuntimeError(f"Gemini file processing failed: {uploaded_file.state.name}")
    return uploaded_file


async def main() -> None:
    if not VIDEO_PATH.exists():
        raise FileNotFoundError(f"Missing bundled video: {VIDEO_PATH}")

    client = Client()
    uploaded_file = None
    try:
        uploaded_file = wait_until_active(client, client.files.upload(file=VIDEO_PATH))
        runner = InMemoryRunner(agent=root_agent, app_name="video_transcription_demo")
        await runner.session_service.create_session(
            app_name="video_transcription_demo",
            user_id="demo_user",
            session_id="video_demo_session",
        )
        async for event in runner.run_async(
            user_id="demo_user",
            session_id="video_demo_session",
            new_message=types.Content(
                role="user",
                parts=[
                    types.Part(text=PROMPT),
                    types.Part.from_uri(
                        file_uri=uploaded_file.uri, mime_type="video/mp4"
                    ),
                ],
            ),
        ):
            if event.is_final_response() and event.content and event.content.parts:
                print(event.content.parts[0].text.strip())
    finally:
        if uploaded_file is not None:
            client.files.delete(name=uploaded_file.name)
        instrumentation.tracer_provider.force_flush()
        instrumentation.tracer_provider.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
