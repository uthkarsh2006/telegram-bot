import os
import threading
import asyncio
import schedule
import time
import requests
from fastapi import FastAPI, Request
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# Bot token from environment variable for security
BOT_TOKEN = os.getenv("BOT_TOKEN")  # set this in Render's Environment Variables

# FastAPI app
app = FastAPI()

# Telegram Bot Handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hello! I am your contest bot 🤖. I will notify you about upcoming contests.")

# Example daily job
def daily_job():
    # This is where you can fetch contest data and send messages
    print("Daily job running...")
    # Example: Send message to your chat (replace CHAT_ID)
    # url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    # data = {"chat_id": "YOUR_CHAT_ID", "text": "Daily contest update!"}
    # requests.post(url, data=data)

def run_schedule():
    schedule.every().day.at("08:00").do(daily_job)  # run daily at 8 AM
    while True:
        schedule.run_pending()
        time.sleep(1)

# Start schedule in a separate thread
threading.Thread(target=run_schedule, daemon=True).start()

# Build the Telegram bot application
application = (
    ApplicationBuilder()
    .token(BOT_TOKEN)
    .build()
)
application.add_handler(CommandHandler("start", start))

# Webhook endpoint for Render
@app.post(f"/{BOT_TOKEN}")
async def telegram_webhook(req: Request):
    data = await req.json()
    update = Update.de_json(data, application.bot)
    await application.update_queue.put(update)
    return {"ok": True}

# Root endpoint
@app.get("/")
def read_root():
    return {"message": "Bot is running!"}

# Run the bot asynchronously
async def main():
    await application.initialize()
    await application.start()
    await application.updater.start_polling()
    print("Bot started successfully!")
    await application.updater.idle()

# Start the bot when running on Render
loop = asyncio.get_event_loop()
loop.create_task(main())
