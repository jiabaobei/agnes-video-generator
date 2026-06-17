---
name: agnes-video-generator
description: 免费生成AI视频的工具。用户输入视频描述后，调用 Agnes AI 的文生视频模型生成带声音的短视频（5秒或10秒），自动轮询生成进度并下载视频。
allowed-tools: []
---

# Agnes Video 2.0 - 文生视频工具

## 概述

使用 Agnes AI 平台的 `agnes-video-v2.0` 模型，将文字描述转换为短视频。完全免费，无需绑定银行卡。

## 快速开始

### 前置条件

- Python 3.8+
- Agnes AI API Key（免费注册获取）

### 视频生成脚本位置

```
C:\Users\user\WorkBuddy\agnes-video-generator-skills\generate_video.py
```

### 使用方法

```bash
# 生成10秒视频（默认）
python "C:\Users\user\WorkBuddy\agnes-video-generator-skills\generate_video.py" "描述内容"

# 生成5秒短视频
python "C:\Users\user\WorkBuddy\agnes-video-generator-skills\generate_video.py" "描述内容" --duration 5

# 交互式输入
python "C:\Users\user\WorkBuddy\agnes-video-generator-skills\generate_video.py"
```

## 使用流程

1. **接收用户描述** → 转换为英文 prompt（如果用户给的是中文）
2. **运行脚本** → 使用上面的命令
3. **等待生成** → 脚本自动轮询，通常 2-5 分钟
4. **下载视频** → 视频自动保存到 `outputs/` 目录
5. **交付用户** → 告知视频文件位置

## API 配置

- **Base URL**: `https://apihub.agnes-ai.com/v1`
- **Model**: `agnes-video-v2.0`
- **时长**: 5秒（121帧）或 10秒（241帧），通过 `--duration` 参数控制
- **帧率**: 24 fps
- **实际输出分辨率**: 1088×832（API 固定，不受参数控制）
- **视频格式**: MP4

## 注意事项

- **脚本内置 API Key**，无需额外配置
- Windows 控制台编码已处理，不会出现乱码
- API 提交请求可能超时，脚本内置 3 次重试（每次等待 300 秒）
- 视频生成结果保存在 `generate_video.py` 同级目录的 `outputs/` 文件夹中
- Agnes Video V2.0 适合风景、物体、静态场景视频，复杂动作效果有限
- 英文 prompt 效果优于中文

## 输出文件

```
<脚本所在目录>/
├── generate_video.py       # 主脚本
├── outputs/
│   └── agnes_video_YYYYMMDD_HHMMSS.mp4  # 生成的视频
├── manifest.json           # 包配置
└── README.md               # 说明文档
```

## 版本

v1.1.1
