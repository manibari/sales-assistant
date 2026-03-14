Generate deployment instructions for setting up a new machine or updating the deployment server.

Steps:

1. Read `.env` to get the current `DATABASE_URL` (mask the password in output).
2. Read `AGENTS.md` Network Config for port info.
3. Check current git branch and latest commit hash.

4. Output a ready-to-paste block:

```
# === Sales Assistant 部署指南 ===

# 1. 拉最新程式碼
cd ~/path/to/sales-assistant
git pull origin main

# 2. 安裝依賴
pip install psycopg2-binary python-dotenv
cd frontend && npm install && cd ..

# 3. 設定 .env（加入以下內容）
DATABASE_URL=postgresql://postgres:****@db.nmccywkhrvlevryqusvs.supabase.co:5432/postgres

# 4. 啟動 backend（port 8001）
set -a && source .env && set +a
uvicorn backend.main:app --host 0.0.0.0 --port 8001 &

# 5. 啟動 frontend（port 3000）
cd frontend && npm run dev &

# 6. 驗證
curl -s http://localhost:8001/api/nx/clients/ | head -5
```

5. Also output the full (unmasked) DATABASE_URL separately so the user can copy it.
6. Remind about Telegram webhook: if this is the production server (`api.phyra.uk`), the webhook should point to `https://api.phyra.uk/api/nx/telegram/webhook`.
