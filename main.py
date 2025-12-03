import os
import threading
import schedule
import time
from fastapi import FastAPI, Request
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import asyncio
import requests

# ---------------- Environment Variable ---------------- #
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("Error: BOT_TOKEN is not set! Add it in Render Environment Variables.")

# ---------------- FastAPI App ---------------- #
app = FastAPI()

# ---------------- Telegram Bot Handlers ---------------- #
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Hello! I am your contest bot 🤖. I will notify you about upcoming contests."
    )

# ---------------- Scheduled Task ---------------- #
def daily_job():
    print("Daily job running...")
    # Example: send message to a specific chat
    # url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    # data = {"chat_id": "CHAT_ID", "text": "Daily contest update!"}
    # requests.post(url, data=data)

def run_schedule():
    schedule.every().day.at("08:00").do(daily_job)
    while True:
        schedule.run_pending()
        time.sleep(1)

threading.Thread(target=run_schedule, daemon=True).start()

# ---------------- Telegram Bot Setup ---------------- #
application = ApplicationBuilder().token(BOT_TOKEN).build()
application.add_handler(CommandHandler("start", start))

# ---------------- Webhook Endpoint for Render ---------------- #
@app.post(f"/{BOT_TOKEN}")
async def telegram_webhook(req: Request):
    data = await req.json()
    update = Update.de_json(data, application.bot)
    await application.update_queue.put(update)
    return {"ok": True}

# ---------------- Root Endpoint ---------------- #
@app.get("/")
def read_root():
    return {"message": "Bot is running!"}

# ---------------- Start the Bot ---------------- #
async def start_bot():
    await application.initialize()
    await application.start()
    print("Bot started successfully!")

# Create asyncio task to run bot
loop = asyncio.get_event_loop()
loop.create_task(start_bot())
