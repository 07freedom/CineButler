#!/bin/bash
#
# CineButler Transmission hook: 下载完成后整理媒体文件
# 将本脚本复制到 transmission-hook/hooks.d/ 或把 CineButler/hooks 加入 HOOK_DIRS
#
# 依赖: TR_TORRENT_NAME, TR_TORRENT_DIR, TR_TORRENT_BYTES_DOWNLOADED (由 Transmission 设置)
#

CINEBUTLER_DIR="/home/tth/src/CineButler"
[[ -d "$CINEBUTLER_DIR" ]] || exit 0

cd "$CINEBUTLER_DIR" || exit 0
exec uv run cinebutler
