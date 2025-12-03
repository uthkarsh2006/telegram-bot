import os
import json
from datetime import datetime, timedelta
from fastapi import FastAPI, Request
from telegram import Bot, Update
import asyncio

# ---------------------- TELEGRAM BOT CONFIG ----------------------
BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"
bot = Bot(BOT_TOKEN)

INITIAL_USER_ID = 1661449752  # Your Telegram ID
USERS_FILE = "users.json"

app = FastAPI()

# ---------------------- USER SYSTEM ----------------------

def save_user(chat_id: int):
    """Save chat ID to users.json"""
    if not os.path.exists(USERS_FILE):
        with open(USERS_FILE, "w") as f:
            json.dump([], f)

    with open(USERS_FILE, "r") as f:
        users = json.load(f)

    if chat_id not in users:
        users.append(chat_id)
        with open(USERS_FILE, "w") as f:
            json.dump(users, f)
        print(f"✓ New user saved: {chat_id}")

def get_all_users():
    """Return all saved users"""
    if not os.path.exists(USERS_FILE):
        return []
    with open(USERS_FILE, "r") as f:
        return json.load(f)

# ---------------------- CONTEST SYSTEM ----------------------

def get_today_contests():
    """Read contests.json and filter today's contests"""
    try:
        with open("contests.json", "r", encoding="utf-8") as f:
            contests = json.load(f)
    except:
        return []

    today = datetime.now().strftime("%d-%m-%Y")
    today_contests = [c for c in contests if c.get("date", "").strip() == today]
    return today_contests

def format_contest_message(contests):
    """Format contests into Telegram message"""
    if not contests:
        return "📅 <b>No contests today!</b>\nEnjoy your free time! 😊"
    
    message = f"🎯 <b>Today's Contests ({len(contests)})</b>\n"
    message += "=" * 30 + "\n\n"
    
    for i, contest in enumerate(contests, 1):
        message += f"<b>{i}. {contest['contest']}</b>\n"
        message += f"🕐 {contest['start_time']} - {contest['end_time']}\n"
        message += f"📱 Platform: {contest['platform']}\n"
        if contest.get('url'):
            message += f"🔗 <a href='{contest['url']}'>Link</a>\n"
        message += "\n"
    message += "Good luck! 🚀"
    return message

# ---------------------- MESSAGE SENDER ----------------------

async def send_message(chat_id, text):
    try:
        await bot.send_message(chat_id=chat_id, text=text, parse_mode="HTML")
    except Exception as e:
        print(f"❌ Failed to send message to {chat_id}: {e}")

async def send_to_all(text):
    users = get_all_users()
    if not users:
        print("⚠ No users subscribed.")
        return
    for chat_id in users:
        await send_message(chat_id, text)
        print(f"✓ Message sent to {chat_id}")

# ---------------------- REMINDERS ----------------------

async def send_reminder(contest):
    message = f"⏰ <b>Reminder:</b> {contest['contest']} starts in 15 minutes!\n"
    message += f"🕐 {contest['start_time']} - {contest['end_time']}\n"
    message += f"📱 Platform: {contest['platform']}\n"
    if contest.get("url"):
        message += f"🔗 <a href='{contest['url']}'>Link</a>"
    await send_to_all(message)

def schedule_reminders():
    """Schedule contest reminders 15 minutes before start"""
    contests = get_today_contests()
    now = datetime.now()
    for contest in contests:
        start_time_str = contest.get("start_time")
        if not start_time_str:
            continue
        try:
            start_time = datetime.strptime(start_time_str, "%H:%M")
            start_time = start_time.replace(year=now.year, month=now.month, day=now.day)
        except:
            continue

        reminder_time = start_time - timedelta(minutes=15)
        delta_seconds = (reminder_time - now).total_seconds()
        if delta_seconds > 0:
            asyncio.get_event_loop().call_later(delta_seconds, lambda c=contest: asyncio.create_task(send_reminder(c)))
            print(f"⏰ Scheduled reminder for {contest['contest']} at {reminder_time.strftime('%H:%M')}")

# ---------------------- WEBHOOK ----------------------

@app.post(f"/{BOT_TOKEN}")
async def webhook(req: Request):
    """Handle incoming Telegram updates"""
    data = await req.json()
    update = Update.de_json(data, bot)

    chat_id = update.message.chat.id if update.message else None
    text = update.message.text if update.message else None

    if text == "/start" and chat_id:
        save_user(chat_id)
        await send_message(chat_id, "You are now subscribed! 🎉\nYou will receive daily contest updates.")
        today_contests = get_today_contests()
        await send_message(chat_id, format_contest_message(today_contests))

    return {"ok": True}

@app.get("/")
async def index():
    return {"status": "Bot is running!"}

# ---------------------- AUTO DAILY BROADCAST ----------------------

async def broadcast_daily_contests():
    today_contests = get_today_contests()
    message = format_contest_message(today_contests)
    await send_to_all(message)
    schedule_reminders()

# Run initial broadcast and reminders on startup
@app.on_event("startup")
async def startup_event():
    print("Bot started...")
    await broadcast_daily_contests()
