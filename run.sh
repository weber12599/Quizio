#!/bin/bash

# Detect Operating System
OS_TYPE="$(uname)"

if [ "$OS_TYPE" == "Darwin" ]; then
    # macOS: Open Docker Desktop if not running
    if ! docker info > /dev/null 2>&1; then
        echo "Detected macOS. Starting Docker Desktop..."
        open -g -a Docker
    else
        echo "Docker is already running on macOS."
    fi

elif [ "$OS_TYPE" == "Linux" ]; then
    # Linux: Use systemctl to start Docker service
    if ! docker info > /dev/null 2>&1; then
        echo "Detected Linux. Starting Docker service..."
        # Start Docker Engine (Standard)
        sudo systemctl start docker
    else
        echo "Docker is already running on Linux."
    fi

else
    echo "Unsupported OS: $OS_TYPE"
    exit 1
fi

# Optional: Wait until Docker daemon is fully ready
echo "Checking Docker status..."
COUNT=0
until docker info > /dev/null 2>&1; do
    echo "Waiting for Docker daemon to be ready... ($((++COUNT))s)"
    sleep 1
    if [ $COUNT -gt 30 ]; then
        echo "Docker failed to start within 30 seconds."
        exit 1
    fi
done

echo "Docker is up and running!"

DOCKER_CMD="docker compose --env-file dev.env"

# 取得第一個參數作為主要動作 (up, down, makemigration, migrate)
ACTION=$1

# 取得第二個參數 (例如 --build 或是 遷移的訊息)
EXTRA_ARG=$2

# 如果沒有輸入參數，顯示使用說明並離開
if [ -z "$ACTION" ]; then
    echo "使用方式: ./run.sh [指令] [參數]"
    echo "  up            : 依序啟動 quizio-data 與 quizio-game"
    echo "  down          : 依序關閉所有服務"
    echo "  makemigration : 產生 Alembic 資料庫遷移腳本 (需加上訊息，如: ./run.sh makemigration \"init\")"
    echo "  migrate       : 執行資料庫遷移，更新到最新版"
    exit 1
fi

if [ "$ACTION" == "down" ]; then
    echo "🛑 準備關閉所有服務..."
    
    echo "🎮 [1/2] Stopping quizio-game (Game Engine)..."
    cd quizio-game || exit
    $DOCKER_CMD down
    cd ..

    echo "📦 [2/2] Stopping quizio-data (Data Service)..."
    cd quizio-data || exit
    $DOCKER_CMD down
    cd ..

    echo "✅ 所有服務已成功關閉！"

elif [ "$ACTION" == "up" ]; then
    echo "🚀 準備啟動所有服務..."

    echo "📦 [1/4] Starting quizio-data (Data Service)..."
    cd quizio-data || exit
    $DOCKER_CMD up -d $EXTRA_ARG
    cd ..

    echo "⏳ [2/4] Waiting for quizio-data API to be ready..."
    until curl -s -f -o /dev/null "http://localhost:8080/docs"; do
        printf "."
        sleep 2
    done
    echo -e "\n✅ quizio-data API is fully online!"

    echo "🎮 [3/4] Starting quizio-game (Game Engine)..."
    cd quizio-game || exit
    $DOCKER_CMD up -d $EXTRA_ARG

    echo "🌐 [4/4] Waiting for Cloudflare Tunnel URL..."
    CF_URL=""
    ATTEMPTS=0
    MAX_ATTEMPTS=15

    while [ -z "$CF_URL" ] && [ $ATTEMPTS -lt $MAX_ATTEMPTS ]; do
        sleep 2
        CF_URL=$($DOCKER_CMD logs cloudflared 2>&1 | grep -Eo 'https://[a-zA-Z0-9-]+\.trycloudflare\.com' | tail -n 1)
        ATTEMPTS=$((ATTEMPTS+1))
    done

    cd ..

    echo ""
    echo "========================================================"
    if [ -n "$CF_URL" ]; then
        echo "🎉 All services started successfully!"
        echo "👉 Admin Dashboard (Local): http://localhost:5174"
        echo "👉 Student Game Lobby (Public): $CF_URL"
        echo "👉 Teacher Host (Public): $CF_URL/host"
    else
        echo "⚠️ Services started, but couldn't fetch Cloudflare URL."
    fi
    echo "========================================================"

elif [ "$ACTION" == "makemigration" ]; then
    if [ -z "$EXTRA_ARG" ]; then
        echo "❌ 錯誤：請提供遷移訊息！"
        echo "範例: ./run.sh makemigration \"add_hint_to_questions\""
        exit 1
    fi
    echo "📝 正在產生 Alembic 遷移腳本 ($EXTRA_ARG)..."
    cd quizio-data || exit
    $DOCKER_CMD exec backend alembic revision --autogenerate -m "$EXTRA_ARG"
    cd ..
    echo "✅ 產生完畢！請檢查 quizio-data/backend/alembic/versions/ 裡的檔案。"

elif [ "$ACTION" == "migrate" ]; then
    echo "🚀 正在套用資料庫變更 (Upgrade Head)..."
    cd quizio-data || exit
    $DOCKER_CMD exec backend alembic upgrade head
    cd ..
    echo "✅ 資料庫更新完畢！"

else
    echo "❌ 錯誤：無法識別的指令 '$ACTION'"
    echo "請直接輸入 ./run.sh 來查看可用指令"
    exit 1
fi