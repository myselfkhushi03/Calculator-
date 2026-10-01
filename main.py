import os, threading, asyncio
from flask import Flask
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

BOT_TOKEN = os.environ.get("BOT_TOKEN")
VERIFY_CODE = "6118588149"
verified_users = set()

flask_app = Flask(__name__)

@flask_app.route('/')
def home():
    status = "TOKEN OK" if BOT_TOKEN else "TOKEN MISSING - Add BOT_TOKEN in Render Env"
    return f"Live - {status} - Verified: {len(verified_users)}"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Bot working! Send code")

async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    text = update.message.text.strip()
    if uid not in verified_users:
        if text == VERIFY_CODE:
            verified_users.add(uid)
            await update.message.reply_text("✅ Verified")
        else:
            await update.message.reply_text("❌ Wrong code")
        return
    await update.message.reply_text(f"Got: {text}")
    try:
        for f in os.listdir("photos")[:10]:
            if f.lower().endswith(('.jpg','.png','.jpeg')):
                with open(os.path.join("photos", f), 'rb') as p:
                    await update.message.reply_photo(p)
    except Exception as e:
        await update.message.reply_text(f"Error: {e}")

def run_bot():
    if not BOT_TOKEN:
        print("❌ BOT_TOKEN missing in Environment Variables!")
        return
    async def runner():
        # delete old webhook first
        from telegram import Bot
        bot = Bot(BOT_TOKEN)
        await bot.delete_webhook(drop_pending_updates=True)
        print("✅ Webhook deleted, starting polling...")
        
        app = Application.builder().token(BOT_TOKEN).build()
        app.add_handler(CommandHandler("start", start))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))
        await app.initialize()
        await app.start()
        await app.updater.start_polling()
        print("✅ Bot polling started - now reply will come")
        while True:
            await asyncio.sleep(3600)
    asyncio.run(runner())

threading.Thread(target=run_bot, daemon=True).start()

if __name__ == '__main__':
    flask_app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
