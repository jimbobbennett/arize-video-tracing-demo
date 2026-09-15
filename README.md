# Gemini video transcription traced in Arize AX

This temporary demo transcribes the bundled 20-second video with Gemini and sends manually created OpenInference spans to Arize AX. The captured LLM input uses the stable, public GitHub video URL rather than Gemini's temporary Files API URI.

## Run it

1. Create and activate a Python virtual environment.
2. Install the dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Copy `.env.example` to `.env`, populate the variables, and export them into your shell.
4. Run the demo:

   ```bash
   python transcribe_video.py
   ```

The script uploads `assets/video-demo.mp4` to Gemini, waits for processing, invokes `gemini-3.8-flash`, and deletes the temporary Gemini upload. It creates a root `CHAIN` span and child `LLM` span explicitly; no auto-instrumentor is used. Gemini still receives its temporary Files API URI, but the captured LLM input uses the public video JSON object.

## Trace fields demonstrated

- The `message_content.type = "video"` and nested `message_content.video` object, with `video.mime_type = "video/mp4"` and the public `video.url`, on the manually set OpenInference input-message part.
- The exported LLM input part: `{ "message_content.video": { "video.mime_type": "video/mp4", "video.url": "https://…/video-demo.mp4" } }`.
- Text prompt and transcript as adjacent OpenInference message-content parts

The video is an authorized, public, derived 20-second/720p clip from the repository owner's source file. This repository is temporary and will be deleted after validation.
