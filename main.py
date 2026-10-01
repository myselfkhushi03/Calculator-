import os, threading, logging
from flask import Flask
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

BOT_TOKEN = os.environ.get("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
PHOTO_FOLDER = "photos"
VERIFY_CODE = "6118588149"
INSTA_USERNAME = "myselfkhushi03"
TG_USERNAME = "myselfkhushi03"

verified_users = set()
logging.basicConfig(level=logging.INFO)

flask_app = Flask(__name__)
@flask_app.route('/')
def home():
    return f"<h2>✅ Bot is Live 24x7 Free</h2><p>@{INSTA_USERNAME} | Verified: {len(verified_users)}</p>"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id in verified_users:
        await update.message.reply_text("✨ Already verified! Send username 📸", parse_mode="HTML")
        return
    await update.message.reply_text("💎 <b>Premium Access</b> 💎\n\n🔐 Send secret code to unlock 📸", parse_mode="HTML")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text.strip()
    if user_id not in verified_users:
        if text == VERIFY_CODE:
            verified_users.add(user_id)
            await update.message.reply_text("✅ Verified! Now send any username 📸", parse_mode="HTML")
        else:
            await update.message.reply_text("❌ Invalid Code 🔐", parse_mode="HTML")
        return

    photos = [f for f in os.listdir(PHOTO_FOLDER) if f.endswith(('.jpg','.png','.jpeg','.webp'))]
    for i, p in enumerate(photos, 1):
        with open(os.path.join(PHOTO_FOLDER, p), 'rb') as photo:
            await update.message.reply_photo(photo, caption=f"📸 Photo {i} | {text}\n📷 @{INSTA_USERNAME}", parse_mode="HTML")
    await update.message.reply_text(f"✅ Done! Follow @{INSTA_USERNAME}")

def run_bot():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()

# Free Web Service Trick
threading.Thread(target=run_bot, daemon=True).start()

if __name__ == '__main__':
    flask_app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
