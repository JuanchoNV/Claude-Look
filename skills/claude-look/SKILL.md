---
name: claude-look
description: "Watch and understand a video from a link (TikTok, Instagram Reels, X, Facebook, YouTube and 1000+ sites). Use it when the user shares a video link and asks what it is about, to summarize it, pull out specific details, or judge it. Temporary low-quality download, key frames + local transcript, everything deleted at the end."
---

# Claude-Look

Understand a video from a link while spending few tokens: instead of looking at every frame,
look at a few small contact sheets (key frames with their timestamp) and read the transcript.

## Steps

1. Run the script that lives in this skill's folder (the first run takes 1-2 min while
   dependencies download; later runs take ~10-20 s for a short video):
   ```
   uv run "<this skill's folder>/look.py" "<URL>"
   ```
   Options: `--max-frames 12` (raise to 18-24 only if the user needs fine visual detail),
   `--model small` (if the transcript looks wrong), `--lang en|es|pt...`, `--no-audio`.
2. Read the output: title, author, duration, description and a transcript with `[mm:ss]` marks.
3. Open the images listed under `sheets` with the Read tool. Each frame shows its timestamp in
   yellow. If the transcript already answers the question, look only at the first sheet.
4. Answer what the user asked, citing timestamps when useful.
5. Always finish by deleting the temp files:
   ```
   uv run "<this skill's folder>/look.py" clean
   ```

## Limits and safety

- Public content only: never pass cookies, log in, or use the user's browser session.
- Works without login on TikTok and public Instagram Reels. YouTube often blocks anonymous
  downloads ("confirm you're not a bot"); if a link fails because it needs a login, tell the
  user and offer to analyze a video file they send instead.
- It does not list whole profiles: get the link of each video first.
- Max 300 MB per video. For long videos (20+ min) warn that transcription takes a while.
- Only the uv package cache and the Whisper model (~150 MB, Hugging Face cache) stay on disk,
  so they are not downloaded again next time.
