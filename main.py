import json
import requests
from playwright.sync_api import sync_playwright
import os
from datetime import datetime, timedelta
import time

TELEGRAM_BOT_TOKEN = "bot tokem"
BASE_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"
USERS_FILE = "users.json"
CONTESTS_FILE = "contests.json"
URL = "https://codolio.com/event-tracker"


def load_json_file(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ Failed to load {path}: {e}")
        return []


def load_contests():
    data = load_json_file(CONTESTS_FILE)
    print("Loaded contests:", data)
    if not data:
        return []
    return data


def format_contest_entries(entries, title):
    """Format contest entries into a message"""
    if not entries:
        return f"❌ {title} - none found."

    msg = f"{title} ({len(entries)})\n"
    msg += "=" * 40 + "\n\n"
    for i, c in enumerate(entries, 1):
        msg += f"<b>{i}. {c.get('contest', 'Unnamed')}</b>\n"
        # use parsed date if available, else raw
        if c.get("_parsed_date"):
            msg += f"📅 {c['_parsed_date'].isoformat()}\n"
        else:
            msg += f"📅 {c.get('date', 'Unknown')}\n"

        # time fields
        st = c.get("start_time") or c.get("time") or ""
        et = c.get("end_time") or ""
        if st:
            msg += f"⏰ {st}"
            if et:
                msg += f" - {et}"
            msg += "\n"

        platform = c.get("platform") or c.get("site") or c.get("resource") or ""
        if platform:
            msg += f"📌 {platform}\n"

        if c.get("url"):
            msg += f"🔗 <a href='{c['url']}'>Link</a>\n"

        msg += "\n"

    return msg


def format_full_contests():
    contests = load_contests()
    #print("Formatting contests, count:", len(contests))
    if not contests:
        return "❌ No contests available to show."
    # Reuse format_contest_entries
    return format_contest_entries(contests, "ALL CONTESTS")


def load_users():
    data = load_json_file(USERS_FILE)
    if not data:
        return []
    # data may be a list of user objects or a single object
    if isinstance(data, dict):
        return [data]
    return data


def save_users(users):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=4)


def add_user(full_user):
    users = load_users()
    
    chat_id = full_user["chat_id"]
    exists = any(u["chat_id"] == chat_id for u in users)

    if not exists:
        users.append(full_user)
        save_users(users)
        print(f"✓ New user added: {full_user}")
    else:
        print(f"User already exists: {chat_id}")


def send_message(chat_id, text):
    try:
        requests.post(
            f"{BASE_URL}/sendMessage",
            json={"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
        )
    except Exception as e:
        print(f"❌ Failed to send to {chat_id}: {e}")


def listen_for_new_users():
    print("📡 Waiting for users to send /start...")

    offset = 0

    while True:
        try:
            response = requests.get(
                f"{BASE_URL}/getUpdates",
                params={"offset": offset, "timeout": 100}
            ).json()
            if "result" in response:
                for update in response["result"]:
                    offset = update["update_id"] + 1
                    if "message" in update:
                        msg = update["message"]
                        chat_id = msg["chat"]["id"]
                        text = msg.get("text", "")

                        if text == "/start":
                            from_user = msg["from"]

                            # Build full user object
                            user_data = {
                                "chat_id": chat_id,
                                "user_id": from_user.get("id"),
                                "first_name": from_user.get("first_name"),
                                "last_name": from_user.get("last_name"),
                                "username": from_user.get("username"),
                                "language": from_user.get("language_code")
                            }

                            add_user(user_data)

                            # Send message to the user
                            first_name = user_data.get("first_name") or ""
                            last_name = user_data.get("last_name") or ""
                            name = (first_name + " " + last_name).strip()
                            personalized = f"👋 Hello {name}!\n\n"
                            personalized += format_full_contests()
                            
                            send_message(chat_id, personalized)
                            print(f"✓ Sent to {chat_id}")
                            time.sleep(0.25)
                            
        except Exception as e:
            print("❌ Error:", e)
        time.sleep(1)


if __name__ == "__main__":
    print("🤖 User Registration Bot Running...")
    listen_for_new_users()
