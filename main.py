import os, json, threading
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

BOT_TOKEN = os.environ.get("BOT_TOKEN")
VERIFY_CODE = "6118588149"
OWNER_NAME = "Khushi" # Bot owner ka naam
OWNER_USERNAME = "myselfkhushi03"
INSTA_LINK = f"https://instagram.com/{OWNER_USERNAME}"

flask_app = Flask(__name__)
@flask_app.route('/')
def home(): return "Live"

VERIFY_FILE = "verified.json"
try:
    with open(VERIFY_FILE, "r") as f:
        verified_users = set(json.load(f))
except:
    verified_users = set()
def save_verified():
    with open(VERIFY_FILE, "w") as f:
        json.dump(list(verified_users), f)

def get_photos():
    photos = []
    for folder in [".", "photos"]:
        if os.path.exists(folder):
            for file in os.listdir(folder):
                if file.lower().endswith(('.jpg','.jpeg','.png','.webp')):
                    path = file if folder == "." else os.path.join(folder, file)
                    if os.path.isfile(path): photos.append(path)
    return list(set(photos))

def keyboard():
    return InlineKeyboardMarkup([[InlineKeyboardButton(f"📷 Follow {OWNER_NAME} on Instagram", url=INSTA_LINK)]])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    user_name = update.effective_user.first_name # User ka asli naam
    uname = f"@{update.effective_user.username}" if update.effective_user.username else user_name

    if uid in verified_users:
        await update.message.reply_text(
            f"Hey {user_name} ✨ Welcome back!\n\n"
            f"You already have access 💌\n"
            f"Sending your photos directly...",
            parse_mode="HTML", reply_markup=keyboard()
        )
        await send_photos(update)
        return

    # AB OWNER KA NAAM KHUSHI HAI, USER KA NAAM ALAG
    await update.message.reply_text(
        f"Hey {user_name} ✨\n\n"
        f"Welcome to {OWNER_NAME}'s private vault 💌\n"
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
        f"I'm {OWNER_NAME}, so glad you're here! 💖\n\n"
        f"You've found my most exclusive collection 📸\n"
        f"Just one tiny step to unlock everything.\n\n"
        f"👤 Your Name: <b>{user_name}</b>\n"
        f"🆔 Your ID: <code>{uid}</code>\n\n"
        f"🔐 Send the secret code to get instant access\n\n"
        f"<i>It's 100% private, just for you</i>",
        parse_mode="HTML", reply_markup=keyboard()
    )

async def send_photos(update: Update):
    photos = get_photos()
    if not photos: return
    name = update.effective_user.first_name
    for i, path in enumerate(photos, 1):
        with open(path, 'rb') as p:
            await update.message.reply_photo(
                photo=p,
                caption=f"For you, {name} 💖 • {i}/{len(photos)}\n\nFrom: {OWNER_NAME} | @{OWNER_USERNAME}\nHope you like it! ✨",
                parse_mode="HTML", reply_markup=keyboard()
            )

async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if uid not in verified_users:
        if update.message.text.strip() == VERIFY_CODE:
            verified_users.add(uid)
            save_verified()
            await update.message.reply_text(f"Yayy {update.effective_user.first_name}! Access granted ✅\nSending all photos from {OWNER_NAME} now...", parse_mode="HTML")
            await send_photos(update)
        else:
            await update.message.reply_text("Oops! Wrong code 🙂 Try again!")
        return
    await send_photos(update)

def run_bot():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))
    app.run_polling()

threading.Thread(target=run_bot, daemon=True).start()
if __name__ == '__main__':
    flask_app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
