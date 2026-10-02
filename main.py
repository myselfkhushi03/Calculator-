import os, json, threading
from datetime import datetime
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

BOT_TOKEN = os.environ.get("BOT_TOKEN")
VERIFY_CODE = "6118588149"
OWNER_NAME = "Khushi"
OWNER_USERNAME = "myselfkhushi03"
INSTA_LINK = f"https://instagram.com/{OWNER_USERNAME}"
ADMIN_IDS = [8536757095] # Tera ID

flask_app = Flask(__name__)
@flask_app.route('/')
def home(): return "Premium Bot Live - Final V3"

VERIFY_FILE = "verified.json"
USER_FILE = "users.json"

try:
    with open(VERIFY_FILE, "r") as f:
        verified_users = set(json.load(f))
except: verified_users = set()

try:
    with open(USER_FILE, "r") as f:
        users_data = json.load(f)
except: users_data = {}

def save_all():
    try:
        with open(VERIFY_FILE, "w") as f: json.dump(list(verified_users), f)
        with open(USER_FILE, "w") as f: json.dump(users_data, f)
    except: pass

def save_user(user):
    uid = str(user.id)
    if uid not in users_data:
        users_data[uid] = {
            "name": user.first_name,
            "username": f"@{user.username}" if user.username else "No username",
            "id": user.id,
            "joined": datetime.now().strftime("%d-%m-%Y %H:%M")
        }
        save_all()

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
    save_user(update.effective_user)
    uid = update.effective_user.id
    user_name = update.effective_user.first_name
    if uid in verified_users:
        await update.message.reply_text(f"Hey {user_name} ✨ Welcome back!\nSending your private collection...", reply_markup=keyboard())
        await send_photos(update, context)
        return
    await update.message.reply_text(
        f"Hey {user_name} ✨\n\nWelcome to {OWNER_NAME}'s private vault 💌\n━━━━━━━━━━━━━━━━━━━━\n\nI'm {OWNER_NAME}, so glad you're here!\n\nYou've found my exclusive collection 📸\nJust one step to unlock.\n\n👤 Your Name: {user_name}\n🆔 Your ID: {uid}\n\n🔐 Send the secret code to unlock\n\n<i>⚠️ Photos are one-time view & can't be forwarded</i>",
        parse_mode="HTML", reply_markup=keyboard()
    )

async def send_photos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        photos = get_photos()
        if not photos:
            await update.message.reply_text("Vault is empty right now")
            return
        await update.message.reply_text("🔓 Unlocking... Photos will auto-delete in 60 sec ⏳")
        for i, path in enumerate(photos, 1):
            try:
                with open(path, 'rb') as p:
                    msg = await update.message.reply_photo(
                        photo=p,
                        caption=f"For you, {update.effective_user.first_name} 💖 • {i}/{len(photos)}\nFrom: {OWNER_NAME} ✨\n\n⚠️ This will delete in 60s - No Forward Allowed",
                        reply_markup=keyboard(), has_spoiler=True, protect_content=True
                    )
                    context.job_queue.run_once(delete_msg, 60, data={'chat_id': msg.chat_id, 'msg_id': msg.message_id})
            except: continue
    except: pass

async def delete_msg(context: ContextTypes.DEFAULT_TYPE):
    try: await context.bot.delete_message(chat_id=context.job.data['chat_id'], message_id=context.job.data['msg_id'])
    except: pass

async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    save_user(update.effective_user)
    uid = update.effective_user.id
    text = update.message.text.strip()
    if uid not in verified_users:
        if text == VERIFY_CODE:
            verified_users.add(uid)
            save_all()
            await update.message.reply_text(f"Yayy! Access granted ✅\nSending photos from {OWNER_NAME}...")
            await send_photos(update, context)
        else:
            await update.message.reply_text("Oops! Wrong code 🥺 Try again")
        return
    await send_photos(update, context)

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("❌ Admin only")
        return
    if not users_data:
        await update.message.reply_text("No users yet")
        return
    text = f"📊 <b>Bot Stats - Full Details</b>\n━━━━━━━━━━━━\n👥 Total Verified: {len(verified_users)}\n📸 Total Photos: {len(get_photos())}\n━━━━━━━━━━━━\n\n"
    for i, (uid, info) in enumerate(users_data.items(), 1):
        verified = "✅ Verified" if int(uid) in verified_users else "❌ Not Verified"
        text += f"<b>{i}. {info['name']}</b>\n 👤 Username: {info['username']}\n 🆔 ID: <code>{info['id']}</code>\n 📅 Joined: {info['joined']}\n {verified}\n\n"
    if len(text) > 4000:
        for x in range(0, len(text), 4000):
            await update.message.reply_text(text[x:x+4000], parse_mode="HTML")
    else:
        await update.message.reply_text(text, parse_mode="HTML")

def run_flask():
    flask_app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))

if __name__ == '__main__':
    threading.Thread(target=run_flask, daemon=True).start()
    print(f"Photos found: {get_photos()}")
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CommandHandler("status", stats))
    app.add_handler(CommandHandler("users", stats))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))
    app.run_polling(drop_pending_updates=True)
