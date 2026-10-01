import os, threading, re
from flask import Flask
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import instaloader

TOKEN = os.environ.get("BOT_TOKEN")
bot = telebot.TeleBot(TOKEN)

app = Flask(__name__)
@app.route('/')
def home(): return "Professional Insta Bot Running"
@app.route('/ping')
def ping(): return "alive", 200
def run_flask(): app.run(host='0.0.0.0', port=8080)

L = instaloader.Instaloader()

def pro_text(p, posts_info, email_found):
    return f"""
╭─「 INSTAGRAM PROFILE 」─
│
├ 👤 Full Name: {p.full_name}
├ 🔗 Username: @{p.username}
├ 🆔 User ID: {p.userid}
│
├─「 BIOGRAPHY 」
│ {p.biography or 'No bio available'}
│
├─「 STATISTICS 」
├ 👥 Followers: {p.followers:,}
├ 👤 Following: {p.followees:,}
├ 📸 Total Posts: {p.mediacount}
│
├─「 ACCOUNT INFO 」
├ 🔒 Private: {'Yes' if p.is_private else 'No'}
├ ✅ Verified: {'Yes' if p.is_verified else 'No'}
├ 💼 Business: {p.business_category_name or 'No'}
├ 📧 Email in Bio: {email_found or 'Not Found'}
├ 🔗 External Link: {p.external_url or 'None'}
│
╰─「 RECENT POSTS 」
{posts_info}
"""

@bot.message_handler(commands=['start'])
def start(m):
    bot.send_message(m.chat.id, "✨ Welcome to Pro Insta Info Bot ✨\n\nJust send any Instagram username.\nExample: virat.kohli", parse_mode="Markdown")

@bot.message_handler(func=lambda m: True)
def get_info(m):
    username = m.text.replace('/insta','').replace('@','').replace('/','').strip().split()[0]
    if len(username) < 2: return
    try:
        load = bot.send_message(m.chat.id, f"🔍 Fetching @{username}...")

        p = instaloader.Profile.from_username(L.context, username)

        email_regex = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
        emails = re.findall(email_regex, p.biography or "")
        email_found = emails[0] if emails else None

        posts_info = ""
        count = 0
        try:
            for post in p.get_posts():
                if count >= 3: break
                posts_info += f"├ ❤️ {post.likes} likes | 💬 {post.comments} comments\n"
                count += 1
        except:
            posts_info = "├ Private Account"

        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("🔗 Open Profile", url=f"https://instagram.com/{p.username}"))

        bot.delete_message(m.chat.id, load.message_id)
        bot.send_photo(m.chat.id, p.profile_pic_url, caption=pro_text(p, posts_info, email_found), reply_markup=markup)

    except Exception as e:
        bot.send_message(m.chat.id, f"❌ User @{username} not found.")

threading.Thread(target=run_flask).start()
bot.infinity_polling()
