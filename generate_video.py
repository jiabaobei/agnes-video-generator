#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Agnes Video 2.0 文生视频工具
用法: python generate_video.py "你的视频描述"
"""

import os
import sys
import json
import time
import urllib.request
import urllib.error

# 修复 Windows 控制台编码
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# ==================== 配置区 ====================
API_KEY = "sk-wtQ84SRJzizAfKWm9m6hbzqYvg5S7rR2ZDlLKcHouC29ncpA"
BASE_URL = "https://apihub.agnes-ai.com/v1"
MODEL_NAME = "agnes-video-v2.0"

# 视频参数（可按需调整）
DEFAULT_WIDTH = 1152
DEFAULT_HEIGHT = 768
DURATION_SECONDS = 10  # 10秒（常用）
NUM_FRAMES = 241       # 10秒 × 24帧 = 241帧
FRAME_RATE = 24


def submit_video_task(prompt):
    """提交视频生成任务，返回 task_id"""
    url = f"{BASE_URL}/videos"
    
    payload = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "width": DEFAULT_WIDTH,
        "height": DEFAULT_HEIGHT,
        "num_frames": NUM_FRAMES,
        "frame_rate": FRAME_RATE
    }
    
    data = json.dumps(payload).encode('utf-8')
    
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    req = urllib.request.Request(url, data=data, headers=headers, method='POST')
    
    try:
        with urllib.request.urlopen(req, timeout=60) as response:
            result = json.loads(response.read().decode('utf-8'))
            task_id = result.get("task_id")
            if task_id:
                print(f"\n✅ 任务已提交！Task ID: {task_id}")
                return task_id
            else:
                print(f"\n❌ 提交失败: {result}")
                sys.exit(1)
    except urllib.error.HTTPError as e:
        body = e.read().decode('utf-8', errors='ignore')
        print(f"\n❌ HTTP 错误 {e.code}: {body}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 提交任务时出错: {e}")
        sys.exit(1)


def poll_video_status(task_id, interval=10):
    """轮询视频任务状态，直到完成或失败"""
    url = f"{BASE_URL}/videos/{task_id}"
    
    headers = {
        "Authorization": f"Bearer {API_KEY}"
    }
    
    print("\n⏳ 正在生成视频，请耐心等待（通常2-3分钟）...")
    print("   （每10秒检查一次进度）\n")
    
    while True:
        time.sleep(interval)
        
        req = urllib.request.Request(url, headers=headers)
        
        try:
            with urllib.request.urlopen(req, timeout=30) as response:
                result = json.loads(response.read().decode('utf-8'))
                
                status = result.get("status", "unknown")
                print(f"   状态: {status}")
                
                if status == "completed":
                    print(f"\n🎉 视频生成完成！\n")
                    # 兼容不同的字段名
                    video_url = result.get("video_url") or result.get("remixed_from_video_id")
                    if video_url:
                        print(f"📹 视频地址: {video_url}")
                        
                        # 下载视频
                        download_video(video_url, task_id)
                        return video_url
                    else:
                        print("⚠️ 未找到视频地址，原始响应:")
                        print(json.dumps(result, indent=2, ensure_ascii=False))
                        return None
                        
                elif status == "failed":
                    print(f"\n❌ 视频生成失败:")
                    print(f"   原因: {result.get('error', '未知')}")
                    sys.exit(1)
                    
                elif status == "processing":
                    print(f"   处理中...")
                    
        except urllib.error.HTTPError as e:
            body = e.read().decode('utf-8', errors='ignore')
            print(f"   HTTP 错误 {e.code}: {body[:200]}")
            if e.code < 500:
                break
            continue
        except Exception as e:
            print(f"   轮询出错: {e}")
            continue


def download_video(video_url, task_id):
    """下载视频到本地"""
    output_dir = "outputs"
    os.makedirs(output_dir, exist_ok=True)
    
    # 用 task_id 或时间戳命名
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    filename = f"agnes_video_{timestamp}.mp4"
    filepath = os.path.join(output_dir, filename)
    
    print(f"📥 正在下载到: {filepath}")
    
    try:
        urllib.request.urlretrieve(video_url, filepath)
        filesize_mb = os.path.getsize(filepath) / 1024 / 1024
        print(f"✅ 下载完成！文件大小: {filesize_mb:.2f} MB")
        print(f"📁 文件路径: {os.path.abspath(filepath)}")
    except Exception as e:
        print(f"❌ 下载失败: {e}")
        print(f"\n🔗 你可以手动从以下地址下载: {video_url}")


def main():
    print("=" * 60)
    print("  Agnes Video 2.0 文生视频工具")
    print("=" * 60)
    
    if len(sys.argv) > 1:
        prompt = " ".join(sys.argv[1:])
    else:
        prompt = input("\n请输入视频描述 (English works best):\n  > ").strip()
    
    if not prompt:
        print("❌ 描述不能为空！")
        sys.exit(1)
    
    print(f"\n📝 描述: {prompt}")
    print(f"🎬 模型: {MODEL_NAME}")
    print(f"⏱️ 时长: {DURATION_SECONDS}秒 ({NUM_FRAMES}帧 @ {FRAME_RATE}fps)")
    print(f"📐 分辨率: {DEFAULT_WIDTH}x{DEFAULT_HEIGHT}")
    print("-" * 60)
    
    # Step 1: 提交任务
    task_id = submit_video_task(prompt)
    
    # Step 2: 轮询状态
    poll_video_status(task_id)
    
    print("\n" + "=" * 60)
    print("  🎉 全部完成！")
    print("=" * 60)


if __name__ == "__main__":
    main()
