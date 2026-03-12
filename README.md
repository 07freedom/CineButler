# CineButler

[English](#cinebutler) | [中文](#中文)

A LangGraph-based media organization workflow that automatically identifies movies/TV series after Transmission downloads complete, renames them according to Infuse scraping rules, and moves them to target folders.

## Features

- Media type detection: movies, TV series, adult content (configurable skip)
- TMDB scraping: identify titles via LLM + TMDB API
- Infuse naming rules: `Title (Year)/Title (Year).ext`, `Show (Year)/Season XX/Show.SXXEXX.ext`
- Smart placement: prefer target with least free space when multiple; notify when space insufficient
- Configurable file operation: `cp` (default, keeps original) or `mv`
- Feishu (Lark) notification: send success/fail/skip results via OpenClaw

## Quick Start

### Install

```bash
cd /path/to/CineButler
uv sync
```

### Configure

1. Copy env template and fill in API keys:

```bash
cp .env.example .env
# Edit .env with LLM_BASE_URL, LLM_API_KEY, LLM_MODEL and TMDB_API_KEY
```

2. Copy `config.yaml.example` to `config.yaml`, set target folders and Feishu open_id.

### Environment Variables

| Variable | Description |
|----------|-------------|
| `LLM_BASE_URL` | LLM API base URL (e.g. `https://api.deepseek.com`) |
| `LLM_API_KEY` | LLM API key |
| `LLM_MODEL` | Model name (e.g. `deepseek-chat`) |
| `TMDB_API_KEY` | TMDB API key for scraping |
| `TMDB_BASE_URL` | *(optional)* TMDB reverse proxy URL |
| `FILE_OP_MODE` | `cp` (default, safe) or `mv` (move, saves space) |

### Usage

**CLI** (typically invoked by Transmission hook):

```bash
uv run cinebutler
# Reads TR_TORRENT_NAME / TORRENT_NAME, TR_TORRENT_DIR / TORRENT_DIR from env

# Or specify manually
uv run cinebutler "The Dark Knight.mkv" "/tmp/downloads" 1073741824
```

**Transmission hook integration**:

```bash
# One-liner install (edit hook-install.sh paths first)
bash hook-install.sh
```

Or manually:

- Copy `hooks/50-cinebutler.sh` to transmission-hook's `hooks.d/`
- Or add to `hooks.conf` HOOK_DIRS: `/path/to/CineButler/hooks`
- Ensure `50-cinebutler.sh` is executable

## config.yaml

```yaml
placement_rules:
  movie:
    targets: ["/mnt/media/movies", "/mnt/media2/movies"]
  tv:
    targets: ["/mnt/media/tv"]
  adult:
    action: skip   # skip | move

notification:
  feishu_target: "ou_xxx"    # Feishu open_id or group chat_id
  node_bin: "/path/to/nvm/node"

tmdb:
  api_key: ""     # Leave empty to read from .env
  language: "zh-CN"
```

## Project Structure

```
CineButler/
├── pyproject.toml
├── config.yaml
├── .env.example
├── hook-install.sh        # Hook install helper
├── src/cinebutler/
│   ├── main.py            # CLI entry
│   ├── config.py
│   ├── llm.py
│   ├── prompts.py
│   ├── workflow.py
│   ├── nodes/             # parse, identify, rename, place, notify
│   └── tools/             # tmdb, filesystem, notifier
├── hooks/
│   └── 50-cinebutler.sh
└── tests/
    ├── test_tmdb.py
    ├── test_movies.sh
    └── test_series.sh
```

## Test

```bash
# Python unit tests
uv run pytest tests/ -v

# Shell integration tests
bash tests/test_movies.sh
bash tests/test_series.sh
```

---

## 中文

[English](#cinebutler) | [中文](#中文)

基于 LangGraph 的媒体整理 Workflow，在 Transmission 下载完成后自动识别电影/剧集、按 Infuse 刮削规则重命名并放入目标文件夹。

### 功能

- 识别媒体类型：电影、剧集、成人内容（可配置跳过）
- TMDB 刮削：通过 LLM + TMDB API 识别作品
- Infuse 命名规则：`Title (Year)/Title (Year).ext`、`Show (Year)/Season XX/Show.SXXEXX.ext`
- 智能放置：多目标时优先选剩余空间最少的；空间不足时通知
- 可配置文件操作模式：`cp`（默认，保留原始文件）或 `mv`（移动，节省空间）
- 飞书通知：通过 OpenClaw 发送成功/失败/跳过结果

### 快速开始

#### 安装

```bash
cd /path/to/CineButler
uv sync
```

#### 配置

1. 复制环境变量模板并填写 API Key：

```bash
cp .env.example .env
# 编辑 .env，填写 LLM_BASE_URL、LLM_API_KEY、LLM_MODEL 和 TMDB_API_KEY
```

2. 复制 `config.yaml.example` 为 `config.yaml`，设置目标文件夹、飞书 open_id 等。

#### 环境变量

| 变量 | 说明 |
|------|------|
| `LLM_BASE_URL` | LLM API 地址（如 `https://api.deepseek.com`） |
| `LLM_API_KEY` | LLM API Key |
| `LLM_MODEL` | 模型名称（如 `deepseek-chat`） |
| `TMDB_API_KEY` | TMDB API Key，用于刮削识别 |
| `TMDB_BASE_URL` | *（可选）* TMDB 反代地址 |
| `FILE_OP_MODE` | `cp`（默认，安全）或 `mv`（移动，节省空间） |

#### 使用方式

**CLI 调用**（通常由 Transmission Hook 自动调用）：

```bash
uv run cinebutler
# 自动读取 TR_TORRENT_NAME / TORRENT_NAME, TR_TORRENT_DIR / TORRENT_DIR

# 或手动指定
uv run cinebutler "黑暗骑士.mkv" "/tmp/downloads" 1073741824
```

**Transmission Hook 集成**：

```bash
# 一键安装（先修改 hook-install.sh 中的路径）
bash hook-install.sh
```

或手动操作：

- 将 `hooks/50-cinebutler.sh` 复制到 transmission-hook 的 `hooks.d/`
- 或在 `hooks.conf` 的 `HOOK_DIRS` 中添加：`/path/to/CineButler/hooks`
- 确保 `50-cinebutler.sh` 可执行

#### 配置文件 config.yaml

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

#### 项目结构

```
CineButler/
├── pyproject.toml
├── config.yaml
├── .env.example
├── hook-install.sh        # Hook 安装脚本
├── src/cinebutler/
│   ├── main.py            # CLI 入口
│   ├── config.py
│   ├── llm.py
│   ├── prompts.py
│   ├── workflow.py
│   ├── nodes/             # parse, identify, rename, place, notify
│   └── tools/             # tmdb, filesystem, notifier
├── hooks/
│   └── 50-cinebutler.sh
└── tests/
    ├── test_tmdb.py
    ├── test_movies.sh
    └── test_series.sh
```

#### 测试

```bash
# Python 单元测试
uv run pytest tests/ -v

# Shell 集成测试
bash tests/test_movies.sh
bash tests/test_series.sh
```
