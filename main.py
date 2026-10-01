import os, json, logging, threading
from flask import Flask
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

BOT_TOKEN = os.environ.get("BOT_TOKEN")
PHOTO_FOLDER = "photos"
VERIFY_CODE = "6118588149"

INSTA_USERNAME = "myselfkhushi03"
TG_USERNAME = "myselfkhushi03"
INSTA_LINK = f"https://instagram.com/{INSTA_USERNAME}"
TG_LINK = f"https://t.me/{TG_USERNAME}"

VERIFY_FILE = "verified.json"
try:
    with open(VERIFY_FILE, "r") as f:
        verified_users = set(json.load(f))
except:
    verified_users = set()

def save_verified():
    with open(VERIFY_FILE, "w") as f:
        json.dump(list(verified_users), f)

logging.basicConfig(level=logging.INFO)
flask_app = Flask(__name__)

@flask_app.route('/')
def home():
    return f"Premium Bot Live - Verified: {len(verified_users)}"

# PHOTO SEND KARNE KA FUNCTION
async def send_all_photos(update, first_name, user_id, chat_id, username_tag):
    photos = sorted([f for f in os.listdir(PHOTO_FOLDER) if f.lower().endswith(('.jpg','.jpeg','.png','.webp'))])
    
    if not photos:
        await update.message.reply_text("❌ No photos found!")
        return

    await update.message.reply_text(
        f"💎 <b>Premium Delivery Unlocked</b> 💎\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 <b>Your Details:</b>\n"
        f"├ Name: {first_name}\n"
        f"├ Username: {username_tag}\n"
        f"├ User ID: <code>{user_id}</code>\n"
        f"├ Chat ID: <code>{chat_id}</code>\n"
        f"└ Total Photos: {len(photos)}\n\n"
        f"📤 <i>Sending all content directly...</i>",
        parse_mode="HTML"
    )

    for i, photo_name in enumerate(photos, 1):
        path = os.path.join(PHOTO_FOLDER, photo_name)
        caption = (
            f"📸 <b>Photo {i}/{len(photos)}</b>\n"
            f"👤 For: {first_name} | {username_tag}\n"
            f"🆔 User ID: <code>{user_id}</code>\n"
            f"💬 Chat ID: <code>{chat_id}</code>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f'📷 <a href="{INSTA_LINK}">Instagram: @{INSTA_USERNAME}</a>\n'
            f'✈️ <a href="{TG_LINK}">Telegram: @{TG_USERNAME}</a>\n'
            f"💎 Premium Access"
        )
        try:
            with open(path, 'rb') as photo:
                await update.message.reply_photo(photo=photo, caption=caption, parse_mode="HTML")
        except Exception as e:
            print(f"Error: {e}")

    await update.message.reply_text(
        f"✅ <b>All {len(photos)} files sent!</b>\n\n"
        f"💌 Follow for more:\n"
        f'📷 <a href="{INSTA_LINK}">Instagram</a> | ✈️ <a href="{TG_LINK}">Telegram</a>',
        parse_mode="HTML"
    )

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    chat_id = update.effective_chat.id
    name = update.effective_user.first_name
    username_tag = f"@{update.effective_user.username}" if update.effective_user.username else "No Username"

    if uid in verified_users:
        await update.message.reply_text(
            f"✨ <b>Welcome Back {name}!</b> You are already verified.\n"
            f"Sending your content directly...",
            parse_mode="HTML"
        )
        await send_all_photos(update, name, uid, chat_id, username_tag)
        return

    await update.message.reply_text(
        f"💎 <b>Welcome to Premium Access, {name}</b> 💎\n"
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
        f"👤 Name: {name}\n"
        f"👤 Username: {username_tag}\n"
        f"🆔 User ID: <code>{uid}</code>\n"
        f"💬 Chat ID: <code>{chat_id}</code>\n\n"
        f"🔐 <b>Send secret code to unlock instantly</b>\n"
        f"<i>After code, all photos will be sent automatically</i>",
        parse_mode="HTML"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    chat_id = update.effective_chat.id
    name = update.effective_user.first_name
    username_tag = f"@{update.effective_user.username}" if update.effective_user.username else "No Username"
    text = update.message.text.strip()

    if uid not in verified_users:
        if text == VERIFY_CODE:
            verified_users.add(uid)
            save_verified()
            await update.message.reply_text("✅ <b>Verification Successful! Sending all content...</b>", parse_mode="HTML")
            # CODE SAHI HOTE HI DIRECT SEND
            await send_all_photos(update, name, uid, chat_id, username_tag)
        else:
            await update.message.reply_text("❌ Invalid Code")
        return
    else:
        # Already verified hai to kuch bhi likhega to fir se bhej dega
        await send_all_photos(update, name, uid, chat_id, username_tag)

def run_bot():
    if not BOT_TOKEN:
        print("TOKEN missing")
        return
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("Bot running...")
    app.run_polling()

threading.Thread(target=run_bot, daemon=True).start()
if __name__ == '__main__':
    flask_app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
