#!/usr/bin/env bash
# CineButler 一键发布到 GitHub
# 用法: ./publish-to-github.sh [repo名称，默认 CineButler]

set -e
REPO_NAME="${1:-CineButler}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=== CineButler 发布到 GitHub ==="

# 1. 初始化 git（如未初始化）
if [[ ! -d .git ]]; then
  git init
  echo "已初始化 Git 仓库"
fi

# 2. 确保 .gitignore 存在
if [[ ! -f .gitignore ]]; then
  echo "错误: 缺少 .gitignore，请先创建"
  exit 1
fi

# 3. 使用 main 分支
git branch -M main 2>/dev/null || true

# 4. 添加所有文件并提交
git add .
if git diff --cached --quiet 2>/dev/null; then
  echo "工作区干净，无新改动"
else
  git commit -m "chore: initial commit - CineButler media workflow"
  echo "已创建初始提交"
fi

# 5. 推送到 GitHub
if command -v gh &>/dev/null; then
  # 使用 GitHub CLI 创建仓库并推送
  echo "使用 gh 创建仓库: $REPO_NAME"
  gh repo create "$REPO_NAME" --private --source=. --push --description "LangGraph workflow for organizing media files from Transmission with TMDB"
  echo ""
  echo "✅ 已成功发布到 GitHub!"
  gh repo view --web 2>/dev/null || true
else
  echo ""
  echo "未安装 GitHub CLI (gh)，请按以下步骤手动完成："
  echo ""
  echo "1. 在浏览器打开 https://github.com/new"
  echo "2. 新建仓库名称: $REPO_NAME"
  echo "3. 选择 Private，不要勾选 README（本地已有）"
  echo "4. 创建后执行："
  echo ""
  echo "   git remote add origin git@github.com:$(git config user.name)/${REPO_NAME}.git"
  echo "   git branch -M main"
  echo "   git push -u origin main"
  echo ""
  echo "或安装 gh 后重试："
  echo "   sudo apt install gh   # Debian/Ubuntu"
  echo "   gh auth login"
  echo "   ./publish-to-github.sh"
fi
