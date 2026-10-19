# /// script
# requires-python = ">=3.10"
# dependencies = ["yt-dlp[default,curl-cffi]", "imageio-ffmpeg", "faster-whisper", "pillow", "numpy"]
# ///
"""Claude-Look: let Claude watch a video from a link (TikTok, Instagram, X, YouTube...) cheaply.

Downloads a low-quality copy to a temp folder, keeps only the frames where the scene changes,
packs them into a few small contact sheets (timestamped), transcribes the audio locally, and
deletes the video and audio right away. Only the sheets remain until you run `clean`.

Usage:
  uv run look.py <url> [--max-frames 12] [--model base] [--lang en] [--no-audio]
  uv run look.py clean     # delete every temp folder left by previous runs
"""
import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

PREFIX = "claude-look-"
TEMP = Path(tempfile.gettempdir())


def clean() -> None:
    n = 0
    for d in TEMP.glob(PREFIX + "*"):
        shutil.rmtree(d, ignore_errors=True)
        n += 1
    print(f"Deleted {n} temp folder(s).")


def mmss(s: float) -> str:
    s = int(s)
    return f"{s // 60:02d}:{s % 60:02d}"


def download(url: str, folder: Path, ffmpeg: str) -> tuple[Path, dict]:
    import yt_dlp

    opts = {
        "outtmpl": str(folder / "video.%(ext)s"),
        # lightest single file with both video and audio (max 480p)
        "format": "best[height<=480][vcodec!=none][acodec!=none]/worst[vcodec!=none][acodec!=none]/best[height<=480]/worst",
        "ffmpeg_location": ffmpeg,
        "quiet": True,
        "no_warnings": True,
        "noprogress": True,
        "noplaylist": True,
        "max_filesize": 300 * 1024 * 1024,
        # no cookies, no logins: public content only
        "cookiefile": None,
    }
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=True)
    video = next(p for p in folder.iterdir() if p.name.startswith("video."))
    return video, info


def frames(video: Path, folder: Path, ffmpeg: str, limit: int) -> list[tuple[float, Path]]:
    """Grab 1 tiny frame per second and keep only the ones that actually change."""
    from PIL import Image, ImageChops, ImageStat

    raw = folder / "raw"
    raw.mkdir()
    subprocess.run(
        [ffmpeg, "-loglevel", "error", "-i", str(video), "-vf", "fps=1,scale=360:-2", "-q:v", "5", str(raw / "%05d.jpg")],
        check=True,
    )
    every = sorted(raw.glob("*.jpg"))
    if not every:
        return []
    picked, last = [], None
    for i, f in enumerate(every):
        img = Image.open(f).convert("L").resize((64, 64))
        if last is None or ImageStat.Stat(ImageChops.difference(img, last)).mean[0] > 12:
            picked.append((float(i), f))
            last = img
    # also the last non-black frame: it usually holds the ending or the call to action
    # (skips fade-outs to black)
    for i in range(len(every) - 1, -1, -1):
        if ImageStat.Stat(Image.open(every[i]).convert("L")).mean[0] > 10:
            break
    picked = [p for p in picked if p[0] <= i] or picked[:1]
    if picked[-1][1] != every[i]:
        picked.append((float(i), every[i]))
    if len(picked) > limit:  # trim evenly, keeping first and last
        idx = [round(k * (len(picked) - 1) / (limit - 1)) for k in range(limit)]
        picked = [picked[k] for k in dict.fromkeys(idx)]
    return picked


def sheets(picked: list[tuple[float, Path]], folder: Path) -> list[Path]:
    """Pack frames into 3x2 sheets with timestamps, so viewing them costs fewer tokens."""
    from PIL import Image, ImageDraw

    out, per_sheet, width = [], 6, 360
    for h in range(0, len(picked), per_sheet):
        group = [(t, Image.open(f).convert("RGB")) for t, f in picked[h : h + per_sheet]]
        height = max(im.height * width // im.width for _, im in group)
        cols = min(3, len(group))
        rows = (len(group) + 2) // 3
        sheet = Image.new("RGB", (cols * width, rows * height), "black")
        d = ImageDraw.Draw(sheet)
        for k, (t, im) in enumerate(group):
            im = im.resize((width, im.height * width // im.width))
            x, y = (k % 3) * width, (k // 3) * height
            sheet.paste(im, (x, y))
            d.rectangle([x, y, x + 52, y + 18], fill="black")
            d.text((x + 4, y + 3), mmss(t), fill="yellow")
        p = folder / f"sheet-{h // per_sheet + 1}.jpg"
        sheet.save(p, quality=70)
        out.append(p)
    return out


def transcribe(video: Path, folder: Path, ffmpeg: str, model: str, lang: str | None) -> list[str]:
    audio = folder / "audio.wav"
    r = subprocess.run([ffmpeg, "-loglevel", "error", "-i", str(video), "-vn", "-ac", "1", "-ar", "16000", str(audio)])
    if r.returncode or not audio.exists():
        return []
    import wave

    import numpy as np
    from faster_whisper import WhisperModel

    # pass already-decoded audio (16 kHz mono WAV) so we don't depend on PyAV
    with wave.open(str(audio)) as w:
        pcm = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
    m = WhisperModel(model, device="cpu", compute_type="int8")
    segs, _ = m.transcribe(pcm, language=lang, vad_filter=True, beam_size=1)
    return [f"[{mmss(s.start)}] {s.text.strip()}" for s in segs]


def main() -> None:
    if len(sys.argv) > 1 and sys.argv[1] == "clean":
        return clean()
    ap = argparse.ArgumentParser(description="Let Claude watch a video from a link.")
    ap.add_argument("url")
    ap.add_argument("--max-frames", type=int, default=12)
    ap.add_argument("--model", default="base", help="Whisper model: tiny | base | small (more accurate, slower)")
    ap.add_argument("--lang", default=None, help="Audio language code: en, es, pt... (default: auto-detect)")
    ap.add_argument("--no-audio", action="store_true", help="Skip transcription")
    a = ap.parse_args()

    import imageio_ffmpeg

    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    folder = Path(tempfile.mkdtemp(prefix=PREFIX))
    try:
        video, info = download(a.url, folder, ffmpeg)
        picked = frames(video, folder, ffmpeg, max(2, a.max_frames))
        out = sheets(picked, folder)
        text = [] if a.no_audio else transcribe(video, folder, ffmpeg, a.model, a.lang)
    except Exception as e:
        shutil.rmtree(folder, ignore_errors=True)
        sys.exit(f"ERROR: {e}")
    # delete everything except the sheets
    for p in folder.iterdir():
        if not p.name.startswith("sheet-"):
            shutil.rmtree(p, ignore_errors=True) if p.is_dir() else p.unlink(missing_ok=True)

    desc = (info.get("description") or "").strip()
    print(json.dumps({
        "title": info.get("title"),
        "author": info.get("uploader") or info.get("channel"),
        "platform": info.get("extractor_key"),
        # some sites (e.g. Instagram) omit duration: estimate it from the last frame (1 per second)
        "duration": mmss(info.get("duration") or (picked[-1][0] + 1 if picked else 0)),
        "description": desc[:600] + ("..." if len(desc) > 600 else ""),
        "temp_folder": str(folder),
        "sheets": [str(p) for p in out],
    }, ensure_ascii=False, indent=1))
    print("\nTRANSCRIPT:" if text else "\nTRANSCRIPT: (no speech detected)")
    print("\n".join(text))


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
