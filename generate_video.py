#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Agnes Video 2.0 文生视频工具 (v1.4.0)
用法:
  python generate_video.py "你的视频描述"              # 默认10秒
  python generate_video.py "你的视频描述" --duration 5  # 5秒
  python generate_video.py "你的视频描述" --duration 10 # 10秒
  python generate_video.py --fallback-info             # 查看备用方案
  python generate_video.py --resume <task_id>          # 恢复轮询
"""

from __future__ import annotations

import argparse
import json
import os
import random
import socket
import sys
import time
import urllib.error
import urllib.request
from typing import Any, Optional

# ==================== 常量配置区 ====================
API_KEY: str = "sk-wtQ84SRJzizAfKWm9m6hbzqYvg5S7rR2ZDlLKcHouC29ncpA"
BASE_URL: str = "https://apihub.agnes-ai.cn/v1"
MODEL_NAME: str = "agnes-video-v2.0"
FRAME_RATE: int = 24

# 网络与重试
SUBMIT_TIMEOUT: int = 300       # 提交超时（秒）
POLL_TIMEOUT: int = 30          # 单次轮询超时（秒）
MAX_RETRIES: int = 3            # 提交重试次数
MAX_POLLS: int = 60             # 最大轮询次数
POLL_INTERVAL: int = 10         # 轮询间隔（秒）
RETRY_DELAY: int = 3            # 重试间隔（秒）

# 输入限制
MAX_PROMPT_LENGTH: int = 1000   # prompt 最大字符数

# 输出
OUTPUT_DIR: str = "outputs"
TASK_STATE_FILE: str = ".agnes_tasks.json"

# User-Agent
USER_AGENT: str = "AgnesVideoTool/1.4.0"

# Agnes API 域名白名单（用于校验视频下载 URL）
ALLOWED_VIDEO_DOMAINS: set[str] = {
    "agnes-ai.com",
    "apihub.agnes-ai.com",
    "apihub.agnes-ai.cn",
    "cdn.agnes-ai.com",
    "media.agnes-ai.com",
    "platform-outputs.agnes-ai.space",
    "agnes-ai.space",
}

# OpenMontage 备用服务默认端口
OPENMONTAGE_DEFAULT_PORT: int = 3000


# ==================== 日志 ====================
def log(msg: str) -> None:
    """安全的打印函数，避免 Windows 编码问题"""
    try:
        print(msg)
        sys.stdout.flush()
    except Exception:
        try:
            sys.stdout.buffer.write((str(msg) + "\n").encode("utf-8", errors="replace"))
            sys.stdout.buffer.flush()
        except Exception:
            # 至少写到 stderr，不要完全静默
            try:
                sys.stderr.write(str(msg) + "\n")
                sys.stderr.flush()
            except Exception:
                pass


# ==================== 工具函数 ====================
def _validate_video_url(url: str) -> bool:
    """校验视频 URL 是否来自 Agnes 可信域名"""
    if not url:
        return False
    if not url.startswith("https://"):
        return False
    # 提取域名
    try:
        host = url.split("/")[2].split(":")[0]
        domain = ".".join(host.split(".")[-2:]) if "." in host else host
        # 允许主域名及其子域
        return any(host.endswith(d) for d in ALLOWED_VIDEO_DOMAINS) or domain == "agnes-ai.com"
    except Exception:
        return False


def _generate_filename(task_id: str) -> str:
    """生成带毫秒+随机后缀的文件名，防止同秒覆盖"""
    now = time.time()
    ms = int((now - int(now)) * 1000)
    timestamp = time.strftime("%Y%m%d_%H%M%S", time.localtime(now))
    suffix = random.randint(1000, 9999)
    return f"agnes_video_{timestamp}_{ms:03d}_{suffix}.mp4"


def _save_task_state(task_id: str, prompt: str, duration: int) -> None:
    """保存任务状态到本地，支持中断恢复"""
    try:
        state: dict[str, Any] = {}
        if os.path.exists(TASK_STATE_FILE):
            with open(TASK_STATE_FILE, "r", encoding="utf-8") as f:
                state = json.load(f)
        state[task_id] = {
            "prompt": prompt,
            "duration": duration,
            "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        }
        with open(TASK_STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
    except Exception as e:
        log(f"[警告] 无法保存任务状态: {e}")


def _load_task_state(task_id: str) -> Optional[dict[str, Any]]:
    """从本地加载任务状态"""
    try:
        if not os.path.exists(TASK_STATE_FILE):
            return None
        with open(TASK_STATE_FILE, "r", encoding="utf-8") as f:
            state = json.load(f)
        return state.get(task_id)
    except Exception:
        return None


def _check_openmontage_service(port: int = OPENMONTAGE_DEFAULT_PORT) -> bool:
    """检测本地 OpenMontage 服务是否在运行"""
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=2):
            return True
    except OSError:
        return False


def _submit_to_openmontage(prompt: str, duration: int) -> Optional[str]:
    """向本地运行的 OpenMontage 提交任务（如果服务已启动）"""
    if not _check_openmontage_service():
        return None
    try:
        url = f"http://127.0.0.1:{OPENMONTAGE_DEFAULT_PORT}/api/generate"
        payload = json.dumps({"prompt": prompt, "duration": duration}).encode("utf-8")
        req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            return result.get("video_path") or result.get("output_path")
    except Exception as e:
        log(f"[OpenMontage] 提交失败: {e}")
        return None


# ==================== 核心逻辑 ====================
def submit_video_task(prompt: str, num_frames: int) -> Optional[str]:
    """提交视频生成任务，返回 task_id"""
    url = f"{BASE_URL}/videos"

    payload = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "num_frames": num_frames,
        "frame_rate": FRAME_RATE,
    }

    data = json.dumps(payload).encode("utf-8")

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
        "User-Agent": USER_AGENT,
    }

    for attempt in range(1, MAX_RETRIES + 1):
        req = urllib.request.Request(url, data=data, headers=headers, method="POST")
        try:
            log(f"   [尝试 {attempt}/{MAX_RETRIES}] 提交请求中...")
            with urllib.request.urlopen(req, timeout=SUBMIT_TIMEOUT) as response:
                result = json.loads(response.read().decode("utf-8"))
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
            body = e.read().decode("utf-8", errors="ignore")
            log(f"\n[HTTP ERROR] {e.code}: {body[:500]}")
            if e.code in (401, 403, 400):
                if e.code == 401:
                    log("   提示: 请检查 API Key 是否正确")
                return None
            # 5xx 错误继续重试
        except urllib.error.URLError as e:
            log(f"\n[网络错误] {e.reason}")
        except json.JSONDecodeError as e:
            log(f"\n[数据解析错误] 响应不是合法 JSON: {e}")
        except OSError as e:
            log(f"\n[系统错误] {e}")

        if attempt < MAX_RETRIES:
            log(f"   等待 {RETRY_DELAY} 秒后重试...")
            time.sleep(RETRY_DELAY)

    log(f"\n[FAIL] 重试 {MAX_RETRIES} 次后仍失败")
    return None


def poll_video_status(task_id: str, interval: int = POLL_INTERVAL) -> Optional[str]:
    """轮询视频任务状态，直到完成或失败"""
    url = f"{BASE_URL}/videos/{task_id}"

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "User-Agent": USER_AGENT,
    }

    log("\n[等待] 正在生成视频，请耐心���候（通常 2-5 分钟）...")
    log(f"   （每 {interval} 秒检查一次进度）\n")

    poll_count = 0

    while poll_count < MAX_POLLS:
        poll_count += 1

        req = urllib.request.Request(url, headers=headers)

        try:
            with urllib.request.urlopen(req, timeout=POLL_TIMEOUT) as response:
                result = json.loads(response.read().decode("utf-8"))

                status = result.get("status", "unknown")
                log(f"   [{poll_count}/{MAX_POLLS}] 状态: {status}")

                if status == "completed":
                    log(f"\n[完成] 视频生成完成!")
                    video_url = (
                        result.get("remixed_from_video_id")
                        or result.get("video_url")
                        or result.get("url")
                    )
                    if not video_url and isinstance(result.get("output"), dict):
                        video_url = result["output"].get("video_url")
                    if not video_url and isinstance(result.get("data"), dict):
                        video_url = result["data"].get("video_url") or result["data"].get("url")
                    # 国内站/新版本 API 将 URL 放在 metadata.url
                    if not video_url and isinstance(result.get("metadata"), dict):
                        video_url = result["metadata"].get("url") or result["metadata"].get("video_url")

                    if video_url:
                        if not _validate_video_url(video_url):
                            log(f"[警告] 视频 URL 未通过域名白名单校验: {video_url}")
                            log("   仍尝试下载，但请确认链接来源可信")
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
                    # 先检查状态，再 sleep，避免首轮无意义等待
                    if poll_count < MAX_POLLS:
                        time.sleep(interval)
                    continue

        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", errors="ignore")
            log(f"   [HTTP ERROR] {e.code}: {body[:200]}")
            if e.code < 500:
                log("   客户端错误，停��轮询")
                return None
        except urllib.error.URLError as e:
            log(f"   [网络错误] {e.reason}")
        except json.JSONDecodeError as e:
            log(f"   [数据解析错误] {e}")
        except OSError as e:
            log(f"   [系统错误] {e}")

        # 非终止状态错误后也 sleep
        if poll_count < MAX_POLLS:
            time.sleep(interval)

    log(f"\n[超时] 轮询超时（{MAX_POLLS * interval}秒）")
    return None


def download_video(video_url: str, task_id: str) -> Optional[str]:
    """下载视频到本地"""
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    filename = _generate_filename(task_id)
    filepath = os.path.join(OUTPUT_DIR, filename)

    log(f"[下载] 正在保存到: {filepath}")

    try:
        urllib.request.urlretrieve(video_url, filepath)
        filesize_mb = os.path.getsize(filepath) / 1024 / 1024
        log(f"[OK] 下载完成! 文件大小: {filesize_mb:.2f} MB")
        log(f"[文件] {os.path.abspath(filepath)}")
        return filepath
    except urllib.error.URLError as e:
        log(f"[下载错误] 网络错误: {e}")
    except OSError as e:
        log(f"[下载错误] 系统错误: {e}")
    except Exception as e:
        log(f"[下载错误] {type(e).__name__}: {e}")

    log(f"\n[手动下载] 可以从以下地址下载: {video_url}")
    return None


def try_openmontage_fallback(prompt: str, duration: int) -> Optional[str]:
    """
    尝试使用 OpenMontage 备用方案。
    
    诚实策略：只尝试调用**已手动启动**的本地 OpenMontage 服务，
    不自动克隆/安装/import 那些必定失败的操作。
    """
    log("[OpenMontage] 检查本地备用服务是否可用...")
    if not _check_openmontage_service():
        log("   [OpenMontage] 本地服务未运行（默认端口 3000）")
        log("   备用方案需要手动启动，请运行: python -m backlot open")
        log("   或查看详细指引: python generate_video.py --fallback-info")
        return None

    log("[OpenMontage] 本地服务已就绪，尝试提交任务...")
    result_path = _submit_to_openmontage(prompt, duration)
    if result_path:
        log(f"[OpenMontage] 备用方案生成成功: {result_path}")
        return result_path

    log("[OpenMontage] 服务运行中但提交失败，请检查 OpenMontage 日志")
    return None


def print_fallback_info() -> None:
    """打印备用方案 OpenMontage 的使用指引"""
    log("=" * 60)
    log("  [备用方案] OpenMontage — 智能体驱动型视频制作系统")
    log("=" * 60)
    log("""
当 Agnes API 不可用时（算力卡顿、服务宕机、网络故障），
可以切换到 OpenMontage 作为备用视频生成方案。

⚠️ 重要说明（v1.4.0 起）:
  OpenMontage 是一个复杂的 AI 编码助手驱动系统，需要
  Python 虚拟环境 + Node.js/npm + Piper TTS + Remotion 等
  依赖。本工具**不再自动尝试** import/make demo 等注定失败的
  操作。如果你已在本地运行 OpenMontage，本工具会检测到并
  尝试自动提交；否则请按以下步骤手动启动:

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

  4. 启动服务
     python -m backlot open
     # 服务运行在 http://localhost:3000

  5. 回到本工具，主方案失败时会自动检测到本地服务并尝试使用

成本参考:
  - 零 Key 路径: 完全免费（Piper TTS + Archive.org 素材 + Remotion 合成）
  - 配置 1-2 个 API Key: $0.15-$1.50/条视频
  - 全配置路径: $1-$3/条视频

项目地址: https://github.com/calesthio/OpenMontage
""")
    log("=" * 60)


def main() -> int:
    parser = argparse.ArgumentParser(description="Agnes Video 2.0 文生视频工具")
    parser.add_argument("prompt", nargs="*", help="视频描述")
    parser.add_argument("--duration", type=int, default=10, choices=[5, 10],
                        help="视频时长（秒），5或10，默认10")
    parser.add_argument("--fallback-info", action="store_true",
                        help="显示备用方案 OpenMontage 的使用指引")
    parser.add_argument("--resume", metavar="TASK_ID",
                        help="恢复指定 task_id 的轮询")
    args = parser.parse_args()

    if args.fallback_info:
        print_fallback_info()
        return 0

    log("=" * 60)
    log("  Agnes Video 2.0 Text-to-Video Tool (v1.4.0)")
    log("=" * 60)

    # 获取 prompt
    if args.prompt:
        prompt = " ".join(args.prompt).strip()
    else:
        try:
            prompt = input("\n请输入视频描述 (英文效果更好):\n  > ").strip()
        except (EOFError, KeyboardInterrupt):
            prompt = ""
        if not prompt:
            log("[错误] 描述不能为空!")
            return 1

    # 输入校验
    if len(prompt) > MAX_PROMPT_LENGTH:
        log(f"[错误] 描述过长（{len(prompt)} 字符），最大允许 {MAX_PROMPT_LENGTH} 字符")
        return 1
    if not prompt:
        log("[错误] 描述不能为空!")
        return 1

    # 根据时长计算帧数
    # +1 是因为 Agnes API 的 num_frames 参数包含首帧，
    # 实际渲染帧数 = duration * FRAME_RATE，但 API 要求总数 +1
    duration = args.duration
    num_frames = duration * FRAME_RATE + 1  # 5秒=121帧, 10秒=241帧

    log(f"\n[描述] {prompt}")
    log(f"[模型] {MODEL_NAME}")
    log(f"[时长] {duration}秒 ({num_frames}帧 @ {FRAME_RATE}fps)")
    log(f"[分辨率] 1088x832（API 固定输出）")
    log("-" * 60)

    # 恢复模式
    if args.resume:
        task_id = args.resume.strip()
        state = _load_task_state(task_id)
        if not state:
            log(f"[错误] 未找到任务 {task_id} 的本地记录，无法恢复")
            return 1
        log(f"[恢复] 已加载任务 {task_id}，继续轮询...")
        video_url = poll_video_status(task_id)
        if video_url:
            log(f"\n[完成] 视频已保存到 outputs/ 目录")
        else:
            log(f"\n[结束] 恢复轮询结束")
        return 0 if video_url else 1

    # Step 1: 提交任务
    task_id = submit_video_task(prompt, num_frames)
    if not task_id:
        log("\n[失败] 任务提交失败")
        log("   尝试切换到备用方案 OpenMontage...")
        fallback_path = try_openmontage_fallback(prompt, duration)
        if fallback_path:
            log(f"[完成] 备用方案生成成功! 视频已保存到: {fallback_path}")
            return 0
        else:
            log("   可能原因: API Key 无效 / 网络故障 / Agnes 服务暂时不可用")
            log("   建议: 1) 检查网络连接  2) 稍后重试  3) 手动使用备用方案 OpenMontage")
            log("   查看备用方案: python generate_video.py --fallback-info")
            return 1

    _save_task_state(task_id, prompt, duration)

    # Step 2: 轮询状态
    video_url = poll_video_status(task_id)

    log("\n" + "=" * 60)
    if video_url:
        log("  [完成] 全部完成! 视频已保存到 outputs/ 目录")
        return 0
    else:
        log("  [失败] 未获得视频，尝试切换到备用方案 OpenMontage...")
        fallback_path = try_openmontage_fallback(prompt, duration)
        if fallback_path:
            log(f"[完成] 备用方案生成成功! 视频已保存到: {fallback_path}")
            return 0
        else:
            log("  [结束] 任务结束（未获得视频）")
            log("   建议: 1) 检查网络连接  2) 稍后重试  3) 手动使用备用方案 OpenMontage")
            log("   查看备用方案: python generate_video.py --fallback-info")
            return 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        log("\n[已中断] 用户手动取消")
        sys.exit(130)
    except Exception as e:
        log(f"\n[严重错误] 未捕获异常: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
