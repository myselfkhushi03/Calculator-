import os, json, time, datetime
from threading import Thread
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand, BotCommandScopeDefault, BotCommandScopeChat
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
MAX_PHOTOS = 5

web = Flask(__name__)
@web.route('/')
def home(): return "Bot Alive"
def run_web(): web.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
Thread(target=run_web, daemon=True).start()

DATA_DIR = "/data" if os.path.exists("/data") else "."
USERS_FILE=os.path.join(DATA_DIR,"users.json")
BANNED_FILE=os.path.join(DATA_DIR,"banned.json")
SETTINGS_FILE=os.path.join(DATA_DIR,"settings.json")
ADMINS_FILE=os.path.join(DATA_DIR,"admins.json")
PHOTO_FOLDER=os.path.join(DATA_DIR,"photos")
os.makedirs(PHOTO_FOLDER, exist_ok=True)
PENDING_ADMIN_MSG = {}

def load(f):
    try: return json.load(open(f,"r"))
    except: return {}
def save(f,d): json.dump(d, open(f,"w"), indent=2)

DEFAULT_SETTINGS = {
    "name":"Khushi",
    "insta":"https://www.instagram.com/myselfkhushi03",
    "code":"6118588149",
    "font":"normal","timer":0,"group":True,"protect": True,
    "welcome":"Hey {user} 💖💖💖 ✨\n\nWelcome to {name}'s private vault 💌\n--------------------------------------------\n\nI'm {name}, so glad you're here!\n\nYou've found my exclusive collection 📸\nJust one step to unlock.\n\n👤 Your Name: {user}\n🆔 Your ID: {id}\n\n🔐 Send the secret code to unlock"
}

def get_settings():
    s=load(SETTINGS_FILE)
    if not s: s=DEFAULT_SETTINGS.copy(); save(SETTINGS_FILE,s)
    s.setdefault("protect", True)
    return s

def load_admins():
    admins = load(ADMINS_FILE)
    if not admins or "list" not in admins:
        admins = {"master": ADMIN_ID, "list": [ADMIN_ID] if ADMIN_ID!=0 else []}
        save(ADMINS_FILE, admins)
    if ADMIN_ID!=0 and ADMIN_ID not in admins["list"]:
        admins["list"].append(ADMIN_ID); save(ADMINS_FILE, admins)
    return admins

def is_admin(uid): return uid in load_admins().get("list", [])
def is_master(uid): return uid == ADMIN_ID

def premium_box(title, lines):
    box = f"📦 {title}\n━━━━━━━━━━━━━━━━━━\n"
    for l in lines: box += f"{l}\n"
    box += "━━━━━━━━━━━━━━━━━━"
    return box

def get_photos():
    return [os.path.join(PHOTO_FOLDER,x) for x in os.listdir(PHOTO_FOLDER) if x.lower().endswith(('.jpg','.jpeg','.png','.webp'))]

def is_banned(uid):
    b=load(BANNED_FILE)
    if str(uid) not in b: return False
    return True if b[str(uid)]=="perm" else time.time() < b[str(uid)]

def parse_time(t):
    if t in ["perm","permanent"]: return "perm"
    try:
        num=int(t[:-1]); unit=t[-1]
        if unit=="m": return time.time()+num*60
        if unit=="h": return time.time()+num*3600
        if unit=="d": return time.time()+num*86400
    except: return None

async def delete_job(context):
    try: await context.bot.delete_message(chat_id=context.job.chat_id, message_id=context.job.data)
    except: pass

# --- YE NAYA FUNCTION HAI MASTER KO NOTIFY KARNE KE LIYE ---
async def notify_master(context, admin_user, action, extra_lines):
    if admin_user.id == ADMIN_ID: return
    try:
        lines = [
            f"👤 Admin: {admin_user.first_name}",
            f"🆔 ID: {admin_user.id}",
            f"🔗 Username: @{admin_user.username or 'N/A'}",
            f"⚡ Action: {action}",
        ] + extra_lines
        await context.bot.send_message(chat_id=ADMIN_ID, text=premium_box("Admin Activity Log", lines))
    except: pass

async def refresh_commands_for_admin(bot, admin_id, is_master_user=False):
    cmds=[
        BotCommand("start","🚀 Start"),
        BotCommand("status","📊 Status"),
        BotCommand("setname","✏️ Name"),
        BotCommand("setcode","🔐 Code"),
        BotCommand("setinsta","🔗 Insta"),
        BotCommand("add","📸 Add 5 max"),
        BotCommand("clearphotos","🗑️ Clear all"),
    ]
    if is_master_user or admin_id==ADMIN_ID:
        cmds.extend([BotCommand("ban","🚫 Ban"),BotCommand("unban","✅ Unban"),BotCommand("addadmin","➕ Add admin"),BotCommand("removeadmin","➖ Remove admin")])
    try: await bot.set_my_commands(cmds, scope=BotCommandScopeChat(chat_id=admin_id))
    except: pass

async def setup_commands(app):
    await app.bot.set_my_commands([BotCommand("start","🚀 Start bot"),BotCommand("admin","📩 Contact admin")], scope=BotCommandScopeDefault())
    for aid in load_admins().get("list", []):
        await refresh_commands_for_admin(app.bot, aid, is_master_user=(aid==ADMIN_ID))

async def start(update, context):
    s=get_settings()
    if is_banned(update.effective_user.id): return
    uid=str(update.effective_user.id); users=load(USERS_FILE)
    if uid not in users:
        users[uid]={"name":update.effective_user.first_name, "username": update.effective_user.username or "N/A", "joined": datetime.datetime.now().strftime("%d-%m-%Y %H:%M"), "verified": False}
        save(USERS_FILE,users)
    welcome=s["welcome"].replace("{user}",update.effective_user.first_name).replace("{name}",s["name"]).replace("{id}",str(uid))
    btn=[[InlineKeyboardButton(f"📸 Follow {s['name']}", url=s["insta"])]]
    await update.message.reply_text(welcome, reply_markup=InlineKeyboardMarkup(btn), protect_content=s.get("protect", True))

async def check_code(update, context):
    if update.effective_user.id in PENDING_ADMIN_MSG:
        PENDING_ADMIN_MSG.pop(update.effective_user.id, None)
        for aid in load_admins().get("list", []):
            try: await context.bot.send_message(chat_id=aid, text=f"📩 New Msg\n👤 {update.effective_user.first_name}\n🆔 {update.effective_user.id}\n💬 {update.message.text}")
            except: pass
        await update.message.reply_text("✅ Message sent to admins 💌")
        return
    s=get_settings()
    if is_banned(update.effective_user.id): return
    if update.message.text.strip()!=s["code"]: return
    all_photos=get_photos()
    if len(all_photos)==0:
        await update.message.reply_text("📭 No photos yet!", protect_content=s.get("protect", True))
        return
    total=len(all_photos)
    await update.message.reply_text(f"✨ Access Granted! 💎 Sending {total} photos...", protect_content=s.get("protect", True))
    for i, p in enumerate(all_photos, 1):
        cap=f"For you, {update.effective_user.first_name} 💖 • {i}/{total}\nFrom: {s['name']} ✨"
        btn=[[InlineKeyboardButton(f"📸 Follow {s['name']}", url=s["insta"])]]
        await update.message.reply_photo(open(p,"rb"), caption=cap, reply_markup=InlineKeyboardMarkup(btn), protect_content=s.get("protect", True))

async def status(update, context):
    if not is_admin(update.effective_user.id): return
    s=get_settings()
    await update.message.reply_text(premium_box("Bot Status", [f"👑 {s['name']}", f"📸 {len(get_photos())}/{MAX_PHOTOS}"]))

async def add_photo(update, context):
    if not is_admin(update.effective_user.id): return
    if not update.message.reply_to_message or not update.message.reply_to_message.photo:
        await update.message.reply_text(f"📸 Reply to a photo with /add")
        return
    current=len(get_photos())
    if current>=MAX_PHOTOS:
        await update.message.reply_text(premium_box("Limit Reached", [f"❌ Max {MAX_PHOTOS} allowed", f"Use /clearphotos"]))
        return
    file=await update.message.reply_to_message.photo[-1].get_file()
    path=os.path.join(PHOTO_FOLDER, f"{int(time.time()*1000)}.jpg")
    await file.download_to_drive(path)
    await update.message.reply_text(premium_box("Photo Added - Premium", [f"✅ Added: {current+1}/{MAX_PHOTOS}"]))
    await notify_master(context, update.effective_user, "Photo Added", [f"📸 Total Now: {current+1}/{MAX_PHOTOS}"])

async def clear_photos(update, context):
    if not is_admin(update.effective_user.id): return
    photos=get_photos()
    if not photos:
        await update.message.reply_text("📭 No photos")
        return
    for p in photos:
        try: os.remove(p)
        except: pass
    await update.message.reply_text(premium_box("Photos Cleared", [f"🗑️ {len(photos)} deleted ✅"]))
    await notify_master(context, update.effective_user, "Clear Photos", [f"🗑️ Deleted: {len(photos)} photos", f"Now: 0/{MAX_PHOTOS}"])

async def set_name(update, context):
    if not is_admin(update.effective_user.id): return
    if not context.args: return
    new_name=" ".join(context.args)
    s=get_settings(); old=s["name"]; s["name"]=new_name; save(SETTINGS_FILE,s)
    await update.message.reply_text(premium_box("Updated", [f"Name: {new_name}"]))
    await notify_master(context, update.effective_user, "Set Name", [f"Old: {old}", f"New: {new_name}"])

async def set_code(update, context):
    if not is_admin(update.effective_user.id): return
    if not context.args: return
    s=get_settings(); old=s["code"]; s["code"]=context.args[0]; save(SETTINGS_FILE,s)
    await update.message.reply_text(premium_box("Updated", [f"Code: {s['code']}"]))
    await notify_master(context, update.effective_user, "Set Code", [f"Old: {old}", f"New: {s['code']}"])

async def set_insta(update, context):
    if not is_admin(update.effective_user.id): return
    if not context.args: return
    raw=context.args[0].replace("@",""); link=raw if "http" in raw else f"https://www.instagram.com/{raw.split('/')[-1]}"
    s=get_settings(); old=s["insta"]; s["insta"]=link; save(SETTINGS_FILE,s)
    await update.message.reply_text(premium_box("Updated", ["Insta set ✅"]))
    await notify_master(context, update.effective_user, "Set Insta", [f"Old: {old}", f"New: {link}"])

async def ban(update, context):
    if not is_master(update.effective_user.id): return
    if not context.args: return
    b=load(BANNED_FILE); b[str(context.args[0])]=parse_time(context.args[1] if len(context.args)>1 else "perm"); save(BANNED_FILE,b)
    await update.message.reply_text(premium_box("Banned", [f"🚫 {context.args[0]} banned ✅"]))

async def unban(update, context):
    if not is_master(update.effective_user.id): return
    if not context.args: return
    b=load(BANNED_FILE); b.pop(context.args[0],None); save(BANNED_FILE,b)
    await update.message.reply_text(premium_box("Unbanned", [f"✅ {context.args[0]} unbanned"]))

def main():
    app=Application.builder().token(BOT_TOKEN).post_init(setup_commands).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("add", add_photo))
    app.add_handler(CommandHandler("clearphotos", clear_photos))
    app.add_handler(CommandHandler("setname", set_name))
    app.add_handler(CommandHandler("setcode", set_code))
    app.add_handler(CommandHandler("setinsta", set_insta))
    app.add_handler(CommandHandler("ban", ban))
    app.add_handler(CommandHandler("unban", unban))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, check_code))
    print("Bot started with Master Log")
    app.run_polling(drop_pending_updates=True)

if __name__=="__main__": main()
