#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Agnes Video 2.0 文生视频工具 (v2.0.0)
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
SUBMIT_TIMEOUT: int = 300
POLL_TIMEOUT: int = 30
MAX_RETRIES: int = 3
MAX_POLLS: int = 60
POLL_INTERVAL: int = 10
RETRY_DELAY: int = 3

# 输入限制
MAX_PROMPT_LENGTH: int = 1000

# 输出
OUTPUT_DIR: str = "outputs"
TASK_STATE_FILE: str = ".agnes_tasks.json"

# User-Agent
USER_AGENT: str = "AgnesVideoTool/2.0.0"

# Agnes API 域名白名单
ALLOWED_VIDEO_DOMAINS: set[str] = {
    "agnes-ai.com",
    "apihub.agnes-ai.com",
    "apihub.agnes-ai.cn",
    "cdn.agnes-ai.com",
    "media.agnes-ai.com",
    "platform-outputs.agnes-ai.space",
    "agnes-ai.space",
}

# LibTV 配置
LIBTV_IM_BASE: str = os.environ.get("OPENAPI_IM_BASE", os.environ.get("IM_BASE_URL", "https://im.liblib.tv"))
LIBTV_ACCESS_KEY: str = os.environ.get("LIBTV_ACCESS_KEY", "")
LIBTV_PROJECT_CANVAS_BASE: str = "https://www.liblib.tv/canvas?projectId="


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
    try:
        host = url.split("/")[2].split(":")[0]
        return any(host.endswith(d) for d in ALLOWED_VIDEO_DOMAINS)
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


# ==================== LibTV 备用方案 ====================
def _libtv_headers() -> dict[str, str]:
    return {
        "Authorization": f"Bearer {LIBTV_ACCESS_KEY}",
        "Content-Type": "application/json",
    }


def _libtv_api_post(path: str, body: dict) -> dict:
    """LibTV POST 请求"""
    url = f"{LIBTV_IM_BASE.rstrip('/')}{path}"
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(url, data=data, method="POST", headers=_libtv_headers())
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8", errors="ignore") if e.fp else ""
        log(f"[LibTV API 错误] {e.code}: {err_body[:500]}")
        return {"error": f"HTTP {e.code}"}
    except urllib.error.URLError as e:
        log(f"[LibTV 网络错误] {e.reason}")
        return {"error": str(e.reason)}
    except Exception as e:
        log(f"[LibTV 错误] {type(e).__name__}: {e}")
        return {"error": str(e)}


def _libtv_api_get(path: str) -> dict:
    """LibTV GET 请求"""
    url = f"{LIBTV_IM_BASE.rstrip('/')}{path}"
    req = urllib.request.Request(url, method="GET", headers=_libtv_headers())
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8", errors="ignore") if e.fp else ""
        log(f"[LibTV API 错误] {e.code}: {err_body[:500]}")
        return {"error": f"HTTP {e.code}"}
    except urllib.error.URLError as e:
        log(f"[LibTV 网络错误] {e.reason}")
        return {"error": str(e.reason)}
    except Exception as e:
        log(f"[LibTV 错误] {type(e).__name__}: {e}")
        return {"error": str(e)}


def _extract_media_urls_from_messages(messages: list[dict]) -> list[str]:
    """从 LibTV 消息中提取图片/视频 URL"""
    urls = []
    for msg in messages:
        content = msg.get("content", "")
        if isinstance(content, str):
            # 简单提取 http/https 链接
            words = content.split()
            for w in words:
                if w.startswith("https://") and ("liblib" in w or "agnes" in w or w.endswith((".mp4", ".png", ".jpg", ".jpeg"))):
                    urls.append(w.strip("`\"',.)]"))
        elif isinstance(content, list):
            for part in content:
                if isinstance(part, dict):
                    url = part.get("url") or part.get("src") or part.get("video_url")
                    if url:
                        urls.append(url)
    # 去重保序
    seen = set()
    unique = []
    for u in urls:
        if u not in seen:
            seen.add(u)
            unique.append(u)
    return unique


def _download_media(url: str, prefix: str) -> Optional[str]:
    """下载 LibTV 生成的媒体文件"""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    ext = ".mp4" if url.endswith(".mp4") else ".png"
    filename = f"libtv_{prefix}_{int(time.time())}_{random.randint(1000,9999)}{ext}"
    filepath = os.path.join(OUTPUT_DIR, filename)
    try:
        urllib.request.urlretrieve(url, filepath)
        size_mb = os.path.getsize(filepath) / 1024 / 1024
        log(f"[LibTV 下载完成] {filepath} ({size_mb:.2f} MB)")
        return filepath
    except Exception as e:
        log(f"[LibTV 下载失败] {e}")
        return None


def try_libtv_fallback(prompt: str, duration: int) -> Optional[str]:
    """
    尝试使用 LibTV 生成视频。
    
    前置条件: 环境变量 LIBTV_ACCESS_KEY 已设置。
    收费提醒: LibTV 新用户有免费额度，超出后按会员/积分收费。
    """
    if not LIBTV_ACCESS_KEY:
        log("[LibTV] 未检测到 LIBTV_ACCESS_KEY 环境变量")
        log("   LibTV 是付费备选方案（新用户有免费额度）")
        log("   使用步骤:")
        log("   1. 访问 https://www.liblib.tv/ 注册账号")
        log("   2. 进入项目 → 点击右上角【LibTV Skills】获取 Access Key")
        log("   3. 设置环境变量: set LIBTV_ACCESS_KEY=你的密钥")
        log("   4. 重新运行本工具")
        log("   查看详情: https://github.com/libtv-labs/libtv-skills")
        return None

    # 收费提醒界面
    log("=" * 60)
    log("  [LibTV] ⚠️  收费提醒")
    log("=" * 60)
    log("  LibTV 新用户有免费额度，但超出后将按会员/积分收费。")
    log("  你当前使用的是【备用方案】，建议确认剩余额度后再继续。")
    log("  收费标准: 年卡最低 39 折，部分模型额外 6 折")
    log("  详情: https://www.liblib.tv/")
    log("=" * 60)

    log("[LibTV] 正在创建会话...")
    create_resp = _libtv_api_post("/openapi/session", {"message": prompt})
    if "error" in create_resp:
        log(f"[LibTV] 创建会话失败: {create_resp.get('error')}")
        return None

    data = create_resp.get("data", {})
    project_uuid = data.get("projectUuid", "")
    session_id = data.get("sessionId", "")
    if not session_id:
        log("[LibTV] 未返回 sessionId，无法继续")
        return None

    project_url = f"{LIBTV_PROJECT_CANVAS_BASE}{project_uuid}" if project_uuid else ""
    log(f"[LibTV] 会话已创建: {session_id}")
    if project_url:
        log(f"[LibTV] 项目画布: {project_url}")

    log("[LibTV] 等待生成（每 10 秒查询一次进度）...")
    last_seq = 0
    for attempt in range(1, 61):
        time.sleep(10)
        query_resp = _libtv_api_get(f"/openapi/session/{session_id}?afterSeq={last_seq}")
        if "error" in query_resp:
            log(f"[LibTV] 查询失败: {query_resp.get('error')}")
            continue

        messages = query_resp.get("data", {}).get("messages", [])
        if not messages:
            continue

        for msg in messages:
            last_seq = max(last_seq, msg.get("seq", last_seq))
            role = msg.get("role", "")
            content = msg.get("content", "")
            if role == "assistant":
                # 检查是否生成完成（assistant 返回了媒体 URL）
                media_urls = _extract_media_urls_from_messages([msg])
                if media_urls:
                    log(f"[LibTV] 检测到生成结果 ({len(media_urls)} 个文件)")
                    for i, url in enumerate(media_urls, 1):
                        log(f"   [{i}] {url}")
                        if url.endswith(".mp4"):
                            path = _download_media(url, f"video_{i}")
                            if path:
                                return path
                        else:
                            path = _download_media(url, f"image_{i}")
                            if path:
                                log(f"   [图片已保存] {path}")
                    # 如果有视频 URL 但下载失败，给出 projectUrl
                    if project_url:
                        log(f"[LibTV] 视频可能未自动下载，请在画布中手动导出:")
                        log(f"   {project_url}")
                        return project_url

        # 检查是否有错误状态
        for msg in messages:
            if msg.get("role") == "error" or "失败" in str(msg.get("content", "")):
                log(f"[LibTV] 生成失败: {msg.get('content', '')[:200]}")
                return None

    log("[LibTV] 轮询超时（10 分钟）")
    if project_url:
        log(f"[LibTV] 任务仍在进行中，请访问画布查看:")
        log(f"   {project_url}")
    return None


def print_fallback_info() -> None:
    """打印备用方案信息"""
    log("=" * 60)
    log("  [备用方案] LibTV — 专业级 AI 视频创作平台")
    log("=" * 60)
    log("""
当 Agnes API 不可用时，可切换到 LibTV 作为备用方案。

⚠️ 收费提醒:
  LibTV 新用户有免费额度，但超出后将按会员/积分收费。
  年卡最低 39 折，部分模型额外 6 折。
  详情: https://www.liblib.tv/

快速开始:
  1. 访问 https://www.liblib.tv/ 注册账号
  2. 进入项目 → 点击右上角【LibTV Skills】获取 Access Key
  3. 设置环境变量:
     Windows: set LIBTV_ACCESS_KEY=你的密钥
     Linux/macOS: export LIBTV_ACCESS_KEY=你的密钥
  4. 重新运行本工具，主方案失败时会自动尝试 LibTV

手动使用:
  也可以直接访问 LibTV 官网，在无限画布中拖拽节点生成视频。

项目地址: https://github.com/libtv-labs/libtv-skills
""")
    log("=" * 60)


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
        except urllib.error.URLError as e:
            log(f"\n[网络��误] {e.reason}")
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

    log("\n[等待] 正在生成视频，请耐心等候（通常 2-5 分钟）...")
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
                    # 国内站 API 将 URL 放在 metadata.url
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
                    if poll_count < MAX_POLLS:
                        time.sleep(interval)
                    continue

        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", errors="ignore")
            log(f"   [HTTP ERROR] {e.code}: {body[:200]}")
            if e.code < 500:
                log("   客户端错误，停止轮询")
                return None
        except urllib.error.URLError as e:
            log(f"   [网络错误] {e.reason}")
        except json.JSONDecodeError as e:
            log(f"   [数据解析错误] {e}")
        except OSError as e:
            log(f"   [系统错误] {e}")

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


def main() -> int:
    parser = argparse.ArgumentParser(description="Agnes Video 2.0 文生视频工具")
    parser.add_argument("prompt", nargs="*", help="视频描述")
    parser.add_argument("--duration", type=int, default=10, choices=[5, 10],
                        help="视频时长（秒），5或10，默认10")
    parser.add_argument("--fallback-info", action="store_true",
                        help="显示备用方案 LibTV 的使用指引")
    parser.add_argument("--resume", metavar="TASK_ID",
                        help="恢复指定 task_id 的轮询")
    args = parser.parse_args()

    if args.fallback_info:
        print_fallback_info()
        return 0

    log("=" * 60)
    log("  Agnes Video 2.0 Text-to-Video Tool (v2.0.0)")
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
    # +1 是因为 Agnes API 的 num_frames 参数包含首帧
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
        log("   尝试切换到备用方案 LibTV...")
        fallback_path = try_libtv_fallback(prompt, duration)
        if fallback_path:
            log(f"[完成] 备用方案生成成功! 视频已保存到: {fallback_path}")
            return 0
        else:
            log("   可能原因: API Key 无效 / 网络故障 / Agnes 服务暂时不可用")
            log("   建议: 1) 检查网络连接  2) 稍后重试  3) 查看备用方案")
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
        log("  [失败] 未获得视频，尝试切换到备用方案 LibTV...")
        fallback_path = try_libtv_fallback(prompt, duration)
        if fallback_path:
            log(f"[完成] 备用方案生成成功! 视频已保存到: {fallback_path}")
            return 0
        else:
            log("  [结束] 任务结束（未获得视频）")
            log("   建议: 1) 检查网络连接  2) 稍后重试  3) 查看备用方案")
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
