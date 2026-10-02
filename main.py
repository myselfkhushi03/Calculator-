import os
from threading import Thread
from flask import Flask
from telegram.ext import Application, CommandHandler

BOT_TOKEN = os.getenv("BOT_TOKEN")

web = Flask(__name__)
@web.route('/')
def home(): return "OK @im_chikuuRobot"

def run_web():
    web.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))

Thread(target=run_web, daemon=True).start()

async def start(update, context):
    await update.message.reply_text("Bot is finally working! @im_chikuuRobot")

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    print("Starting Bot...")
    app.run_polling()

if __name__ == "__main__":
    main()
