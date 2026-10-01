import os, threading, re, requests, time
from flask import Flask
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

TOKEN = os.environ.get("BOT_TOKEN")
bot = telebot.TeleBot(TOKEN)

# Ye 409 error fix karega
try:
    bot.remove_webhook()
    time.sleep(1)
    bot.delete_webhook(drop_pending_updates=True)
except: pass

app = Flask(__name__)
@app.route('/')
def home(): return "Bot Fixed & Running"
@app.route('/ping')
def ping(): return "alive", 200
def run_flask(): app.run(host='0.0.0.0', port=8080)

def get_insta_info(username):
    headers = {
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15",
        "X-IG-App-ID": "936619743392459"
    }
    url = f"https://i.instagram.com/api/v1/users/web_profile_info/?username={username}"
    r = requests.get(url, headers=headers, timeout=15)
    if r.status_code!= 200:
        raise Exception(f"Status {r.status_code}")
    data = r.json()['data']['user']
    return data

@bot.message_handler(commands=['start'])
def start(m):
    bot.send_message(m.chat.id, "✨ **Pro Bot Fixed** ✨\nUsername bhejo ex: `virat.kohli`", parse_mode="Markdown")

@bot.message_handler(func=lambda m: True)
def get_info(m):
    username = m.text.replace('/insta','').replace('@','').replace('/','').strip().split()[0].lower()
    if len(username) < 2: return
    try:
        load = bot.send_message(m.chat.id, f"🔍 Fetching `@{username}`...", parse_mode="Markdown")

        p = get_insta_info(username)

        bio = p.get('biography') or 'No bio'
        email_regex = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
        emails = re.findall(email_regex, bio)
        email_found = emails[0] if emails else 'Not Found'

        text = f"""
╭─「 **INSTAGRAM PROFILE** 」─
│
├ 👤 **Name:** {p.get('full_name')}
├ 🔗 **Username:** @{p.get('username')}
├ 🆔 **ID:** `{p.get('id')}`
│
├─「 **BIO** 」
│ {bio}
│
├─「 **STATS** 」
├ 👥 Followers: `{p.get('edge_followed_by',{}).get('count',0):,}`
├ 👤 Following: `{p.get('edge_follow',{}).get('count',0):,}`
├ 📸 Posts: `{p.get('edge_owner_to_timeline_media',{}).get('count',0)}`
│
├─「 **INFO** 」
├ 🔒 Private: {'Yes' if p.get('is_private') else 'No'}
├ ✅ Verified: {'Yes' if p.get('is_verified') else 'No'}
├ 📧 Email in Bio: {email_found}
├ 🔗 Link: {p.get('bio_links')[0]['url'] if p.get('bio_links') else 'None'}
│
╰─ **https://instagram.com/{username}**
"""
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("🔗 Open Profile", url=f"https://instagram.com/{username}"))

        bot.delete_message(m.chat.id, load.message_id)
        bot.send_photo(m.chat.id, p.get('profile_pic_url_hd'), caption=text, parse_mode="Markdown", reply_markup=markup)

    except Exception as e:
        print(e)
        try: bot.delete_message(m.chat.id, load.message_id)
        except: pass
        bot.send_message(m.chat.id, f"❌ `@{username}` nahi mila ya Instagram ne block kiya.\nDusra username try kar.", parse_mode="Markdown")

threading.Thread(target=run_flask, daemon=True).start()

if __name__ == "__main__":
    # infinity_polling ki jagah ye use kar - conflict khatam
    while True:
        try:
            bot.infinity_polling(timeout=60, long_polling_timeout=60, skip_pending=True)
        except Exception as e:
            print(f"Polling error: {e}")
            time.sleep(5)
