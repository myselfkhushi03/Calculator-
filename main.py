import os, threading, re
from flask import Flask
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import yt_dlp

TOKEN = os.environ.get("BOT_TOKEN")
bot = telebot.TeleBot(TOKEN)

app = Flask(__name__)
@app.route('/')
def home(): return "Premium Bot Live"
def run_flask(): app.run(host='0.0.0.0', port=8080)

# Store url temporary
user_data = {}

def get_buttons(url_id):
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("🎬 Best Quality", callback_data=f"best|{url_id}"),
        InlineKeyboardButton("🎥 1080p HD", callback_data=f"1080|{url_id}"),
        InlineKeyboardButton("📱 720p HD", callback_data=f"720|{url_id}"),
        InlineKeyboardButton("📀 480p", callback_data=f"480|{url_id}"),
        InlineKeyboardButton("🎵 MP3 Audio", callback_data=f"mp3|{url_id}"),
        InlineKeyboardButton("🔊 M4A Audio", callback_data=f"m4a|{url_id}"),
    )
    return markup

@bot.message_handler(commands=['start'])
def start(m):
    bot.send_message(m.chat.id,
    "╭─「 **PREMIUM DOWNLOADER** 」─\n"
    "│\n"
    "├ 🔥 YouTube / Insta / FB / TikTok\n"
    "├ 🎬 Quality Select Option\n"
    "├ 🎵 MP3 / Audio Support\n"
    "│\n"
    "╰─ Bas Link Bhejo 👇",
    parse_mode="Markdown")

@bot.message_handler(func=lambda m: True)
def handle_link(m):
    url = m.text.strip()
    if not url.startswith("http"):
        return bot.reply_to(m, "❌ Link bhejo bhai!")

    load = bot.reply_to(m, "🔍 **Fetching details...**", parse_mode="Markdown")

    try:
        ydl_opts = {'quiet': True, 'no_warnings': True, 'skip_download': True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            title = info.get('title','Unknown Title')[:70]
            thumb = info.get('thumbnail')
            duration = info.get('duration', 0)
            views = info.get('view_count', 0)

        user_data[str(m.chat.id)] = url

        caption = (
            f"╭─「 **VIDEO FOUND** 」─\n"
            f"│\n"
            f"├ 🎬 **Title:** {title}\n"
            f"├ ⏱️ **Duration:** {duration//60}:{duration%60:02d} min\n"
            f"├ 👁️ **Views:** {views:,}\n"
            f"│\n"
            f"╰─ **Quality Select Karo 👇**"
        )

        bot.delete_message(m.chat.id, load.message_id)
        if thumb:
            bot.send_photo(m.chat.id, thumb, caption=caption, parse_mode="Markdown", reply_markup=get_buttons(str(m.chat.id)))
        else:
            bot.send_message(m.chat.id, caption, parse_mode="Markdown", reply_markup=get_buttons(str(m.chat.id)))

    except Exception as e:
        bot.edit_message_text(f"❌ Link support nahi hai ya private hai.\nYouTube link try kar.", m.chat.id, load.message_id)

@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    try:
        quality, chat_id_key = call.data.split("|")
        url = user_data.get(chat_id_key)
        if not url:
            return bot.answer_callback_query(call.id, "❌ Link expire ho gaya, dobara bhejo!")

        bot.edit_message_caption(f"⏳ **Downloading {quality.upper()}...**\n\nThoda wait karo, premium quality me bhej raha hu...", call.message.chat.id, call.message.message_id, parse_mode="Markdown")

        # Format select
        if quality == "best":
            fmt = "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best"
        elif quality == "1080":
            fmt = "bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[height<=1080]"
        elif quality == "720":
            fmt = "bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720]"
        elif quality == "480":
            fmt = "best[height<=480][ext=mp4]/best[height<=480]"
        elif quality == "mp3":
            fmt = "bestaudio/best"
            # will convert to mp3 via postprocessor
        else:
            fmt = "bestaudio[ext=m4a]/bestaudio"

        ydl_opts = {
            'format': fmt,
            'outtmpl': f'/tmp/{chat_id_key}_%(id)s.%(ext)s',
            'quiet': True,
        }
        if quality == "mp3":
            ydl_opts.update({
                'postprocessors': [{'key': 'FFmpegExtractAudio','preferredcodec': 'mp3','preferredquality': '192'}]
            })

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            file_path = ydl.prepare_filename(info)
            # fix for mp3 extension
            if quality == "mp3":
                file_path = file_path.rsplit(".",1)[0] + ".mp3"

            final_caption = f"✅ **{info.get('title','')[:80]}**\n\n╰─ Quality: {quality.upper()} | @YourBotName"

            with open(file_path, 'rb') as f:
                if quality in ["mp3","m4a"]:
                    bot.send_audio(call.message.chat.id, f, caption=final_caption, parse_mode="Markdown")
                else:
                    bot.send_video(call.message.chat.id, f, caption=final_caption, parse_mode="Markdown", supports_streaming=True)

            if os.path.exists(file_path):
                os.remove(file_path)

        bot.delete_message(call.message.chat.id, call.message.message_id)

    except Exception as e:
        print(e)
        bot.send_message(call.message.chat.id, f"❌ Download fail: {str(e)[:150]}")

threading.Thread(target=run_flask, daemon=True).start()
bot.infinity_polling(skip_pending=True)
