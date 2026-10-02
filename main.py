import os, json, time, random
from threading import Thread
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand, BotCommandScopeDefault, BotCommandScopeChat
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

web = Flask(__name__)
@web.route('/')
def home(): return "Bot Alive"
def run_web(): web.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
Thread(target=run_web, daemon=True).start()

USERS_FILE="users.json"; BANNED_FILE="banned.json"; SETTINGS_FILE="settings.json"
PHOTO_FOLDER="photos"; os.makedirs(PHOTO_FOLDER, exist_ok=True)

def load(f):
    try: return json.load(open(f,"r"))
    except: return {}
def save(f,d): json.dump(d, open(f,"w"), indent=2)

def get_settings():
    s=load(SETTINGS_FILE)
    if not s:
        s={"name":"Khushi","insta":"https://www.instagram.com/_khushi..1432__?igsh=MTU2b3c0d3R4eW90","code":"6118588149","welcome":"Hey {user} ✨\n\nWelcome to {name}'s private vault 💌\n______________________________\n\nI'm {name}, so glad you're here!\n\nYou've found my exclusive collection 📸\nJust one step to unlock.\n\n👤 Your Name: {user}\n🆔 Your ID: {id}\n\n🔐 Send the secret code to unlock"}
        save(SETTINGS_FILE,s)
    return s

def get_photos(): return [os.path.join(PHOTO_FOLDER,x) for x in os.listdir(PHOTO_FOLDER) if x.lower().endswith(('.jpg','.jpeg','.png','.webp'))]

def is_banned(uid):
    b=load(BANNED_FILE)
    if str(uid) not in b: return False
    exp=b[str(uid)]
    if exp=="perm": return True
    if time.time()>exp:
        b.pop(str(uid)); save(BANNED_FILE,b); return False
    return True

def parse_time(t):
    if t in ["perm","permanent"]: return "perm"
    try:
        unit=t[-1]; num=int(t[:-1])
        if unit=="m": return time.time()+num*60
        if unit=="h": return time.time()+num*3600
        if unit=="d": return time.time()+num*86400
    except: return None

# --- Commands Setup (Admin only visibility) ---
async def setup_commands(app: Application):
    await app.bot.set_my_commands([BotCommand("start", "Start the bot")], scope=BotCommandScopeDefault())
    if ADMIN_ID!= 0:
        admin_cmds = [
            BotCommand("start", "Start bot"),
            BotCommand("setname", "Change name"),
            BotCommand("setcode", "Change secret code"),
            BotCommand("setinsta", "Change insta link"),
            BotCommand("add", "Add photo (reply to photo)"),
            BotCommand("status", "Check status"),
            BotCommand("ban", "Ban user: /ban ID 1d/2d/perm"),
            BotCommand("unban", "Unban user: /unban ID"),
            BotCommand("broadcast", "Send msg to all users"),
        ]
        await app.bot.set_my_commands(admin_cmds, scope=BotCommandScopeChat(chat_id=ADMIN_ID))

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if is_banned(update.effective_user.id): return
    s=get_settings(); uid=str(update.effective_user.id)
    users=load(USERS_FILE)
    if uid not in users:
        users[uid]={"name":update.effective_user.first_name}; save(USERS_FILE,users)
    welcome = s["welcome"].replace("{user}", update.effective_user.first_name).replace("{name}", s["name"]).replace("{id}", str(uid))
    btn = [[InlineKeyboardButton(f"📷 Follow {s['name']}", url=s["insta"])]]
    await update.message.reply_text(welcome, reply_markup=InlineKeyboardMarkup(btn))

async def check_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if is_banned(update.effective_user.id): return
    s=get_settings(); txt=update.message.text.strip()
    if txt==s["code"]:
        all_photos=get_photos()
        if not all_photos:
            await update.message.reply_text("No photos yet"); return
        to_send = random.sample(all_photos, min(2, len(all_photos)))
        await update.message.reply_text(f"Yayy! Access granted ✅\nSending from {s['name']}...")
        for i, p in enumerate(to_send, 1):
            cap = f"For you, {update.effective_user.first_name} 💖 • {i}/{len(to_send)}\nFrom: {s['name']} ✨"
            btn = [[InlineKeyboardButton(f"📷 Follow {s['name']}", url=s["insta"])]]
            await update.message.reply_photo(open(p,"rb"), caption=cap, reply_markup=InlineKeyboardMarkup(btn))
    elif txt.isdigit() and len(txt)>=4:
        await update.message.reply_text("Oops! Wrong code 🥺")

async def set_name(update, context):
    if update.effective_user.id!=ADMIN_ID: return
    s=get_settings(); s["name"]=" ".join(context.args); save(SETTINGS_FILE,s)
    await update.message.reply_text(f"Name -> {s['name']}")
async def set_code(update, context):
    if update.effective_user.id!=ADMIN_ID: return
    s=get_settings(); s["code"]=context.args[0]; save(SETTINGS_FILE,s)
    await update.message.reply_text(f"Code -> {s['code']}")
async def set_insta(update, context):
    if update.effective_user.id!=ADMIN_ID: return
    s=get_settings(); s["insta"]=context.args[0]; save(SETTINGS_FILE,s)
    await update.message.reply_text("Insta updated")
async def add_photo(update, context):
    if update.effective_user.id!=ADMIN_ID: return
    if not update.message.reply_to_message or not update.message.reply_to_message.photo:
        await update.message.reply_text("Reply to photo with /add"); return
    file=await update.message.reply_to_message.photo[-1].get_file()
    await file.download_to_drive(os.path.join(PHOTO_FOLDER, f"{int(time.time())}.jpg"))
    await update.message.reply_text(f"Added ✅ Total: {len(get_photos())}")
async def status(update, context):
    if update.effective_user.id!=ADMIN_ID: return
    s=get_settings()
    await update.message.reply_text(f"Name:{s['name']}\nCode:{s['code']}\nPhotos:{len(get_photos())}\nUsers:{len(load(USERS_FILE))}\nBanned:{len(load(BANNED_FILE))}")

async def ban(update, context):
    if update.effective_user.id!=ADMIN_ID: return
    if len(context.args)<1:
        await update.message.reply_text("Use: /ban USER_ID 1d / 2d / perm\nEx: /ban 12345 2d")
        return
    uid=context.args[0]
    dur=context.args[1] if len(context.args)>1 else "perm"
    exp=parse_time(dur)
    if not exp:
        await update.message.reply_text("Time galat hai. Use: 1d, 2d, 7d, 1h, 30m, perm"); return
    b=load(BANNED_FILE); b[uid]=exp; save(BANNED_FILE,b)
    await update.message.reply_text(f"User {uid} banned for {dur} ✅")

async def unban(update, context):
    if update.effective_user.id!=ADMIN_ID: return
    if len(context.args)<1: return
    b=load(BANNED_FILE); b.pop(context.args[0],None); save(BANNED_FILE,b)
    await update.message.reply_text(f"User {context.args[0]} unbanned ✅")

async def broadcast(update, context):
    if update.effective_user.id!=ADMIN_ID: return
    users = load(USERS_FILE)
    if not users:
        await update.message.reply_text("Koi user nahi hai abhi")
        return
    # Agar kisi msg/photo pe reply karke /broadcast kiya
    if update.message.reply_to_message:
        msg = update.message.reply_to_message
        await update.message.reply_text(f"Broadcasting to {len(users)} users...")
        count=0
        for uid in users.keys():
            try:
                await msg.copy(chat_id=int(uid))
                count+=1
            except: pass
        await update.message.reply_text(f"Broadcast done ✅ Sent to {count} users")
    else:
        text = " ".join(context.args)
        if not text:
            await update.message.reply_text("Use:\n/broadcast Your message here\n\nYa kisi photo/msg pe reply karke /broadcast likho")
            return
        await update.message.reply_text(f"Broadcasting to {len(users)} users...")
        count=0
        for uid in users.keys():
            try:
                await context.bot.send_message(chat_id=int(uid), text=text)
                count+=1
            except: pass
        await update.message.reply_text(f"Broadcast done ✅ Sent to {count} users")

def main():
    app = Application.builder().token(BOT_TOKEN).post_init(setup_commands).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("setname", set_name))
    app.add_handler(CommandHandler("setcode", set_code))
    app.add_handler(CommandHandler("setinsta", set_insta))
    app.add_handler(CommandHandler("add", add_photo))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("ban", ban))
    app.add_handler(CommandHandler("unban", unban))
    app.add_handler(CommandHandler("broadcast", broadcast))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, check_code))
    app.run_polling(drop_pending_updates=True)

if __name__=="__main__":
    main()
