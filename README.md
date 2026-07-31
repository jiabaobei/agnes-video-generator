# Agnes Video 2.0 - 免费文生视频工具

> **✨ 免费生成AI视频！只需一段文字描述，2-3分钟即可获得短视频！**

[![Version](https://img.shields.io/badge/version-2.0.0-blue)]()
[![License](https://img.shields.io/badge/license-MIT-green)]()
[![Python](https://img.shields.io/badge/python-3.8%2B-yellow)]()

## 🎬 功能亮点

- **完全免费**：Agnes AI 无限期免费开放 API，无需绑定银行卡
- **开箱即用**：脚本已内置免费 API Key，下载后直接使用，无需任何配置
- **双时长支持**：5秒短视频 / 10秒标准视频，通过 `--duration` 参数切换
- **一键操作**：输入描述 → 自动轮询 → 自动下载，全流程自动化
- **跨平台**：纯 Python 标准库实现，无需安装第三方依赖
- **🆕 备用方案**：内置 LibTV 备用方案，主方案故障时引导用户使用（新用户有免费额度，超出后按会员/积分收费）

## 🔄 备用方案：LibTV

当 Agnes API 不可用时（算力卡顿、服务宕机、网络故障），可立即切换到 **LibTV**：

- **项目地址**：https://www.liblib.tv/
- **定位**：专业级 AI 视频创作平台，集成 Seedance 2.0、可灵 3.0、Wan 2.6 等 30+ 顶级视频模型
- **核心能力**：无限画布 + 节点式工作流，支持剧本生成、分镜设计、图生视频、视频编辑
- **免费额度**：新用户有免费额度，订阅用户最高赠送 300 条免费顶级视频额度
- **成本**：年卡最低 39 折，部分模型额外 6 折；会员 SKU 价格比主流竞品低 76%

> ⚠️ **收费提醒**：LibTV 是付费备选方案，免费额度用完后将按会员/积分收费。
> 请确认剩余额度后再使用，或访问官网了解最新价格。

**快速切换**：
```bash
# 查看备用方案详情
python generate_video.py --fallback-info

# 或直接访问 LibTV 官网注册使用
https://www.liblib.tv/
```

**手动使用步骤**：
1. 访问 https://www.liblib.tv/ 注册账号
2. 进入项目 → 点击右上角【LibTV Skills】获取 Access Key
3. 设置环境变量: `set LIBTV_ACCESS_KEY=你的密钥`（Windows）或 `export LIBTV_ACCESS_KEY=你的密钥`（macOS/Linux）
4. 重新运行本工具，主方案失败时会自动尝试 LibTV

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
| `--fallback-info` | flag | false | 显示备用方案 LibTV 的使用指引 |
| `--resume` | string | - | 恢复指定 task_id 的轮询（中断后继续） |

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

### 安全与可靠性

- **URL 校验**：下载前校验视频 URL 必须为 `https` 且域名属于 Agnes 白名单，防止中间人攻击
- **异常处理**：细化了 `urllib.error.URLError`、`json.JSONDecodeError`、`OSError` 等具体异常，不再吞掉所有错误
- **文件名冲突**：文件名含毫秒+随机后缀，同秒多次运行也不会覆盖
- **中断恢复**：`--resume <task_id>` 可恢复中断的轮询，无需重新提交

### 超时与重试

- **提交超时**：300秒（Agnes 服务端响应可能较慢）
- **重试次数**：3次
- **轮询间隔**：10秒，首轮不等待（避免已完成的请求多等 10 秒），最多轮询60次

## ❓ 常见问题

### Q: 视频生成需要多久？
A: 实际生成约2分钟，加上排队和API响应时间，总共约3-6分钟。

### Q: 为什么我请求的 1152x768 但输出是 1088x832？
A: Agnes API 会忽略 width/height 参数，固定输出 1088×832。这是 API 的行为，不是 bug。

### Q: 视频质量怎么样？
A: Agnes Video V2.0 在公开排行榜 Elo 分数约 934，适合风景、物体等场景，复杂动作（如跳舞）效果可能一般。

### Q: 想换成自己的 API Key 怎么办？
A: 打开 `generate_video.py`，把第 23 行的 `API_KEY` 值改成你自己的即可。

### Q: 轮询时按 Ctrl+C 中断了怎么办？
A: 重新运行 `python generate_video.py --resume <之前的 task_id>` 即可继续等待，无需重新提交。

### Q: 备用方案（LibTV）怎么用？
A: 先运行 `python generate_video.py --fallback-info` 查看指引。LibTV 需要注册账号并获取 Access Key，新用户有免费额度，超出后按会员/积分收费。

## 📄 许可证

MIT License

## 🙏 致谢

- [Agnes AI](https://agnes-ai.com) - 提供免费的文生视频 API

## 📋 更新日志

### v2.0.0
- **备用方案切换为 LibTV**：移除 OpenMontage 备用方案（过于复杂，无法自动切换），改为 LibTV 作为付费备选方案
- **新增收费提醒界面**：使用 LibTV 前弹出明确提醒，告知用户免费额度用完后将收费
- **LibTV 自动集成**：设置 `LIBTV_ACCESS_KEY` 环境变量后，主方案失败时自动尝试 LibTV
- **删除 OpenMontage 相关代码**：`ensure_openmontage()`、`try_openmontage_fallback()` 等函数已移除

### v1.4.1
- **国内节点修复**：BASE_URL 改为 `https://apihub.agnes-ai.cn/v1`（Agnes 2026-07-29 上线国内站）
- 域名白名单新增 `apihub.agnes-ai.cn`、`platform-outputs.agnes-ai.space`、`agnes-ai.space`
- 新增 `metadata.url` 提取逻辑（国内站 API 视频地址字段）
- `.gitignore` 新增 `outputs/` 和 `.agnes_tasks.json`

### v1.4.0
- **安全加固**：下载视频前校验 URL scheme（必须 https）和域名白名单（agnes-ai.com 子域），防止恶意链接
- **修复轮询延迟**：首轮不 sleep，已完成的请求不再多等 10 秒
- **文件名防冲突**：追加毫秒+随机后缀，同秒多次运行也不会覆盖
- **异常处理细化**：区分 `URLError`、`JSONDecodeError`、`OSError`，不再裸 `except Exception`
- **日志兜底**：`log()` 函数最后一层写入 `sys.stderr`，不再完全静默
- **输入校验**：prompt 限制 1000 字符，自动 strip 空白
- **常量集中管理**：超时、重试、轮询间隔等全部集中到顶部配置区
- **User-Agent**：请求头加上 `AgnesVideoTool/1.4.0`
- **中断恢复**：新增 `--resume <task_id>` 参数，支持断点续轮询
- **备用方案诚实化**：不再自动 import/make demo/克隆 OpenMontage（注定失败），改为检测本地已启动的服务（端口 3000），诚实告知用户手动启动步骤

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
