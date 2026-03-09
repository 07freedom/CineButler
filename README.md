# CineButler

基于 LangGraph 的媒体整理 Workflow，在 Transmission 下载完成后自动识别电影/剧集、按 Infuse 刮削规则重命名并放入目标文件夹。

## 功能

- 识别媒体类型：电影、剧集、成人内容（可配置跳过）
- TMDB 刮削：通过 LLM + TMDB API 识别作品
- Infuse 命名规则：`Title (Year)/Title (Year).ext`、`Show (Year)/Season XX/Show.SXXEXX.ext`
- 智能放置：多目标时优先选剩余空间最少的；空间不足时通知
- 安全：仅使用 `mv` 命令
- 飞书通知：通过 OpenClaw 发送成功/失败/跳过结果

## 快速开始

### 安装

```bash
cd /path/to/CineButler
uv sync
```

### 配置

1. 复制环境变量模板并填写 API Key：

```bash
cp .env.example .env
# 编辑 .env，填写 LLM_PROVIDERS 和 TMDB_API_KEY
```

2. 复制 `config.yaml.example` 为 `config.yaml`，设置目标文件夹、飞书 open_id 等。

### 环境变量

| 变量 | 说明 |
|------|------|
| `LLM_PROVIDERS` | JSON 数组，按优先级配置多个 LLM（DeepSeek、OpenRouter 等） |
| `TMDB_API_KEY` | TMDB API Key，用于刮削识别 |

### 使用方式

**CLI 调用**（通常由 Transmission Hook 自动调用）：

```bash
uv run cinebutler
# 自动读取环境变量 TR_TORRENT_NAME, TR_TORRENT_DIR, TR_TORRENT_BYTES_DOWNLOADED

# 或手动指定
uv run cinebutler "黑暗骑士.mkv" "/tmp/downloads" 1073741824
```

**Transmission Hook 集成**：

- 将 `hooks/50-cinebutler.sh` 复制到 transmission-hook 的 `hooks.d/`
- 或在 `hooks.conf` 的 `HOOK_DIRS` 中添加：`/home/tth/src/CineButler/hooks`
- 确保 `50-cinebutler.sh` 可执行

## 配置文件 config.yaml

```yaml
placement_rules:
  movie:
    targets: ["/mnt/media/movies", "/mnt/media2/movies"]
  tv:
    targets: ["/mnt/media/tv"]
  adult:
    action: skip   # skip | move

notification:
  feishu_target: "ou_xxx"    # 飞书 open_id 或群 chat_id
  node_bin: "/path/to/nvm/node"

tmdb:
  api_key: ""     # 留空则从 .env 读取
  language: "zh-CN"
```

## 项目结构

```
CineButler/
├── pyproject.toml
├── config.yaml
├── .env.example
├── src/cinebutler/
│   ├── main.py        # CLI 入口
│   ├── config.py
│   ├── llm.py
│   ├── workflow.py
│   ├── nodes/         # parse, identify, rename, place, notify
│   └── tools/         # tmdb, filesystem, notifier
├── hooks/
│   └── 50-cinebutler.sh
└── tests/
    └── test_workflow.py
```

## 测试

```bash
uv run pytest tests/ -v
```
