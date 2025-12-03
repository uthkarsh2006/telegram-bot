import os
import json
import requests
from datetime import datetime, timedelta
import time
import threading
import schedule

from fastapi import FastAPI, Request
from telegram import Update
from telegram.ext import Application, ContextTypes

# ---------------------- TELEGRAM BOT CONFIG ----------------------
BOT_TOKEN = "8509447063:AAELdnx56rIYaMxk3PKLEBafRqPQlzkMqZg"
API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

# Your Telegram ID (creator/admin)
INITIAL_USER_ID = 1661449752

# ---------------------- FASTAPI APP ----------------------
app = FastAPI()
application = Application.builder().token(BOT_TOKEN).build()

@app.post(f"/{BOT_TOKEN}")
async def telegram_webhook(req: Request):
    """Receive updates from Telegram via webhook"""
    data = await req.json()
    update = Update.de_json(data, application.bot)
    await application.update_queue.put(update)
    return {"ok": True}

# ---------------------- USER SYSTEM ----------------------
def save_user(chat_id):
    """Save a chat ID to users.json if not already present"""
    try:
        if not os.path.exists("users.json"):
            with open("users.json", "w") as f:
                json.dump([], f)

        with open("users.json", "r") as f:
            users = json.load(f)
    except:
        users = []

    if chat_id not in users:
        users.append(chat_id)
        with open("users.json", "w") as f:
            json.dump(users, f)
        print(f"✓ New user saved: {chat_id}")

def listen_for_new_users():
    """Continuously listen for /start messages and save chat IDs"""
    print("👂 Listening for new users...")
    last_update_id = None

    while True:
        try:
            url = f"{API_URL}/getUpdates"
            if last_update_id:
                url += f"?offset={last_update_id + 1}"

            res = requests.get(url).json()

            if "result" in res:
                for update in res["result"]:
                    last_update_id = update["update_id"]

                    message = update.get("message")
                    if not message:
                        continue

                    chat_id = message["chat"]["id"]
                    text = message.get("text", "")

                    if text == "/start":
                        save_user(chat_id)

                        # Send welcome message
                        welcome_msg = "You are now subscribed! 🎉\nYou will receive daily contest updates."
                        send_message(chat_id, welcome_msg)

                        # Send today's contests immediately
                        today_contests = get_today_contests()
                        contest_msg = format_contest_message(today_contests)
                        send_message(chat_id, contest_msg)

        except Exception as e:
            print(f"❌ Error listening for users: {e}")

        time.sleep(1)

# ---------------------- MESSAGE SENDER ----------------------
def send_message(chat_id, message):
    """Send a single Telegram message"""
    url = f"{API_URL}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "HTML"
    }
    try:
        requests.post(url, json=payload)
    except Exception as e:
        print(f"❌ Failed to send message to {chat_id}: {e}")

def send_to_all(message):
    """Send message to all saved users"""
    try:
        with open("users.json", "r") as f:
            users = json.load(f)
    except:
        users = []

    if not users:
        print("⚠ No users subscribed.")
        return

    for chat in users:
        send_message(chat, message)
        print(f"✓ Message sent to {chat}")

# ---------------------- CONTEST SYSTEM ----------------------
def get_today_contests():
    """Read contests.json and filter today's contests"""
    try:
        with open("contests.json", "r", encoding="utf-8") as f:
            contests = json.load(f)
        
        today = datetime.now().strftime("%d-%m-%Y")
        today_contests = []

        for contest in contests:
            contest_date = contest.get("date", "").strip()
            if contest_date == today:
                today_contests.append(contest)
        
        return today_contests

    except FileNotFoundError:
        print("❌ contests.json not found!")
        return []
    except json.JSONDecodeError:
        print("❌ Invalid JSON in contests.json!")
        return []

def format_contest_message(contests):
    """Format contests into a nice Telegram message"""
    if not contests:
        return "📅 <b>No contests scheduled for today!</b>\n\nEnjoy your free time! 😊"
    
    message = f"🎯 <b>Today's Contests ({len(contests)})</b>\n"
    message += "=" * 30 + "\n\n"
    
    for i, contest in enumerate(contests, 1):
        message += f"<b>{i}. {contest['contest']}</b>\n"
        message += f"   🕐 Time: {contest['start_time']} - {contest['end_time']}\n"
        message += f"   📱 Platform: {contest['platform']}\n"
        if contest.get('url'):
            message += f"   🔗 <a href='{contest['url']}'>Contest Link</a>\n"
        message += "\n"
    
    message += "Good luck! 🚀"
    return message

# ---------------------- BROADCAST SYSTEM ----------------------
def broadcast_daily_contests():
    """Send today's contests to all users"""
    print(f"📅 Sending daily contest updates at {datetime.now().strftime('%H:%M:%S')}...")
    today_contests = get_today_contests()
    message = format_contest_message(today_contests)
    send_to_all(message)
    schedule_contest_reminders(today_contests)

# ---------------------- REMINDER SYSTEM ----------------------
def schedule_contest_reminders(contests):
    """Schedule reminders 15 minutes before each contest"""
    now = datetime.now()
    for contest in contests:
        start_time_str = contest.get("start_time", "")
        if not start_time_str:
            continue

        try:
            start_time = datetime.strptime(start_time_str, "%H:%M")
            start_time = start_time.replace(year=now.year, month=now.month, day=now.day)
        except:
            continue

        reminder_time = start_time - timedelta(minutes=15)
        if reminder_time > now:
            schedule.every().day.at(reminder_time.strftime("%H:%M")).do(lambda c=contest: send_reminder(c))
            print(f"⏰ Scheduled reminder for {contest['contest']} at {reminder_time.strftime('%H:%M')}")

def send_reminder(contest):
    """Send reminder message 15 minutes before contest"""
    message = f"⏰ <b>Reminder:</b> {contest['contest']} starts in 15 minutes!\n"
    message += f"🕐 Time: {contest['start_time']} - {contest['end_time']}\n"
    message += f"📱 Platform: {contest['platform']}\n"
    if contest.get("url"):
        message += f"🔗 <a href='{contest['url']}'>Contest Link</a>"
    send_to_all(message)

# ---------------------- MAIN PROGRAM ----------------------
def main():
    print("=" * 60)
    print("Checking for today's contests...")
    print("=" * 60)
    
    today_contests = get_today_contests()
    
    if today_contests:
        print(f"\n✓ Found {len(today_contests)} contest(s) today!")
        for contest in today_contests:
            print(f"  - {contest['contest']} at {contest['start_time']}")
    else:
        print("\n📅 No contests today")
    
    message = format_contest_message(today_contests)

    print("\n📤 Sending contest updates to all users...\n")
    send_to_all(message)
    schedule_contest_reminders(today_contests)

# ---------------------- START BOT ----------------------
if __name__ == "__main__":
    print("Saving files to:", os.getcwd())

    # Start listener thread
    listener = threading.Thread(target=listen_for_new_users, daemon=True)
    listener.start()

    # Run main() once at startup
    main()

    # Automatically subscribe yourself
    send_message(INITIAL_USER_ID, "You are now subscribed! 🎉\nYou will receive daily contest updates.")
    send_message(INITIAL_USER_ID, format_contest_message(get_today_contests()))
    save_user(INITIAL_USER_ID)

    # Schedule daily broadcast at 04:00 AM
    schedule.every().day.at("04:00").do(broadcast_daily_contests)

    # Keep bot running forever
    print("Bot is running 24/7. Waiting for users...")
    while True:
        schedule.run_pending()
        time.sleep(10)
