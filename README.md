# Gemini video transcription traced in Arize AX

This temporary demo runs a Google ADK agent that transcribes the bundled 20-second video with Gemini and sends OpenInference auto-instrumented traces to Arize AX. The agent's `before_model_callback` adds the stable, public GitHub video URL to ADK's active LLM span, so the trace renders the input without relying on Gemini's temporary Files API URI.

## Run it

1. Create and activate a Python virtual environment.
2. Install the dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Copy `.env.example` to `.env`, populate the variables, and export them into your shell.
4. Run the demo:

   ```bash
   python run.py
   ```

The script uploads `assets/video-demo.mp4` to Gemini, waits for processing, runs the `video_transcriber` ADK agent with `gemini-3.8-flash`, and deletes the temporary Gemini upload. The OpenInference Google ADK instrumentor automatically emits the CHAIN, AGENT, and LLM spans; no application span is created manually.

Gemini still receives its temporary Files API URI. Immediately before export, the demo replaces only the LLM span's captured `input.value` video part with the public URL, so it renders as a stable JSON object in Arize AX.

## Trace fields demonstrated

- The `message_content.type = "video"` and nested `message_content.video.video` object, with `video.mime_type = "video/mp4"` and the public `video.url`, on the matching OpenInference input-message part. Its indexes are derived from ADK's request so they remain correct when it adds a system message.
- The exported LLM input part: `{ "message_content.video": { "video.mime_type": "video/mp4", "video.url": "https://…/video-demo.mp4" } }`.
- Text prompt and transcript as adjacent OpenInference message-content parts

The video is an authorized, public, derived 20-second/720p clip from the repository owner's source file. This repository is temporary and will be deleted after validation.
