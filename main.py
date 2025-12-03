import os
import threading
import schedule
import time
from fastapi import FastAPI, Request
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import asyncio
import requests

# Bot token from environment variable
BOT_TOKEN = os.getenv("BOT_TOKEN")  # Make sure this is set in Render Environment Variables

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN environment variable is not set!")

# FastAPI app
app = FastAPI()

# ---------------- Telegram Bot Handlers ---------------- #
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for /start command"""
    await update.message.reply_text(
        "Hello! I am your contest bot 🤖. I will notify you about upcoming contests."
    )

# ---------------- Scheduled Task ---------------- #
def daily_job():
    """Daily task to send updates"""
    print("Daily job running...")
    # Example: send a message to a specific chat
    # Replace CHAT_ID with your Telegram chat id
    # url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    # data = {"chat_id": "CHAT_ID", "text": "Daily contest update!"}
    # requests.post(url, data=data)

def run_schedule():
    """Run scheduled jobs in a separate thread"""
    schedule.every().day.at("08:00").do(daily_job)  # Runs daily at 08:00
    while True:
        schedule.run_pending()  # Checks if any scheduled job needs to run
        time.sleep(1)

# Start scheduler in a background thread
threading.Thread(target=run_schedule, daemon=True).start()

# ---------------- Telegram Bot Setup ---------------- #
application = ApplicationBuilder().token(BOT_TOKEN).build()
application.add_handler(CommandHandler("start", start))

# ---------------- Webhook Endpoint for Render ---------------- #
@app.post(f"/{BOT_TOKEN}")
async def telegram_webhook(req: Request):
    """Receives updates from Telegram via webhook"""
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
    """Initialize and start the Telegram bot asynchronously"""
    await application.initialize()
    await application.start()
    print("Bot started successfully!")

# Run the bot asynchronously on Render
loop = asyncio.get_event_loop()
loop.create_task(start_bot())
