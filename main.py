import os, json, threading
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

BOT_TOKEN = os.environ.get("BOT_TOKEN")
VERIFY_CODE = "6118588149"
OWNER_NAME = "Khushi"
OWNER_USERNAME = "myselfkhushi03"
INSTA_LINK = f"https://instagram.com/{OWNER_USERNAME}"

flask_app = Flask(__name__)
@flask_app.route('/')
def home(): return "Premium Bot Live - OK"

# Verified system
VERIFY_FILE = "verified.json"
try:
    with open(VERIFY_FILE, "r") as f:
        verified_users = set(json.load(f))
except:
    verified_users = set()

def save_verified():
    try:
        with open(VERIFY_FILE, "w") as f:
            json.dump(list(verified_users), f)
    except: pass

def get_photos():
    photos = []
    for folder in [".", "photos"]:
        if os.path.exists(folder):
            for file in os.listdir(folder):
                if file.lower().endswith(('.jpg','.jpeg','.png','.webp')):
                    path = file if folder == "." else os.path.join(folder, file)
                    if os.path.isfile(path):
                        photos.append(path)
    return list(set(photos))

def keyboard():
    return InlineKeyboardMarkup([[InlineKeyboardButton(f"📷 Follow {OWNER_NAME}", url=INSTA_LINK)]])

# --- ALWAYS WORKS WELCOME ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        uid = update.effective_user.id
        user_name = update.effective_user.first_name
        
        if uid in verified_users:
            await update.message.reply_text(
                f"Hey {user_name} ✨ Welcome back!\n\nYour access is active 💌\nSending photos directly...",
                reply_markup=keyboard()
            )
            await send_photos(update)
            return

        # Ye msg 100% ayega, isme photo ka koi code nahi
        await update.message.reply_text(
            f"Hey {user_name} ✨\n\n"
            f"Welcome to {OWNER_NAME}'s private vault 💌\n"
            f"━━━━━━━━━━━━━━━━━━━━\n\n"
            f"I'm {OWNER_NAME}, so glad you're here!\n\n"
            f"You've found my exclusive collection 📸\n"
            f"Just one step to unlock.\n\n"
            f"👤 Your Name: {user_name}\n"
            f"🆔 Your ID: {uid}\n\n"
            f"🔐 Send the secret code to unlock",
            reply_markup=keyboard()
        )
    except Exception as e:
        print(f"START ERROR: {e}")
        await update.message.reply_text(f"Hey! Bot is working ✅ Your ID: {update.effective_user.id}")

# --- SAFE PHOTO SENDER (crash proof) ---
async def send_photos(update: Update):
    try:
        photos = get_photos()
        if not photos:
            await update.message.reply_text("Vault is empty right now, contact @myselfkhushi03")
            return
        
        for i, path in enumerate(photos, 1):
            try:
                with open(path, 'rb') as p:
                    await update.message.reply_photo(
                        photo=p,
                        caption=f"For you, {update.effective_user.first_name} 💖 • {i}/{len(photos)}\nFrom: {OWNER_NAME} ✨",
                        reply_markup=keyboard()
                    )
            except Exception as e:
                print(f"Photo send error {path}: {e}")
                continue
    except Exception as e:
        print(f"SEND_PHOTOS ERROR: {e}")

async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        uid = update.effective_user.id
        text = update.message.text.strip()
        if uid not in verified_users:
            if text == VERIFY_CODE:
                verified_users.add(uid)
                save_verified()
                await update.message.reply_text(f"Yayy! Access granted ✅\nSending photos from {OWNER_NAME}...")
                await send_photos(update)
            else:
                await update.message.reply_text("Oops! Wrong code 😗 Try again")
            return
        await send_photos(update)
    except Exception as e:
        print(f"HANDLE ERROR: {e}")

def run_bot():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))
    app.run_polling(drop_pending_updates=True)

threading.Thread(target=run_bot, daemon=True).start()

if __name__ == '__main__':
    flask_app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
