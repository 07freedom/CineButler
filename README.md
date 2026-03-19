# CineButler
![Banner](assets/banner.png)

[English](#cinebutler) | [中文](#中文)

A LangGraph-based media organization workflow that automatically identifies movies/TV series after Transmission downloads complete, renames them according to Infuse scraping rules, and moves them to target folders.

## Features

- Media type detection: movies, TV series, adult content (configurable skip)
- TMDB scraping: identify titles via LLM + TMDB API
- Infuse naming: `Title (Year).ext`, `Show/Season XX/Show.SXXEXX {tmdb-id}.ext`
- Smart placement: balanced across multiple target drives, space-aware
- Smart TV season matching: scans existing folder structure and lets LLM decide the correct subfolder
- Duplicate detection: skip or overwrite when destination file already exists
- Configurable per-type action: `mv`, `cp`, or `skip`
- Notification via OpenClaw: feishu, telegram, and more (with warning alerts for duplicates)

## Quick Start

### Install

```bash
cd /path/to/CineButler
uv sync
```

### Configure

**Step 1 — Secrets (`.env`)**

Put API keys and service URLs here. This file should never be committed.

```bash
cp .env.example .env
# Edit .env and fill in your keys
```

| Variable | Required | Description |
|----------|----------|-------------|
| `LLM_BASE_URL` | ✅ | LLM API base URL (e.g. `https://api.deepseek.com`) |
| `LLM_API_KEY` | ✅ | LLM API key |
| `LLM_MODEL` | ✅ | Model name (e.g. `deepseek-chat`) |
| `TMDB_API_KEY` | ✅ | TMDB API key — get one free at [themoviedb.org](https://www.themoviedb.org/settings/api) |
| `TMDB_BASE_URL` | ☑️ optional | TMDB reverse proxy URL (omit to use the official endpoint) |

**Step 2 — Daily config (`config.yaml`)**

Put target directories, actions, notifications, and naming preferences here.

```bash
cp config.yaml.example config.yaml
# Edit config.yaml
```

| Section | Description |
|---------|-------------|
| `targets` | Destination directories per media type (supports multiple drives) |
| `actions` | Per-type file operation: `mv`, `cp`, or `skip` |
| `actions.on_duplicate` | Behavior when destination file already exists: `skip` (default) or `overwrite` |
| `notification` | OpenClaw channel, target ID, and node binary path |
| `tmdb.language` | Preferred metadata language (e.g. `zh-CN`, `en-US`) |
| `file_naming` | `infuse` (Infuse/TMDB standard) or `raw` (keep original filename) |

### Usage

**CLI** (typically invoked by the Transmission hook):

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

- Copy `hooks/50-cinebutler.sh` to your transmission-hook `hooks.d/` directory
- Ensure the script is executable

## config.yaml

```yaml
# Destination directories — multiple paths supported per type
targets:
  movie:
    - /mnt/disk1/Movies
  tv:
    - /mnt/disk1/Series

# File operation per media type
actions:
  movie: mv      # mv | cp | skip
  tv: mv
  adult: skip
  unknown: skip
  on_duplicate: skip  # skip | overwrite

# Notification via OpenClaw
notification:
  channel: feishu   # telegram|whatsapp|discord|slack|feishu|signal|imessage|msteams|mattermost|matrix|...
  target: "ou_xxx"
  node_bin: "/path/to/node/bin"

tmdb:
  api_key: ""       # leave empty — set TMDB_API_KEY in .env instead
  language: "zh-CN"

file_naming: infuse  # infuse | raw
```

## Project Structure

```
CineButler/
├── config.yaml          # daily config (targets, actions, notifications)
├── config.yaml.example
├── .env                 # secrets (API keys, URLs) — do not commit
├── .env.example
├── hook-install.sh
├── src/cinebutler/
│   ├── main.py
│   ├── config.py
│   ├── workflow.py
│   ├── nodes/           # classify, match, name, place, notify
│   └── tools/           # tmdb, filesystem, notifier
├── hooks/
│   └── 50-cinebutler.sh
└── tests/
```

## Test

```bash
uv run pytest tests/ -v
```

---

## 中文

[English](#cinebutler) | [中文](#中文)

基于 LangGraph 的媒体整理 Workflow，在 Transmission 下载完成后自动识别电影/剧集、按 Infuse 刮削规则重命名并放入目标文件夹。

### 功能

- 识别媒体类型：电影、剧集、成人内容（可配置跳过）
- TMDB 刮削：通过 LLM + TMDB API 识别作品
- Infuse 命名规则：`Title (Year).ext`、`Show/Season XX/Show.SXXEXX {tmdb-id}.ext`
- 智能放置：多磁盘均衡、空间感知
- 剧集季度匹配：扫描已有目录结构，由 LLM 判断放入正确的子文件夹
- 重复文件检测：目标位置已存在同名文件时可选跳过或覆盖
- 按类型配置操作：`mv`、`cp` 或 `skip`
- 通过 OpenClaw 推送通知：支持飞书、Telegram 等（重复文件会触发黄色警告）

### 快速开始

#### 安装

```bash
cd /path/to/CineButler
uv sync
```

#### 配置

**第一步 — 密钥（`.env`）**

仅放 API Key 和服务地址，不应提交到版本库。

```bash
cp .env.example .env
# 编辑 .env，填写实际值
```

| 变量 | 是否必填 | 说明 |
|------|----------|------|
| `LLM_BASE_URL` | ✅ | LLM API 地址（如 `https://api.deepseek.com`） |
| `LLM_API_KEY` | ✅ | LLM API Key |
| `LLM_MODEL` | ✅ | 模型名称（如 `deepseek-chat`） |
| `TMDB_API_KEY` | ✅ | TMDB API Key，在 [themoviedb.org](https://www.themoviedb.org/settings/api) 免费申请 |
| `TMDB_BASE_URL` | ☑️ 可选 | TMDB 反代地址（留空使用官方地址） |

**第二步 — 日常配置（`config.yaml`）**

目标目录、操作模式、通知渠道、命名规则等均在此配置。

```bash
cp config.yaml.example config.yaml
# 编辑 config.yaml
```

| 配置项 | 说明 |
|--------|------|
| `targets` | 按媒体类型配置目标目录，支持多个路径（多盘） |
| `actions` | 每种类型的文件操作：`mv`、`cp` 或 `skip` |
| `actions.on_duplicate` | 目标位置存在同名文件时的行为：`skip`（默认）或 `overwrite` |
| `notification` | OpenClaw 渠道、接收方 ID、node 路径 |
| `tmdb.language` | 元数据首选语言（如 `zh-CN`、`en-US`） |
| `file_naming` | `infuse`（Infuse/TMDB 标准重命名）或 `raw`（保留原始文件名） |

#### 使用方式

**CLI**（通常由 Transmission Hook 自动调用）：

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

或手动操作：将 `hooks/50-cinebutler.sh` 复制到 transmission-hook 的 `hooks.d/` 并确保可执行。

#### 配置文件 config.yaml

```yaml
# 目标目录，每种类型支持多个路径
targets:
  movie:
    - /mnt/disk1/Movies
  tv:
    - /mnt/disk1/Series

# 每种媒体类型的操作
actions:
  movie: mv      # mv | cp | skip
  tv: mv
  adult: skip
  unknown: skip
  on_duplicate: skip  # skip | overwrite

# 通过 OpenClaw 发送通知
notification:
  channel: feishu   # telegram|whatsapp|discord|slack|feishu|signal|imessage|msteams|mattermost|matrix|...
  target: "ou_xxx"
  node_bin: "/path/to/node/bin"

tmdb:
  api_key: ""       # 留空，从 .env 的 TMDB_API_KEY 读取
  language: "zh-CN"

file_naming: infuse  # infuse | raw
```

#### 测试

```bash
uv run pytest tests/ -v
```
