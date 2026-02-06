#!/bin/bash
# Render 部署測試腳本

# 替換成你的實際 Render URL
RENDER_URL="https://your-app-name.onrender.com"

echo "======================================"
echo "Render 部署測試腳本"
echo "======================================"
echo ""

# 測試 1: 健康檢查
echo "🔍 測試 1: 健康檢查"
echo "執行: curl $RENDER_URL/health"
curl -s $RENDER_URL/health | jq '.'
echo ""
echo ""

# 測試 2: 根路徑
echo "🔍 測試 2: 根路徑"
echo "執行: curl $RENDER_URL/"
curl -s $RENDER_URL/ | jq '.'
echo ""
echo ""

# 測試 3: 觸發工作流
echo "🔍 測試 3: 觸發 Email Summary 工作流"
echo "執行: curl -X POST $RENDER_URL/webhook/email-summary"
curl -s -X POST $RENDER_URL/webhook/email-summary | jq '.'
echo ""
echo ""

echo "======================================"
echo "✅ 測試完成！"
echo "======================================"
echo ""
echo "接下來："
echo "1. 查看 Slack 頻道是否收到郵件摘要"
echo "2. 前往 Render Dashboard → Logs 查看執行詳情"
echo "3. 如果有檢測到事件，測試 Slack 按鈕互動"
echo ""
