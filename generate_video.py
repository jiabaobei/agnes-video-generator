#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Agnes Video 2.0 文生视频工具 (v1.2.0)
用法:
  python generate_video.py "你的视频描述"              # 默认10秒
  python generate_video.py "你的视频描述" --duration 5  # 5秒
  python generate_video.py "你的视频描述" --duration 10 # 10秒
  python generate_video.py --fallback-info             # 查看备用方案
"""

import os
import sys
import json
import time
import urllib.request
import urllib.error
import argparse

# ==================== 配置区 ====================
# 如果你的 Skill 分享给了别人，建议让他们把 Key 填在 config.ini 里（更安全）
# 但对自己用，硬编码最方便
API_KEY = "sk-wtQ84SRJzizAfKWm9m6hbzqYvg5S7rR2ZDlLKcHouC29ncpA"
BASE_URL = "https://apihub.agnes-ai.com/v1"
MODEL_NAME = "agnes-video-v2.0"

# 视频参数
# 注意：Agnes API 会忽略 width/height 参数，实际输出固定为 1088x832
FRAME_RATE = 24


def log(msg):
    """安全的打印函数，避免 Windows 编码问题"""
    try:
        print(msg)
        sys.stdout.flush()
    except Exception:
        try:
            sys.stdout.buffer.write((str(msg) + "\n").encode("utf-8", errors="replace"))
            sys.stdout.buffer.flush()
        except Exception:
            pass


def submit_video_task(prompt, num_frames):
    """提交视频生成任务，返回 task_id"""
    url = f"{BASE_URL}/videos"

    # width/height 参数会被 API 忽略，实际输出固定 1088x832
    # num_frames 参数有效，控制视频时长
    payload = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "num_frames": num_frames,
        "frame_rate": FRAME_RATE
    }

    data = json.dumps(payload).encode('utf-8')

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    max_attempts = 3
    for attempt in range(1, max_attempts + 1):
        req = urllib.request.Request(url, data=data, headers=headers, method='POST')
        try:
            log(f"   [尝试 {attempt}/{max_attempts}] 提交请求中...")
            with urllib.request.urlopen(req, timeout=300) as response:
                result = json.loads(response.read().decode('utf-8'))
                task_id = result.get("task_id")
                if task_id:
                    log(f"\n[OK] 任务已提交! Task ID: {task_id}")
                    return task_id
                else:
                    log(f"\n[FAIL] 提交失败，响应: {result}")
                    err = result.get("error") or result.get("message")
                    if err:
                        log(f"   错误: {err}")
                    return None
        except urllib.error.HTTPError as e:
            body = e.read().decode('utf-8', errors='ignore')
            log(f"\n[HTTP ERROR] {e.code}: {body[:500]}")
            if e.code in (401, 403, 400):
                if e.code == 401:
                    log("   提示: 请检查 API Key 是否正确")
                return None
            # 5xx 错误可以重试
        except Exception as e:
            log(f"\n[ERROR] 提交任务时出错: {type(e).__name__}: {e}")

        if attempt < max_attempts:
            log("   等待 3 秒后重试...")
            time.sleep(3)

    log(f"\n[FAIL] 重试 {max_attempts} 次后仍失败")
    return None


def poll_video_status(task_id, interval=10):
    """轮询视频任务状态，直到完成或失败"""
    url = f"{BASE_URL}/videos/{task_id}"

    headers = {
        "Authorization": f"Bearer {API_KEY}"
    }

    log("\n[等待] 正在生成视频，请耐心等候（通常 2-5 分钟）...")
    log("   （每 10 秒检查一次进度）\n")

    max_polls = 60  # 最多轮询 10 分钟
    poll_count = 0

    while poll_count < max_polls:
        time.sleep(interval)
        poll_count += 1

        req = urllib.request.Request(url, headers=headers)

        try:
            with urllib.request.urlopen(req, timeout=30) as response:
                result = json.loads(response.read().decode('utf-8'))

                status = result.get("status", "unknown")
                log(f"   [{poll_count}/{max_polls}] 状态: {status}")

                if status == "completed":
                    log(f"\n[完成] 视频生成完成!")
                    # Agnes API 返回的视频 URL 在 "remixed_from_video_id" 字段
                    # (不是 "video_url"，这是之前踩过的坑)
                    video_url = (
                        result.get("remixed_from_video_id")
                        or result.get("video_url")
                        or result.get("url")
                    )
                    # 也检查嵌套结构
                    if not video_url and isinstance(result.get("output"), dict):
                        video_url = result["output"].get("video_url")
                    if not video_url and isinstance(result.get("data"), dict):
                        video_url = result["data"].get("video_url") or result["data"].get("url")

                    if video_url:
                        log(f"[视频地址] {video_url}")
                        download_video(video_url, task_id)
                        return video_url
                    else:
                        log("[警告] 未找到视频地址，原始响应:")
                        log(json.dumps(result, indent=2, ensure_ascii=False))
                        return None

                elif status == "failed":
                    log(f"\n[失败] 视频生成失败:")
                    log(f"   原因: {result.get('error', '未知')}")
                    return None

                elif status in ("processing", "pending", "running", "queued"):
                    continue  # 继续等待

        except urllib.error.HTTPError as e:
            body = e.read().decode('utf-8', errors='ignore')
            log(f"   [HTTP ERROR] {e.code}: {body[:200]}")
            if e.code < 500:
                log("   客户端错误，停止轮询")
                return None
            continue
        except Exception as e:
            log(f"   [POLL ERROR] {e}")
            continue

    log(f"\n[超时] 轮询超时（{max_polls * interval}秒）")
    return None


def download_video(video_url, task_id):
    """下载视频到本地"""
    output_dir = "outputs"
    os.makedirs(output_dir, exist_ok=True)

    timestamp = time.strftime("%Y%m%d_%H%M%S")
    filename = f"agnes_video_{timestamp}.mp4"
    filepath = os.path.join(output_dir, filename)

    log(f"[下载] 正在保存到: {filepath}")

    try:
        urllib.request.urlretrieve(video_url, filepath)
        filesize_mb = os.path.getsize(filepath) / 1024 / 1024
        log(f"[OK] 下载完成! 文件大小: {filesize_mb:.2f} MB")
        log(f"[文件] {os.path.abspath(filepath)}")
        return filepath
    except Exception as e:
        log(f"[下载错误] {e}")
        log(f"\n[手动下载] 可以从以下地址下载: {video_url}")
        return None


def print_fallback_info():
    """打印备用方案 OpenMontage 的使用指引"""
    log("=" * 60)
    log("  [备用方案] OpenMontage — 智能体驱动型视频制作系统")
    log("=" * 60)
    log("""
当 Agnes API 不可用时（算力卡顿、服务宕机、网络故障），
可以切换到 OpenMontage 作为备用视频生成方案。

OpenMontage 是什么:
  - 开源智能体驱动型视频制作系统
  - 支持文字/图片 → 完整视频（含旁白、字幕、剪辑、合成）
  - 支持 15+ 视频生成提供商（Kling、Runway、Google Veo、WAN 2.1 等）
  - 零 API Key 可用（Piper TTS + Archive.org 免费素材 + Remotion 合成）

快速开始:
  1. 克隆仓库
     git clone https://github.com/calesthio/OpenMontage.git
     cd OpenMontage

  2. 安装依赖
     make setup
     # 或 Windows:
     py -3 -m venv .venv; .\\.venv\\Scripts\\Activate.ps1; python -m pip install -r requirements.txt; cd remotion-composer; npm install; cd ..; python -m pip install piper-tts

  3. 配置 API Key（可选，零 Key 也能用）
     cp .env.example .env
     # 编辑 .env，填入至少一个视频生成 API Key

  4. 在 AI 编码助手中输入需求，例如:
     "Make a 45-second animated explainer about why the sky is blue"
     "Create a 30-second Ghibli-style animated video of a magical library"

  5. 查看实时进度:
     python -m backlot open

成本参考:
  - 零 Key 路径: 完全免费（Piper TTS + Archive.org 素材 + Remotion 合成）
  - 配置 1-2 个 API Key: $0.15-$1.50/条视频
  - 全配置路径: $1-$3/条视频

项目地址: https://github.com/calesthio/OpenMontage
""")
    log("=" * 60)


def main():
    parser = argparse.ArgumentParser(description="Agnes Video 2.0 文生视频工具")
    parser.add_argument("prompt", nargs="*", help="视频描述")
    parser.add_argument("--duration", type=int, default=10, choices=[5, 10],
                        help="视频时长（秒），5或10，默认10")
    parser.add_argument("--fallback-info", action="store_true",
                        help="显示备用方案 OpenMontage 的使用指引")
    args = parser.parse_args()

    # 显示备用方案信息
    if args.fallback_info:
        print_fallback_info()
        return

    log("=" * 60)
    log("  Agnes Video 2.0 Text-to-Video Tool (v1.1.1)")
    log("=" * 60)

    # 获取 prompt
    if args.prompt:
        prompt = " ".join(args.prompt)
    else:
        try:
            prompt = input("\n请输入视频描述 (英文效果更好):\n  > ").strip()
        except Exception:
            prompt = ""
        if not prompt:
            log("[错误] 描述不能为空!")
            sys.exit(1)

    # 根据时长计算帧数
    duration = args.duration
    num_frames = duration * FRAME_RATE + 1  # 5秒=121帧, 10秒=241帧

    log(f"\n[描述] {prompt}")
    log(f"[模型] {MODEL_NAME}")
    log(f"[时长] {duration}秒 ({num_frames}帧 @ {FRAME_RATE}fps)")
    log(f"[分辨率] 1088x832（API 固定输出）")
    log("-" * 60)

    # Step 1: 提交任务
    task_id = submit_video_task(prompt, num_frames)
    if not task_id:
        log("\n[失败] 任务提交失败")
        log("   可能原因: API Key 无效 / 网络故障 / Agnes 服务暂时不可用")
        log("   建议: 1) 检查网络连接  2) 稍后重试  3) 使用备用方案 OpenMontage")
        log("   查看备用方案: python generate_video.py --fallback-info")
        sys.exit(1)

    # Step 2: 轮询状态
    video_url = poll_video_status(task_id)

    log("\n" + "=" * 60)
    if video_url:
        log("  [完成] 全部完成! 视频已保存到 outputs/ 目录")
    else:
        log("  [结束] 任务结束（未获得视频）")
        log("   建议: 1) 检查网络连接  2) 稍后重试  3) 使用备用方案 OpenMontage")
        log("   查看备用方案: python generate_video.py --fallback-info")
    log("=" * 60)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        log("\n[已中断] 用户手动取消")
        sys.exit(130)
    except Exception as e:
        log(f"\n[严重错误] 未捕获异常: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
