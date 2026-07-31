---
name: agnes-video-generator
description: 免费生成AI视频的工具。用户输入视频描述后，调用 Agnes AI 的文生视频模型生成带声音的短视频，自动轮询生成进度并下载视频。主方案故障时自动切换到 OpenMontage 备用方案。
---

# Agnes Video 2.0 - 文生视频工具

## 概述

使用 Agnes AI 平台的 `agnes-video-v2.0` 模型，将文字描述转换为短视频。完全免费，无需绑定银行卡。

**备用方案**：当 Agnes API 不可用时，自动切换到 [OpenMontage](https://github.com/calesthio/OpenMontage)（智能体驱动型视频制作系统，支持 15+ 视频生成提供商）。

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
5. **故障切换** → 若 Agnes API 失败，运行 `python generate_video.py --fallback-info` 查看 OpenMontage 备用方案

## API 配置

- **Base URL**: `https://apihub.agnes-ai.com/v1`
- **Model**: `agnes-video-v2.0`
- **时长**: 默认10秒（241帧），也可通过 `--duration 5` 改为5秒
- **帧率**: 24 fps
- **实际输出分辨率**: 1088×832（API 固定输出）
- **视频格式**: MP4（自带 AAC 音频）

## 注意事项

- 脚本已内置 API Key，开箱即用
- Windows 编码已处理，不会出现乱码
- 脚本内置3次重试机制，应对 API 超时
- 视频生成结果保存在 `outputs/` 文件夹中
- 英文 prompt 效果通常更好
- 适合风景、动物、静物等场景，复杂动作效果有限

## 版本

v1.2.0
