# Agnes Video 2.0 - 文生视频工具

> **✨ 免费生成高质量AI视频！只需一段文字描述，2-3分钟即可获得带声音的10秒短视频！**

## 🎬 功能亮点

- **完全免费**：Agnes AI 无限期免费开放 API，无需绑定银行卡
- **中英文双语**：原生支持中文描述，自动生成中英文对话音频
- **视频带声音**：自动生成 AAC 音频，无需额外配音
- **一键操作**：输入描述 → 自动轮询 → 自动下载，全流程自动化
- **多种分辨率**：支持 720P/1080P，默认 1152x768 高清

## 📋 快速开始

### 前置条件
- Python 3.8+
- Agnes AI API Key（免费获取：https://platform.agnes-ai.com）

### 安装配置
```bash
# 克隆仓库
git clone https://github.com/donghai2026/agnes-video-generator.git
cd agnes-video-generator

# 编辑 manifest.json，填入你的 API Key
# api_key: "sk-你的API Key"
```

### 使用方法
```bash
# 运行脚本，输入视频描述
python generate_video.py "A cute shiba inu sleeping under cherry blossom trees"
```

## ⚙️ 配置说明

在 `manifest.json` 中修改以下配置：
- `api_key`: 你的 Agnes AI API Key
- `model`: 视频模型名称（默认：agnes-video-v2.0）
- `duration_seconds`: 视频时长（默认：10秒）
- `resolution`: 视频分辨率（默认：1152x768）

## 📝 视频描述技巧

- **英文效果更好**：模型训练数据以英文为主
- **包含场景描述**：光线、背景、动作、氛围
- **指定对话内容**：在描述中加入 `saying '...'` 可生成指定台词
- **示例**：
  - `A Chinese dumpling restaurant, chef is speaking Chinese to customers, saying '欢迎光临，请坐'`
  - `Red sports car driving on a mountain road at sunset`

## 🎥 输出格式

- **格式**: MP4
- **音频**: AAC（支持中英文对话）
- **时长**: 10秒（可调，5-18秒）
- **分辨率**: 1152x768（可调）

## 🔧 高级配置

### 修改视频时长
```python
# 5秒视频
NUM_FRAMES = 121  # 121帧 @ 24fps = ~5秒

# 10秒视频（默认）
NUM_FRAMES = 241  # 241帧 @ 24fps = ~10秒

# 18秒视频
NUM_FRAMES = 441  # 441帧 @ 24fps = ~18秒
```

## ❓ 常见问题

### Q: 视频生成需要多久？
A: 通常需要2-3分钟，请耐心等待。

### Q: 支持中文描述吗？
A: 支持，但英文效果更佳。脚本会自动处理中文描述。

### Q: 视频有声音吗？
A: 有！自动生成 AAC 音频，支持中英文对话。

### Q: API Key 哪里获取？
A: 访问 https://platform.agnes-ai.com 注册并获取免费 API Key。

## 📄 许可证

MIT License

## 🙏 致谢

- [Agnes AI](https://agnes-ai.com) - 提供免费的文生视频 API
- [Vercel Labs](https://vercel.com) - Skills 框架
