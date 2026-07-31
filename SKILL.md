---
name: agnes-video-generator
description: 免费生成AI视频的工具。用户输入视频描述后，调用 Agnes AI 的文生视频模型生成带声音的短视频，自动轮询生成进度并下载视频。主方案故障时自动切换到 LibTV 备用方案（付费，新用户有免费额度）。
---

# Agnes Video 2.0 - 文生视频工具

## 概述

使用 Agnes AI 平台的 `agnes-video-v2.0` 模型，将文字描述转换为短视频。完全免费，无需绑定银行卡。

**备用方案**：当 Agnes API 不可用时，自动切换到 [LibTV](https://www.liblib.tv/)（专业级 AI 视频创作平台，集成 Seedance 2.0、可灵 3.0、Wan 2.6 等 30+ 顶级视频模型）。

> ⚠️ LibTV 新用户有免费额度，超出后按会员/积分收费。使用前请确认剩余额度。

## 快速开始

### 前置条件

- Python 3.8+
- 免费 API Key（在 https://platform.agnes-ai.com 注册获取）

### 使用方法

```bash
# 生成10秒视频（默认）
python generate_video.py "描述内容"

# 交互式输入
python generate_video.py
```

## 使用流程

1. **接收用户描述** → 用自然语言描述想要的视频
2. **运行脚本** → 执行 `generate_video.py`
3. **等待生成** → 脚本自动轮询，通常 2-5 分钟
4. **获取视频** → 视频自动保存到 `outputs/` 目录
5. **故障切换（LibTV）** → 若 Agnes API 失败，脚本自动尝试 LibTV（需设置 `LIBTV_ACCESS_KEY` 环境变量）

## 备用方案使用

### LibTV 手动使用

1. 访问 https://www.liblib.tv/ 注册账号
2. 进入项目 → 点击右上角【LibTV Skills】获取 Access Key
3. 设置环境变量: `set LIBTV_ACCESS_KEY=你的密钥`（Windows）
4. 重新运行本工具，主方案失败时会自动尝试 LibTV

## 版本

v2.0.0
