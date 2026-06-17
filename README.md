# Agnes Video 2.0 - 免费文生视频工具

> **✨ 免费生成AI视频！只需一段文字描述，2-3分钟即可获得短视频！**

## 🎬 功能亮点

- **完全免费**：Agnes AI 无限期免费开放 API，无需绑定银行卡
- **开箱即用**：脚本已内置免费 API Key，下载后直接使用，无需任何配置
- **双时长支持**：5秒短视频 / 10秒标准视频，通过 `--duration` 参数切换
- **一键操作**：输入描述 → 自动轮询 → 自动下载，全流程自动化
- **跨平台**：纯 Python 标准库实现，无需安装第三方依赖

## 📋 快速开始

### 1. 下载脚本

```bash
git clone https://github.com/jiabaobei/agnes-video-generator.git
cd agnes-video-generator
```

或者直接在 GitHub 页面点击 `Code` → `Download ZIP` 下载解压。

### 2. 运行（直接就能用！）

```bash
# 生成10秒视频（默认）
python generate_video.py "A cute cat playing with a ball of yarn"

# 生成5秒短视频
python generate_video.py "A marmot waving its paw on a grassland" --duration 5

# 交互式输入（不传 prompt 参数）
python generate_video.py
```

> ✅ **无需配置 API Key，脚本已内置，直接运行即可！**

## ⚙️ 命令行参数

| 参数 | 类型 | 默认 | 说明 |
|------|------|------|------|
| `prompt` | 位置参数（可选） | - | 视频描述，不传则交互式输入 |
| `--duration` | int | 10 | 视频时长，支持 `5` 或 `10` 秒 |

## 📝 视频描述技巧

- **英文效果更好**：模型训练数据以英文为主
- **包含场景描述**：光线、背景、动作、氛围
- **具体动作优于抽象描述**：用 "waving paw" 代替 "dancing"，模型更容易理解
- **示例**：
  - `A cute cat playing with a ball of yarn on a sunny afternoon`
  - `Red sports car driving on a mountain road at sunset`
  - `A chef cooking in a Chinese restaurant kitchen, steam rising`

## 🎥 输出规格

| 属性 | 值 |
|------|------|
| 格式 | MP4 |
| 时长 | 5秒（121帧）或 10秒（241帧）|
| 分辨率 | 1088×832（API 固定输出）|
| 帧率 | 24 fps |
| 生成耗时 | 约2-5分钟 |

## 🔧 技术细节

### 视频URL获取方式

视频生成完成后，API 返回的 JSON 中，视频 URL 在 `remixed_from_video_id` 字段中，脚本已自动兼容提取。

### 超时与重试

- **提交超时**：300秒（Agnes 服务端响应可能较慢）
- **重试次数**：3次
- **轮询间隔**：10秒，最多轮询60次

## ❓ 常见问题

### Q: 视频生成需要多久？
A: 实际生成约2分钟，加上排队和API响应时间，总共约3-6分钟。

### Q: 为什么我请求的 1152x768 但输出是 1088x832？
A: Agnes API 会忽略 width/height 参数，固定输出 1088×832。这是 API 的行为，不是 bug。

### Q: 视频质量怎么样？
A: Agnes Video V2.0 在公开排行榜 Elo 分数约 934，适合风景、物体等场景，复杂动作（如跳舞）效果可能一般。

### Q: 想换成自己的 API Key 怎么办？
A: 打开 `generate_video.py`，把第 23 行的 `API_KEY` 值改成你自己的即可。

## 📄 许可证

MIT License

## 🙏 致谢

- [Agnes AI](https://agnes-ai.com) - 提供免费的文生视频 API

## 📋 更新日志

### v1.1.1
- 恢复 API Key 硬编码（开箱即用，无需配置）
- 优化 README，降低使用门槛
- 改进错误提示信息

### v1.1.0
- 新增 `--duration 5|10` 参数
- 修复视频 URL 字段名（`remixed_from_video_id`）
- 提交超时提升至 300s
- 移除无效的 width/height 参数
- 改进 Windows 编码兼容性

### v1.0.0
- 初始版本
