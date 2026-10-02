import json, os, time, random, asyncio
from threading import Thread
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

# --- KEEP ALIVE FOR RENDER FREE WEB SERVICE ---
web = Flask(__name__)
@web.route('/')
def home(): return "Bot is Alive @im_chikuuRobot - OK"
def run_web(): web.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
Thread(target=run_web, daemon=True).start()

# --- CONFIG ---
MAIN_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

USERS_FILE="users.json"; BANNED_FILE="banned.json"; SETTINGS_FILE="settings.json"; CLONES_FILE="clones.json"
PHOTO_FOLDER="photos"; os.makedirs(PHOTO_FOLDER, exist_ok=True)

COPYRIGHT = "© @im_chikuuRobot"

DEFAULT_WELCOME = """Hey {user} ✨

Welcome to {name}'s private vault 💌
______________________________

I'm {name}, so glad you're here!

You've found my exclusive collection 📸
Just one step to unlock.

👤 Your Name: {user}
🆔 Your ID: {id}

🔐 Send the secret code to unlock"""

WRONG_MSG = "Oops! Wrong code 🥺 Try again"
SUCCESS_MSG = "Yayy! Access granted ✅\nSending photos from {name}..."

def load(f):
    try: return json.load(open(f,"r"))
    except: return {}
def save(f,d): json.dump(d, open(f,"w"), indent=2)

def get_settings():
    s=load(SETTINGS_FILE)
    if not s:
        s={"name":"Khushi","insta":"https://instagram.com/","code":"6118588149","welcome":DEFAULT_WELCOME}
        save(SETTINGS_FILE,s)
    if "welcome" not in s: s["welcome"]=DEFAULT_WELCOME
    return s

def get_photos():
    return [os.path.join(PHOTO_FOLDER,x) for x in os.listdir(PHOTO_FOLDER) if x.lower().endswith(('.jpg','.jpeg','.png','.webp'))]

def parse_time(t):
    if t=="perm": return "perm"
    try:
        num=int(t[:-1]); unit=t[-1]
        if unit=="m": return time.time()+num*60
        if unit=="h": return time.time()+num*3600
        if unit=="d": return time.time()+num*86400
    except: return None

def is_banned(uid):
    b=load(BANNED_FILE)
    if str(uid) not in b: return False
    exp=b[str(uid)]
    if exp=="perm": return True
    if time.time()>exp:
        b.pop(str(uid)); save(BANNED_FILE,b); return False
    return True

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if is_banned(update.effective_user.id): return
    s=get_settings(); uid=str(update.effective_user.id)
    users=load(USERS_FILE)
    if uid not in users:
        users[uid]={"name":update.effective_user.first_name,"seen":[]}; save(USERS_FILE,users)
    welcome = s["welcome"].replace("{user}", update.effective_user.first_name).replace("{name}", s["name"]).replace("{id}", str(update.effective_user.id))
    welcome = f"{welcome}\n\n{COPYRIGHT}"
    btn = [[InlineKeyboardButton(f"📷 Follow {s['name']}", url=s["insta"])]]
    await update.message.reply_text(welcome, reply_markup=InlineKeyboardMarkup(btn))

async def check_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if is_banned(update.effective_user.id): return
    s=get_settings(); txt=update.message.text.strip()
    if txt==s["code"]:
        uid=str(update.effective_user.id); users=load(USERS_FILE)
        all_photos=get_photos(); seen=users.get(uid,{}).get("seen",[])
        available=[p for p in all_photos if p not in seen]
        if not available: available=all_photos; seen=[]
        if not available: await update.message.reply_text("No photos added yet."); return
        photo=random.choice(available); seen.append(photo); users[uid]["seen"]=seen; save(USERS_FILE,users)
        await update.message.reply_text(f"{SUCCESS_MSG.replace('{name}', s['name'])}\n\n{COPYRIGHT}")
        await update.message.reply_photo(photo=open(photo,"rb"))
    else:
        if txt.isdigit() and len(txt)>=4:
            await update.message.reply_text(f"{WRONG_MSG}\n\n{COPYRIGHT}")

# ADMIN ONLY
async def set_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id!=ADMIN_ID: return
    s=get_settings(); s["name"]=" ".join(context.args); save(SETTINGS_FILE,s)
    await update.message.reply_text(f"Name changed -> {s['name']} ✅")
async def set_insta(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id!=ADMIN_ID: return
    s=get_settings(); s["insta"]=context.args[0]; save(SETTINGS_FILE,s)
    await update.message.reply_text("Insta changed ✅")
async def set_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id!=ADMIN_ID: return
    s=get_settings(); s["code"]=context.args[0]; save(SETTINGS_FILE,s)
    await update.message.reply_text(f"Code -> {s['code']} ✅")
async def set_welcome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id!=ADMIN_ID: return
    s=get_settings()
    if not context.args: await update.message.reply_text("Use: /setwelcome default"); return
    if context.args[0].lower()=="default":
        s["welcome"]=DEFAULT_WELCOME; save(SETTINGS_FILE,s); await update.message.reply_text("Default welcome set ✅"); return
    s["welcome"]=" ".join(context.args); save(SETTINGS_FILE,s); await update.message.reply_text("Custom welcome set ✅")
async def add_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id!=ADMIN_ID: return
    if not update.message.reply_to_message or not update.message.reply_to_message.photo:
        await update.message.reply_text("Reply to photo with /add"); return
    file=await update.message.reply_to_message.photo[-1].get_file()
    await file.download_to_drive(os.path.join(PHOTO_FOLDER, f"{int(time.time())}.jpg"))
    await update.message.reply_text(f"Added ✅ Total {len(get_photos())}")
async def ban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id!=ADMIN_ID: return
    exp=parse_time(context.args[1] if len(context.args)>1 else "perm")
    b=load(BANNED_FILE); b[context.args[0]]=exp; save(BANNED_FILE,b); await update.message.reply_text("Banned ✅")
async def unban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id!=ADMIN_ID: return
    b=load(BANNED_FILE); b.pop(context.args[0],None); save(BANNED_FILE,b); await update.message.reply_text("Unbanned ✅")
async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id!=ADMIN_ID: return
    s=get_settings(); await update.message.reply_text(f"Name:{s['name']}\nCode:{s['code']}\nPhotos:{len(get_photos())}\nUsers:{len(load(USERS_FILE))}\n\n{COPYRIGHT}")
async def clone_bot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id!=ADMIN_ID: return
    clones=load(CLONES_FILE); clones[context.args[0]]=True; save(CLONES_FILE,clones)
    asyncio.create_task(run_bot(context.args[0])); await update.message.reply_text(f"Cloned ✅\n{COPYRIGHT}")

def get_handlers():
    return [CommandHandler("start",start),CommandHandler("setname",set_name),CommandHandler("setinsta",set_insta),CommandHandler("setcode",set_code),CommandHandler("setwelcome",set_welcome),CommandHandler("add",add_photo),CommandHandler("status",status),CommandHandler("photos",status),CommandHandler("ban",ban),CommandHandler("unban",unban),CommandHandler("clone",clone_bot),MessageHandler(filters.TEXT & ~filters.COMMAND, check_code)]

async def run_bot(token):
    app=Application.builder().token(token).build()
    for h in get_handlers(): app.add_handler(h)
    await app.initialize(); await app.start(); await app.updater.start_polling()

async def main():
    for tok in load(CLONES_FILE): asyncio.create_task(run_bot(tok))
    app=Application.builder().token(MAIN_TOKEN).build()
    for h in get_handlers(): app.add_handler(h)
    await app.initialize(); await app.start(); await app.updater.start_polling()
    await asyncio.Event().wait()

if __name__=="__main__": asyncio.run(main())
