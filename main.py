import json
import requests
import time
import datetime
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
key = os.getenv("key")
print(f"BOT_TOKEN: {BOT_TOKEN}")
print(f"API Key: {key}")

last_update_id = 0
user_limit = {}

def get_updates():
    """Fetch updates from Telegram API."""
    global last_update_id
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"

    try:
        response = requests.get(url)
        data = response.json()
        if "result" in data and data["result"]:
            latest_update = data["result"][-1]
            update_id = latest_update["update_id"]

            if update_id != last_update_id:
                # Extract required details
                message_part = latest_update["message"]["text"]
                chat_id = latest_update["message"]["chat"]["id"]
                first_name = latest_update["message"]["from"]["first_name"]
                reply_id = latest_update["message"]["message_id"]

                last_update_id = update_id  # Update the last processed ID
                return message_part, chat_id, first_name, reply_id, update_id
        return None  # No new updates
    except Exception as e:
        print(f"Error fetching updates: {e}")
        return None

def send_message(chat_id, text, reply_id=None):
    """Send a message to a Telegram user."""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "reply_to_message_id": reply_id}
    try:
        requests.post(url, json=payload)
    except Exception as e:
        print(f"Error sending message: {e}")

def is_valid_url(msg):
    """Check if the provided message is a valid URL."""
    return msg.lower().startswith("http")

def shorten_url(message_part, key):
    """Shorten the given URL using TinyURL API."""
    url = "https://api.tinyurl.com/create"
    payload = json.dumps({"url": message_part})
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {key}",
    }

    try:
        response = requests.post(url, headers=headers, data=payload)
        response_data = response.json()
        return response_data["data"]["tiny_url"]
    except Exception as e:
        print(f"Error shortening URL: {e}")
        return None

def user_limit_check(chat_id):
    """Check and enforce daily request limits for users."""
    now = datetime.datetime.now()
    if chat_id in user_limit:
        user_data = user_limit[chat_id]
        if user_data["count"] >= 5:
            time_diff = datetime.timedelta(days=1) - (now - user_data["timestamp"])
            if now - user_data["timestamp"] < datetime.timedelta(days=1):
                hours = time_diff.seconds // 3600
                minutes = (time_diff.seconds // 60) % 60
                seconds = time_diff.seconds % 60
                return (
                    False,
                    f"🙂 Daily limit of 5 requests reached.\nTime remaining: {hours:02}:{minutes:02}:{seconds:02}",
                )
            else:
                # Reset after 24 hours
                user_limit[chat_id] = {"count": 1, "timestamp": now}
        else:
            user_limit[chat_id]["count"] += 1
    else:
        user_limit[chat_id] = {"count": 1, "timestamp": now}
    return True, ""

def main():
    """Main polling loop."""
    print("Bot is running...")
    while True:
        try:
            update = get_updates()
            if update:
                message_part, chat_id, first_name, reply_id, update_id = update

                if is_valid_url(message_part):
                    allowed, message = user_limit_check(chat_id)
                    if allowed:
                        short_url = shorten_url(message_part, key)
                        if short_url:
                            send_message(
                                chat_id,
                                f"This is your shortened link 🔗:\n\n{short_url}",
                                reply_id,
                            )
                        else:
                            send_message(
                                chat_id,
                                "❌ Failed to shorten the URL. Please try again later.",
                                reply_id,
                            )
                    else:
                        send_message(chat_id, message, reply_id)
                else:
                    send_message(
                        chat_id,
                        f"Hello, {first_name}!\n\n❌ Invalid URL format.\nPlease enter a valid URL starting with 'https' or 'http'.",
                        reply_id,
                    )
        except Exception as e:
            print(f"Error in main loop: {e}")
        time.sleep(2)

if __name__ == "__main__":
    main()
