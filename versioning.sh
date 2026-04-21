#!/bin/bash

# ==========================================
# Quizio Version Bump Script
# Usage: ./versioning.sh <new_version>
# Example: ./versioning.sh 1.0.0
# ==========================================

NEW_VERSION=$1

# Check if version argument is provided
if [ -z "$NEW_VERSION" ]; then
    echo "❌ 錯誤: 請指定一個版本號 (例如: ./versioning.sh 1.0.0)"
    exit 1
fi

echo "🚀 準備將所有專案版本號升級至: $NEW_VERSION"

# Update frontend and electron projects using npm
update_npm_version() {
    DIR=$1
    echo "📦 更新 $DIR..."
    (cd "$DIR" && npm version "$NEW_VERSION" --no-git-tag-version --allow-same-version)
}

update_npm_version "quizio-data/frontend"
update_npm_version "quizio-game/frontend"
update_npm_version "quizio-game/electron"

# Update Python backend projects using sed
update_python_version() {
    FILE=$1
    echo "🐍 更新 $FILE..."
    # Handle sed syntax differences between macOS (darwin) and Linux
    if [[ "$OSTYPE" == "darwin"* ]]; then
        sed -i '' -E "s/version='[^']+'/version='$NEW_VERSION'/g" "$FILE"
    else
        sed -i -E "s/version='[^']+'/version='$NEW_VERSION'/g" "$FILE"
    fi
}

update_python_version "quizio-data/backend/main.py"
update_python_version "quizio-game/backend/main.py"

echo "=========================================="
echo "✅ 版號更新完成！請使用 git diff 確認修改內容。"
echo "接下來您可以執行以下指令來觸發 GitHub Actions 發布流程:"
echo "  git add ."
echo "  git commit -m \"chore: bump version to v$NEW_VERSION\""
echo "  git tag v$NEW_VERSION"
echo "  git push origin release --tags"
