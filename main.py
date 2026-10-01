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
def home(): return "Premium Bot Live - Fixed"

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
                    if os.path.isfile(path): photos.append(path)
    return list(set(photos))

def keyboard():
    return InlineKeyboardMarkup([[InlineKeyboardButton(f"📷 Follow {OWNER_NAME}", url=INSTA_LINK)]])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    user_name = update.effective_user.first_name
    if uid in verified_users:
        await update.message.reply_text(f"Hey {user_name} ✨ Welcome back!\nSending photos directly...", reply_markup=keyboard())
        await send_photos(update)
        return
    await update.message.reply_text(
        f"Hey {user_name} ✨\n\nWelcome to {OWNER_NAME}'s private vault 💌\n━━━━━━━━━━━━━━━━━━━━\n\nI'm {OWNER_NAME}, so glad you're here!\n\nYou've found my exclusive collection 📸\nJust one step to unlock.\n\n👤 Your Name: {user_name}\n🆔 Your ID: {uid}\n\n🔐 Send the secret code to unlock",
        reply_markup=keyboard()
    )

async def send_photos(update: Update):
    try:
        photos = get_photos()
        if not photos:
            await update.message.reply_text("Vault is empty right now")
            return
        for i, path in enumerate(photos, 1):
            try:
                with open(path, 'rb') as p:
                    await update.message.reply_photo(photo=p, caption=f"For you, {update.effective_user.first_name} 💖 • {i}/{len(photos)}\nFrom: {OWNER_NAME} ✨", reply_markup=keyboard())
            except: continue
    except: pass

async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    text = update.message.text.strip()
    if uid not in verified_users:
        if text == VERIFY_CODE:
            verified_users.add(uid)
            save_verified()
            await update.message.reply_text(f"Yayy! Access granted ✅\nSending photos from {OWNER_NAME}...")
            await send_photos(update)
        else:
            await update.message.reply_text("Oops! Wrong code 🥺 Try again")
        return
    await send_photos(update)

# FLASK KO BACKGROUND ME
def run_flask():
    flask_app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))

if __name__ == '__main__':
    # Flask background me
    threading.Thread(target=run_flask, daemon=True).start()
    
    # BOT MAIN THREAD ME - Yahi fix hai
    print(f"Photos found: {get_photos()}")
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))
    app.run_polling(drop_pending_updates=True)
