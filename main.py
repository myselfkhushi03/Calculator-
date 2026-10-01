import os, threading
from flask import Flask
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

BOT_TOKEN = os.environ.get("BOT_TOKEN")
VERIFY_CODE = "6118588149"

verified_users = set()

flask_app = Flask(__name__)

@flask_app.route('/')
def home():
    return "Bot is Live"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"Bot live hai! Tera ID: {update.effective_user.id}\nSecret code bhej")

async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    text = update.message.text.strip()
    print(f"Message from {uid}: {text}") # Render logs me dikhega
    
    if uid not in verified_users:
        if text == VERIFY_CODE:
            verified_users.add(uid)
            await update.message.reply_text("✅ Verified! Ab username bhej")
        else:
            await update.message.reply_text(f"❌ Wrong code. Tune bheja: {text}")
        return
    else:
        await update.message.reply_text(f"Username mila: {text} - photos bhej raha hu")
        # photos bhejne ka try
        try:
            import os
            files = os.listdir("photos")
            await update.message.reply_text(f"Photos folder me {len(files)} files hain")
            for f in files[:5]:
                with open(f"photos/{f}", "rb") as p:
                    await update.message.reply_photo(p)
        except Exception as e:
            await update.message.reply_text(f"Photos error: {e}")

def run_bot():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))
    app.run_polling()

threading.Thread(target=run_bot, daemon=True).start()

if __name__ == '__main__':
    flask_app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
