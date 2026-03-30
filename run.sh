#!/bin/bash

# 取得第一個參數作為主要動作 (up 或 down)
ACTION=$1

# 取得第二個參數 (例如 --build)
EXTRA_ARG=$2

# 如果沒有輸入參數，顯示使用說明並離開
if [ -z "$ACTION" ]; then
    echo "使用方式: ./run.sh [up|down] [--build]"
    echo "  up      : 依序啟動 quizio-data 與 quizio-game"
    echo "  down    : 依序關閉 quizio-game 與 quizio-data"
    echo "  --build : (選用) 在啟動前強制重新建置 Docker 映像檔"
    exit 1
fi

if [ "$ACTION" == "down" ]; then
    echo "🛑 準備關閉所有服務..."
    
    # 關閉時建議先關閉前端/遊戲引擎，再關閉資料庫
    echo "🎮 [1/2] Stopping quizio-game (Game Engine)..."
    cd quizio-game || exit
    docker compose --env-file dev.env down
    cd ..

    echo "📦 [2/2] Stopping quizio-data (Data Service)..."
    cd quizio-data || exit
    docker compose --env-file dev.env down
    cd ..

    echo "✅ 所有服務已成功關閉！"

elif [ "$ACTION" == "up" ]; then
    echo "🚀 準備啟動所有服務..."

    # 1. 啟動 quizio-data (將 EXTRA_ARG 也就是 --build 傳遞進去)
    echo "📦 [1/4] Starting quizio-data (Data Service)..."
    cd quizio-data || exit
    docker compose --env-file dev.env up -d $EXTRA_ARG
    cd ..

    # 2. 等待 Data Service 啟動
    echo "⏳ [2/4] Waiting for quizio-data API to be ready..."
    until curl -s -f -o /dev/null "http://localhost:8080/docs"; do
        printf "."
        sleep 2
    done
    echo -e "\n✅ quizio-data API is fully online!"

    # 3. 啟動 quizio-game
    echo "🎮 [3/4] Starting quizio-game (Game Engine)..."
    cd quizio-game || exit
    docker compose --env-file dev.env up -d $EXTRA_ARG

    # 4. 等待 Cloudflare Tunnel 取得網址
    echo "🌐 [4/4] Waiting for Cloudflare Tunnel URL..."
    CF_URL=""
    ATTEMPTS=0
    MAX_ATTEMPTS=15

    while [ -z "$CF_URL" ] && [ $ATTEMPTS -lt $MAX_ATTEMPTS ]; do
        sleep 2
        # 使用 2>&1 確保 stderr 的輸出也能被 grep 捕捉到
        CF_URL=$(docker compose --env-file dev.env logs cloudflared 2>&1 | grep -Eo 'https://[a-zA-Z0-9-]+\.trycloudflare\.com' | tail -n 1)
        ATTEMPTS=$((ATTEMPTS+1))
    done

    cd ..

    # 5. 印出結果
    echo ""
    echo "========================================================"
    if [ -n "$CF_URL" ]; then
        echo "🎉 All services started successfully!"
        echo "👉 Admin Dashboard (Local): http://localhost:5174"
        echo "👉 Student Game Lobby (Public): $CF_URL"
        echo "👉 Teacher Host (Public): $CF_URL/host"
    else
        echo "⚠️ Services started, but couldn't fetch Cloudflare URL."
        echo "Please check logs manually: cd quizio-game && docker compose --env-file dev.env logs cloudflared"
    fi
    echo "========================================================"

else
    echo "❌ 錯誤：無法識別的指令 '$ACTION'"
    echo "請使用 './run.sh up' 或 './run.sh down'"
    exit 1
fi