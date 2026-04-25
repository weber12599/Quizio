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
echo "--------------------------------------------------------"

# ==========================================
# 嚴格環境變數與指令解析
# ==========================================
ENV=$1
ACTION=$2
EXTRA_ARG=$3

# 顯示使用說明 (若缺少必填參數)
if [ -z "$ENV" ] || [ -z "$ACTION" ]; then
    echo "使用方式: ./run.sh <環境> <指令> [參數]"
    echo ""
    echo "環境選項 (必填):"
    echo "  dev           : 使用開發環境 (強制讀取 docker-compose.dev.yml 與 dev.env)"
    echo "  prod          : 使用正式環境 (強制讀取 docker-compose.yml 與 .env)"
    echo ""
    echo "指令選項 (必填):"
    echo "  up            : 依序啟動所有服務"
    echo "  down          : 依序關閉所有服務"
    echo "  build         : 重新構建所有服務的映像檔"
    echo "  makemigration : 產生 Alembic 資料庫遷移腳本 (如: ./run.sh dev makemigration \"init\")"
    echo "  migrate       : 執行資料庫遷移，更新到最新版"
    echo "  history       : 顯示 Alembic 資料庫遷移歷史紀錄"
    echo "  downgrade     : 降級資料庫狀態 (預設為 -1，或指定: ./run.sh dev downgrade -2)"
    exit 1
fi

# 驗證環境參數是否合法
if [ "$ENV" != "dev" ] && [ "$ENV" != "prod" ]; then
    echo "❌ 錯誤：環境參數必須是 'dev' 或 'prod'"
    exit 1
fi

# 根據環境設定對應的檔案
if [ "$ENV" == "dev" ]; then
    echo "🔧 ENV: Development"
    COMPOSE_FILE="docker-compose.dev.yml"
    ENV_FILE=".env.dev"
else
    echo "🌍 ENV: Production"
    COMPOSE_FILE="docker-compose.yml"
    ENV_FILE=".env"
fi
echo "--------------------------------------------------------"

# 定義嚴格執行 docker compose 的函數
execute_docker() {
    # 嚴格檢查設定檔是否存在
    if [ ! -f "$COMPOSE_FILE" ]; then
        echo "❌ 致命錯誤：在目錄 $(pwd) 找不到指定的設定檔 '$COMPOSE_FILE'！"
        echo "👉 由於採用嚴格模式，請確保你已經手動建立了該檔案。"
        exit 1
    fi

    # 嚴格檢查環境變數檔是否存在
    if [ ! -f "$ENV_FILE" ]; then
        echo "❌ 致命錯誤：在目錄 $(pwd) 找不到指定的環境變數檔 '$ENV_FILE'！"
        echo "👉 請確保你已經建立了該環境變數檔案。"
        exit 1
    fi

    # 檔案都存在才執行
    docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" "$@"
}

# ==========================================
# 執行 Action
# ==========================================

if [ "$ACTION" == "down" ]; then
    echo "🛑 準備關閉所有服務..."
    
    echo "🎮 [1/2] Stopping quizio-game (Game Engine)..."
    cd quizio-game || exit
    execute_docker down -v
    cd ..

    echo "📦 [2/2] Stopping quizio-data (Data Service)..."
    cd quizio-data || exit
    execute_docker down -v
    cd ..

    echo "✅ 所有服務已成功關閉！"

elif [ "$ACTION" == "up" ]; then
    echo "🚀 準備啟動所有服務..."

    echo "📦 [1/4] Starting quizio-data (Data Service)..."
    cd quizio-data || exit
    execute_docker up -d $EXTRA_ARG
    cd ..

    echo "⏳ [2/4] Waiting for quizio-data API to be ready..."
    until curl -s -f -o /dev/null "http://localhost:18080/docs"; do
        printf "."
        sleep 2
    done
    echo -e "\n✅ quizio-data API is fully online!"

    echo "🎮 [3/4] Starting quizio-game (Game Engine)..."
    cd quizio-game || exit
    execute_docker up -d $EXTRA_ARG

    echo "🌐 [4/4] Waiting for Cloudflare Tunnel URL..."
    CF_URL=""
    ATTEMPTS=0
    MAX_ATTEMPTS=15

    while [ -z "$CF_URL" ] && [ $ATTEMPTS -lt $MAX_ATTEMPTS ]; do
        sleep 2
        CF_URL=$(execute_docker logs cloudflared 2>&1 | grep -Eo 'https://[a-zA-Z0-9-]+\.trycloudflare\.com' | tail -n 1)
        ATTEMPTS=$((ATTEMPTS+1))
    done

    cd ..

    echo ""
    echo "========================================================"
    if [ -n "$CF_URL" ]; then
        echo "🎉 All services started successfully ($ENV Mode)!"
        echo "👉 Admin Dashboard (Local): http://localhost:5174"
        echo "👉 Student Game Lobby (Public): $CF_URL"
        echo "👉 Teacher Host (Public): $CF_URL/host"
    else
        echo "⚠️ Services started, but couldn't fetch Cloudflare URL."
    fi
    echo "========================================================"

elif [ "$ACTION" == "build" ]; then
    echo "🛠️ 正在重新構建映像檔 ($ENV Mode)..."
    
    echo "📦 [1/2] Building quizio-data..."
    cd quizio-data || exit
    execute_docker build $EXTRA_ARG
    cd ..

    echo "🎮 [2/2] Building quizio-game..."
    cd quizio-game || exit
    execute_docker build $EXTRA_ARG
    cd ..

    echo "✅ 所有映像檔已構建完成！"

elif [ "$ACTION" == "makemigration" ]; then
    if [ -z "$EXTRA_ARG" ]; then
        echo "❌ 錯誤：請提供遷移訊息！"
        echo "範例: ./run.sh dev makemigration \"add_hint_to_questions\""
        exit 1
    fi
    echo "📝 正在產生 Alembic 遷移腳本 ($EXTRA_ARG)..."
    cd quizio-data || exit
    execute_docker exec backend alembic revision --autogenerate -m "$EXTRA_ARG"
    cd ..
    echo "✅ 產生完畢！請檢查 quizio-data/backend/alembic/versions/ 裡的檔案。"

elif [ "$ACTION" == "migrate" ]; then
    echo "🚀 正在套用資料庫變更 (Upgrade Head)..."
    cd quizio-data || exit
    execute_docker exec backend alembic upgrade head
    cd ..
    echo "✅ 資料庫更新完畢！"

elif [ "$ACTION" == "history" ]; then
    echo "📜 Showing Alembic migration history..."
    cd quizio-data || exit
    execute_docker exec backend alembic history
    cd ..

elif [ "$ACTION" == "downgrade" ]; then
    # Set default revision to -1 if no extra argument is provided
    REVISION=${EXTRA_ARG:--1}
    echo "⏪ Downgrading database to revision: $REVISION"
    cd quizio-data || exit
    execute_docker exec backend alembic downgrade "$REVISION"
    cd ..
    echo "✅ 資料庫降級完畢！"

else
    echo "❌ 錯誤：無法識別的指令 '$ACTION'"
    echo "請直接輸入 ./run.sh 來查看可用指令"
    exit 1
fi