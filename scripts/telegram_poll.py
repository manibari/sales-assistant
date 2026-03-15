"""Telegram polling bridge — forwards updates to local FastAPI webhook.

Usage: python scripts/telegram_poll.py

For local development only. In production, use webhook mode.
"""

import asyncio
import logging
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import httpx
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
log = logging.getLogger("tg-poll")

TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
SECRET = os.environ.get("TELEGRAM_WEBHOOK_SECRET", "")
LOCAL_WEBHOOK = os.environ.get("TELEGRAM_LOCAL_WEBHOOK", "http://localhost:8002/api/nx/telegram/webhook")
TG_API = f"https://api.telegram.org/bot{TOKEN}"


async def poll():
    # Remove any existing webhook so getUpdates works
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.post(f"{TG_API}/deleteWebhook")
        log.info("deleteWebhook: %s", r.json().get("description", r.text))

    offset = 0
    log.info("Polling started — forwarding to %s", LOCAL_WEBHOOK)
    log.info("Send a message to @Manibari_Adjutant_bot to test")

    async with httpx.AsyncClient(timeout=60) as client:
        while True:
            try:
                r = await client.get(
                    f"{TG_API}/getUpdates",
                    params={"offset": offset, "timeout": 30},
                    timeout=40,
                )
                data = r.json()
                if not data.get("ok"):
                    log.error("getUpdates failed: %s", data)
                    await asyncio.sleep(5)
                    continue

                for update in data.get("result", []):
                    offset = update["update_id"] + 1
                    # Log incoming message
                    msg = update.get("message", {})
                    chat = msg.get("chat", {})
                    text = msg.get("text", "")
                    photo = msg.get("photo")
                    log.info(
                        "← [%s] %s%s",
                        chat.get("first_name", chat.get("id")),
                        text[:80] if text else "",
                        " [photo]" if photo else "",
                    )

                    # Forward to local webhook
                    try:
                        headers = {}
                        if SECRET:
                            headers["X-Telegram-Bot-Api-Secret-Token"] = SECRET
                        resp = await client.post(
                            LOCAL_WEBHOOK,
                            json=update,
                            headers=headers,
                            timeout=30,
                        )
                        log.info("→ webhook %s", resp.status_code)
                    except Exception as e:
                        log.error("→ webhook error: %s", e)

            except httpx.ReadTimeout:
                continue
            except KeyboardInterrupt:
                break
            except Exception as e:
                log.error("Poll error: %s", e)
                await asyncio.sleep(5)


if __name__ == "__main__":
    try:
        asyncio.run(poll())
    except KeyboardInterrupt:
        log.info("Stopped.")
