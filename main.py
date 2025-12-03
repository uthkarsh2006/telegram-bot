import os
import json
from fastapi import FastAPI, Request
from telegram import Bot, Update
from telegram.ext import Application, CommandHandler, ContextTypes

# ---------------- TELEGRAM CONFIG ----------------
BOT_TOKEN = "8509447063:AAELdnx56rIYaMxk3PKLEBafRqPQlzkMqZg"
bot = Bot(BOT_TOKEN)
app = FastAPI()

# Initialize Telegram Application
application = Application.builder().token(BOT_TOKEN).build()

# ---------------- USER SYSTEM ----------------
USERS_FILE = "users.json"

def save_user(chat_id: int):
    """Save a chat ID to users.json"""
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

# ---------------- CONTEST SYSTEM ----------------
def get_today_contests():
    try:
        with open("contests.json", "r", encoding="utf-8") as f:
            contests = json.load(f)
        return contests
    except:
        return []

def format_contest_message(contests):
    if not contests:
        return "📅 <b>No contests today!</b> Enjoy your free time! 😊"

    message = f"🎯 <b>Today's Contests ({len(contests)})</b>\n"
    message += "=" * 30 + "\n\n"
    for i, contest in enumerate(contests, 1):
        message += f"<b>{i}. {contest['contest']}</b>\n"
        message += f"   🕐 Time: {contest['start_time']} - {contest['end_time']}\n"
        message += f"   📱 Platform: {contest['platform']}\n"
        if contest.get("url"):
            message += f"   🔗 <a href='{contest['url']}'>Link</a>\n"
        message += "\n"
    message += "Good luck! 🚀"
    return message

# ---------------- TELEGRAM COMMAND ----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    save_user(chat_id)
    await context.bot.send_message(chat_id=chat_id, text="You are now subscribed! 🎉")
    contests = get_today_contests()
    await context.bot.send_message(chat_id=chat_id, text=format_contest_message(contests), parse_mode="HTML")

application.add_handler(CommandHandler("start", start))

# ---------------- WEBHOOK ----------------
@app.post(f"/{BOT_TOKEN}")
async def webhook(req: Request):
    data = await req.json()
    update = Update.de_json(data, bot)
    await application.process_update(update)
    return {"ok": True}

# ---------------- ROOT ----------------
@app.get("/")
async def index():
    return {"status": "Bot is running!"}
