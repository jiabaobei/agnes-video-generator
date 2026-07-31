# agnes-video-generator

**Free, open-source text-to-video & image-to-video tool.**  
One command turns a text prompt or image into a 5s / 10s short video.  
Powered by [Agnes AI](https://agnes-ai.com) video model. No GPU required.

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![Status](https://img.shields.io/badge/status-active-success.svg)]()

---

## Why this exists

Most AI video generators are either paid (Runway, Pika) or require a powerful local GPU (Stable Video Diffusion).  
**agnes-video-generator** fills the gap: free, open-source, and runs on any machine with Python — because inference happens in the cloud via the Agnes AI API.

## Quick start

```bash
git clone https://github.com/jiabaobei/agnes-video-generator.git
cd agnes-video-generator

# Generate a 10-second video (default)
python generate_video.py "A cute cat playing with a ball of yarn on a sunny afternoon"

# Generate a 5-second short
python generate_video.py "Red sports car driving on a mountain road at sunset" --duration 5

# Interactive mode (no prompt argument)
python generate_video.py
```

**No API key setup needed.** The script ships with a built-in free Agnes AI key and works out of the box.

## Features

- **Free & open-source** (MIT) — no paywalls, no rate-limited free tier
- **Cloud inference** — no local GPU required; works on laptops, servers, even Raspberry Pi
- **Text-to-video & image-to-video** — pass a prompt or an image
- **5s / 10s durations** — choose via `--duration`
- **One-command workflow** — submit → poll → download, fully automated
- **Cross-platform** — pure Python standard library, no heavy dependencies

## Output specs

| Property | Value |
|----------|-------|
| Format | MP4 |
| Duration | 5s (121 frames) or 10s (241 frames) |
| Resolution | 1088×832 (fixed by API) |
| Framerate | 24 fps |
| Typical latency | ~2–5 minutes |

## Prompt tips

- English prompts work better (training data is English-heavy)
- Include scene details: lighting, background, action, mood
- Specific actions beat abstract descriptions: prefer `waving paw` over `dancing`
- Examples:
  - `A chef cooking in a Chinese restaurant kitchen, steam rising`
  - `A drone flying over snow mountains at golden hour`
  - `A robot watering plants on a balcony, sunlight through leaves`

## Tech notes

- Video URL is extracted from the API response field `remixed_from_video_id` (compatibility shim included)
- Submit timeout: 300s; retries: 3; poll interval: 10s, max 60 attempts
- Windows encoding compatibility handled

## Use cases

- Social media short-video素材批量生成
- Explainer / promo clips without hiring editors
- Prototyping video ideas quickly
- Learning AI video generation pipelines

## Comparison with alternatives

| Tool | Cost | GPU needed | Open source |
|------|------|------------|-------------|
| Runway Gen-2 | $0.05/s+ | No | No |
| Pika | Limited free tier | No | No |
| 可灵 / 即梦 | Limited free tier | No | No |
| Stable Video Diffusion | Free | 8G+ VRAM | Yes |
| **agnes-video-generator** | **Free** | **No** | **Yes (MIT)** |

## Roadmap

- [ ] Batch prompt queue
- [ ] More output resolutions
- [ ] Community prompt templates
- [ ] Web UI wrapper

## License

MIT — feel free to use, modify, and ship.

## Star history

If this tool saves you time, a star is the best support.  
GitHub: https://github.com/jiabaobei/agnes-video-generator
