#!/bin/bash
#
# CineButler Transmission hook: 下载完成后整理媒体文件
# 将本脚本复制到 transmission-hook/hooks.d/ 或把 CineButler/hooks 加入 HOOK_DIRS
#
# 依赖: TR_TORRENT_NAME, TR_TORRENT_DIR, TR_TORRENT_BYTES_DOWNLOADED (由 Transmission 设置)
#

CINEBUTLER_DIR="/home/tth/src/CineButler"
LOG_FILE="${CINEBUTLER_DIR}/logs/hook.log"

# 初始化日志目录
mkdir -p "$(dirname "$LOG_FILE")"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" >> "$LOG_FILE"
}

log "===== Hook 触发 ====="
log "脚本路径: $0"
log "运行用户: $(id)"
log "TR_TORRENT_NAME=${TR_TORRENT_NAME:-<未设置>}"
log "TR_TORRENT_DIR=${TR_TORRENT_DIR:-<未设置>}"
log "TR_TORRENT_BYTES_DOWNLOADED=${TR_TORRENT_BYTES_DOWNLOADED:-<未设置>}"
log "TR_TORRENT_ID=${TR_TORRENT_ID:-<未设置>}"

if [[ ! -d "$CINEBUTLER_DIR" ]]; then
    log "错误: CINEBUTLER_DIR 不存在: $CINEBUTLER_DIR"
    exit 0
fi

cd "$CINEBUTLER_DIR" || { log "错误: 无法进入目录 $CINEBUTLER_DIR"; exit 0; }

# 从 .env 加载代理等环境变量（Transmission daemon 不继承用户 shell 的代理设置）
if [[ -f ".env" ]]; then
    set -a
    # shellcheck disable=SC1091
    source <(grep -v '^\s*#' .env | grep -v '^\s*$' | grep -v "^LLM_PROVIDERS")
    set +a
    log "已加载 .env (HTTP_PROXY=${HTTP_PROXY:-未设置}, HTTPS_PROXY=${HTTPS_PROXY:-未设置})"
fi

# 补充用户工具路径（daemon 不继承用户 shell 的 PATH）
export PATH="/home/tth/src/anaconda3/bin:/home/tth/.local/bin:$PATH"

log "开始执行 cinebutler..."
uv run cinebutler >> "$LOG_FILE" 2>&1
EXIT_CODE=$?
log "cinebutler 退出码: $EXIT_CODE"
log "===== Hook 结束 ====="
exit $EXIT_CODE
