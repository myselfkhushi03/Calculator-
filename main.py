import json, os, time
from datetime import datetime
from zoneinfo import ZoneInfo
from collections import Counter
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

# Data files
USERS_FILE = "users.json"
BANNED_FILE = "banned.json"

# Anti-spam memory
cooldown = {}

def load_json(file):
    try:
        with open(file, "r") as f:
            return json.load(f)
    except: return {}

def save_json(file, data):
    with open(file, "w") as f:
        json.dump(data, f, indent=2)

# 1. Save user with IST time
def save_user(user_id, name):
    users = load_json(USERS_FILE)
    if str(user_id) not in users:
        users[str(user_id)] = {
            "name": name,
            "joined": datetime.now(ZoneInfo("Asia/Kolkata")).strftime("%d-%m-%Y %I:%M %p"),
            "date": datetime.now(ZoneInfo("Asia/Kolkata")).strftime("%d-%m-%Y"),
            "photos_seen": 0
        }
        save_json(USERS_FILE, users)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    banned = load_json(BANNED_FILE)
    if str(uid) in banned:
        await update.message.reply_text("❌ You are banned from this bot.")
        return

    # Anti-Spam: 5 sec cooldown
    if uid in cooldown and time.time() - cooldown[uid] < 5:
        await update.message.reply_text("⏳ Thoda slow bhai, 5 sec ruk ja.")
        return
    cooldown[uid] = time.time()

    save_user(uid, update.effective_user.username or update.effective_user.first_name)

    # Anti bar-bar same photo - logic
    users = load_json(USERS_FILE)
    seen = users[str(uid)].get("photos_seen", 0)
    users[str(uid)]["photos_seen"] = seen + 1
    save_json(USERS_FILE, users)

    await update.message.reply_text(f"🔥 Welcome {update.effective_user.first_name}!\nPhoto {seen+1} unlock ho gayi (Demo)")

# ADMIN COMMANDS

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id!= ADMIN_ID: return
    users = load_json(USERS_FILE)
    await update.message.reply_text(f"📊 Total Users: {len(users)}\nBanned: {len(load_json(BANNED_FILE))}")

async def export_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id!= ADMIN_ID: return
    await update.message.reply_document(document=open(USERS_FILE, "rb"), filename="users.json")

async def backup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id!= ADMIN_ID: return
    await update.message.reply_document(document=open(USERS_FILE, "rb"), caption="Backup ✅")

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id!= ADMIN_ID: return
    if not context.args:
        await update.message.reply_text("Use: /broadcast message yaha likho")
        return
    text = " ".join(context.args)
    users = load_json(USERS_FILE)
    sent = 0
    for uid in users:
        if uid in load_json(BANNED_FILE): continue
        try:
            await context.bot.send_message(int(uid), text)
            sent += 1
        except: pass
    await update.message.reply_text(f"Broadcast {sent} users ko bhej diya ✅")

async def ban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id!= ADMIN_ID: return
    if not context.args: return
    banned = load_json(BANNED_FILE)
    banned[context.args[0]] = True
    save_json(BANNED_FILE, banned)
    await update.message.reply_text(f"User {context.args[0]} banned ✅")

async def unban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id!= ADMIN_ID: return
    banned = load_json(BANNED_FILE)
    if context.args[0] in banned:
        del banned[context.args[0]]
        save_json(BANNED_FILE, banned)
    await update.message.reply_text(f"User {context.args[0]} unbanned ✅")

async def chart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id!= ADMIN_ID: return
    users = load_json(USERS_FILE)
    dates = [v.get("date","") for v in users.values()]
    c = Counter(dates)
    msg = "📈 Last 7 days chart:\n\n"
    for d, count in list(c.items())[-7:]:
        msg += f"{d}: {'█'*count} ({count})\n"
    await update.message.reply_text(msg)

app = Application.builder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("status", status))
app.add_handler(CommandHandler("export", export_users))
app.add_handler(CommandHandler("backup", backup))
app.add_handler(CommandHandler("broadcast", broadcast))
app.add_handler(CommandHandler("ban", ban))
app.add_handler(CommandHandler("unban", unban))
app.add_handler(CommandHandler("chart", chart))
app.run_polling()
