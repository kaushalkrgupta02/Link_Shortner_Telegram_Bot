import json
import requests
import time
import datetime
from dotenv import load_dotenv
import os


load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
key = os.getenv("key")
print(BOT_TOKEN)
print(key)

last_update_id = 0
last_sent_update_id = 0


def get_updates(offset=None):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"
    params = {"offset": offset, "timeout": 5}
    try:
        response = requests.get(url)
        data = response.json()
        message_part = data["result"][-1]["message"]["text"]
        id = data["result"][-1]["message"]["chat"]["id"]
        first_name = data["result"][-1]["message"]["from"]["first_name"]
        reply_id = data["result"][-1]["message"]["message_id"]
        update_id = data["result"][-1]["update_id"]
        return message_part, id, first_name, reply_id, update_id

    except Exception as e:
        print(f"Error fetching updates: {e}")


def sendMessage(id, shrt_url, message_id=None):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": id, "text": shrt_url, "reply_to_message_id": message_id}
    r = requests.post(url, json=payload)
    # print(r.json())


def isValidUrl(msg):
    return msg.startswith("http") or msg.startswith("Http")


def fromapi(message_part, key):
    url = "https://api.tinyurl.com/create?api_token={key}"

    payload = json.dumps({"url": message_part})
    print(payload)
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {key}",
    }

    response = requests.post(url, headers=headers, data=payload)
    shrt_url = response.json()["data"]["tiny_url"]
    return shrt_url


user_limit = {}


def user_lmt(id):
    now = datetime.datetime.now()
    if id in user_limit:
        if user_limit[id]["count"] > 5:
            print(user_limit[id]["timestamp"])
            time_diff = datetime.timedelta(days=1) - (now - user_limit[id]["timestamp"])
            hour = time_diff.seconds // 3600
            min =  (time_diff.seconds // 60) % 60
            sec = time_diff.seconds % 60
            if now - user_limit[id]["timestamp"] < datetime.timedelta(days=1):
                return (
                    False,
                    f"🙂 Thank you.\nThis is an experimental BOT, and the admin has set a daily limit of 5 successful requests per user\n\n Time Remaining : {hour}:{min}:{sec} ",
                )
            else:
                user_limit[id] = {"count": 1, "timestamp": now}
        else:
            user_limit[id]["count"] += 1
    else:
        user_limit[id] = {"count": 1, "timestamp": now}
    return True, ""


def main():
    global last_update_id
    global last_sent_update_id
    while True:
        try:
            get_updt = get_updates()
            update_id = get_updt[4]
            if update_id != last_update_id:
                last_update_id = update_id
                message_part = get_updt[0]
                id = get_updt[1]
                first_name = get_updt[2]
                reply_id = get_updt[3]
                if isValidUrl(message_part):
                    allowed, msg = user_lmt(id)
                    if allowed:
                        shrt_url = fromapi(message_part, key)
                        print(shrt_url)
                        sendMessage(
                            id,
                            f"This is your shorten link🔗 👇\n\n{shrt_url}",
                            reply_id,
                        )
                        print("\n")
                        print(user_limit)
                        print("\n")

                    else:
                        sendMessage(id, msg)
                else:
                    sendMessage(
                        id,
                        f'Hello, {first_name}\n\n❌ Wrong URL for this Bot\n\n☺ Please enter a valid URL which starts with 🔐"https" ',
                        reply_id,
                    )

                last_sent_update_id = update_id
        except Exception as e:
            print(f"Error: {e}")
            # sendMessage(id, f"Error: {e}", reply_id)
        time.sleep(2)


if __name__ == "__main__":
    main()
