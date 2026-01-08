from flask import Flask, request
import requests, sqlite3, datetime, os
import openai

app = Flask(__name__)

PAGE_TOKEN = os.getenv("PAGE_TOKEN")
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")
openai.api_key = os.getenv("OPENAI_API_KEY")

conn = sqlite3.connect("chatlog.db", check_same_thread=False)
cur = conn.cursor()
cur.execute("""
CREATE TABLE IF NOT EXISTS chat(
user TEXT, msg TEXT, reply TEXT, time TEXT)
""")
conn.commit()

KEYWORDS = {
    "hello": "Xin chào 👋",
    "giá": "Inbox để nhận báo giá 💰",
    "admin": "Admin sẽ liên hệ bạn sớm"
}

@app.route("/webhook", methods=["GET"])
def verify():
    if request.args.get("hub.verify_token") == VERIFY_TOKEN:
        return request.args.get("hub.challenge")
    return "Sai token"

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.json
    for entry in data["entry"]:
        for event in entry["messaging"]:
            if "message" in event:
                uid = event["sender"]["id"]
                text = event["message"].get("text", "")

                reply = keyword(text)
                if not reply:
                    reply = chatgpt(text)

                send(uid, reply)
                save(uid, text, reply)
    return "OK"

def keyword(text):
    text = text.lower()
    for k in KEYWORDS:
        if k in text:
            return KEYWORDS[k]

def chatgpt(text):
    try:
        r = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role":"user","content":text}]
        )
        return r.choices[0].message.content
    except:
        return "Bot đang bận 😥"

def send(uid, text):
    url = f"https://graph.facebook.com/v18.0/me/messages?access_token={PAGE_TOKEN}"
    requests.post(url, json={
        "recipient":{"id":uid},
        "message":{"text":text}
    })

def save(u,m,r):
    t = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cur.execute("INSERT INTO chat VALUES (?,?,?,?)",(u,m,r,t))
    conn.commit()

if __name__ == "__main__":
    app.run()
