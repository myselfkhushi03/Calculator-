import json, os, time, random
from threading import Thread
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# --- WEB SERVER FOR RENDER FREE ---
web = Flask(__name__)
@web.route('/')
def home(): return "Bot is Alive @im_chikuuRobot - OK"
def run_web():
    web.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
Thread(target=run_web, daemon=True).start()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

USERS_FILE="users.json"; BANNED_FILE="banned.json"; SETTINGS_FILE="settings.json"
PHOTO_FOLDER="photos"; os.makedirs(PHOTO_FOLDER, exist_ok=True)
COPYRIGHT = "© @im_chikuuRobot"

def load(f):
    try: return json.load(open(f))
    except: return {}
def save(f,d): json.dump(d, open(f,"w"), indent=2)

def get_settings():
    s=load(SETTINGS_FILE)
    if not s:
        s={"name":"Khushi","insta":"https://instagram.com/","code":"6118588149","welcome":"Hey {user} ✨\n\nWelcome to {name}'s private vault 💌\n______________________________\n\nI'm {name}, so glad you're here!\n\nYou've found my exclusive collection 📸\nJust one step to unlock.\n\n👤 Your Name: {user}\n🆔 Your ID: {id}\n\n🔐 Send the secret code to unlock"}
        save(SETTINGS_FILE,s)
    return s

def get_photos(): return [os.path.join(PHOTO_FOLDER,x) for x in os.listdir(PHOTO_FOLDER) if x.lower().endswith(('.jpg','.jpeg','.png','.webp'))]
def is_banned(uid):
    b=load(BANNED_FILE)
    if str(uid) not in b: return False
    exp=b[str(uid)]
    if exp=="perm": return True
    if time.time()>exp: b.pop(str(uid)); save(BANNED_FILE,b); return False
    return True

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if is_banned(update.effective_user.id): return
    s=get_settings(); uid=str(update.effective_user.id); users=load(USERS_FILE)
    if uid not in users: users[uid]={"name":update.effective_user.first_name,"seen":[]}; save(USERS_FILE,users)
    welcome = s["welcome"].replace("{user}", update.effective_user.first_name).replace("{name}", s["name"]).replace("{id}", str(uid))
    btn = [[InlineKeyboardButton(f"📷 Follow {s['name']}", url=s["insta"])]]
    await update.message.reply_text(f"{welcome}\n\n{COPYRIGHT}", reply_markup=InlineKeyboardMarkup(btn))

async def check_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if is_banned(update.effective_user.id): return
    s=get_settings(); txt=update.message.text.strip()
    if txt==s["code"]:
        uid=str(update.effective_user.id); users=load(USERS_FILE)
        all_photos=get_photos(); seen=users.get(uid,{}).get("seen",[])
        available=[p for p in all_photos if p not in seen]
        if not available: available=all_photos; seen=[]
        if not available: await update.message.reply_text("No photos yet"); return
        photo=random.choice(available); seen.append(photo); users[uid]["seen"]=seen; save(USERS_FILE,users)
        await update.message.reply_text(f"Yayy! Access granted ✅\nSending photos from {s['name']}...\n\n{COPYRIGHT}")
        await update.message.reply_photo(open(photo,"rb"))
    elif txt.isdigit() and len(txt)>=4:
        await update.message.reply_text(f"Oops! Wrong code 🥺 Try again\n\n{COPYRIGHT}")

async def set_name(update, context):
    if update.effective_user.id!=ADMIN_ID: return
    s=get_settings(); s["name"]=" ".join(context.args); save(SETTINGS_FILE,s); await update.message.reply_text(f"Name -> {s['name']}")
async def set_code(update, context):
    if update.effective_user.id!=ADMIN_ID: return
    s=get_settings(); s["code"]=context.args[0]; save(SETTINGS_FILE,s); await update.message.reply_text(f"Code -> {s['code']}")
async def set_insta(update, context):
    if update.effective_user.id!=ADMIN_ID: return
    s=get_settings(); s["insta"]=context.args[0]; save(SETTINGS_FILE,s); await update.message.reply_text("Insta OK")
async def add_photo(update, context):
    if update.effective_user.id!=ADMIN_ID: return
    if not update.message.reply_to_message or not update.message.reply_to_message.photo: await update.message.reply_text("Reply to photo with /add"); return
    file=await update.message.reply_to_message.photo[-1].get_file()
    await file.download_to_drive(os.path.join(PHOTO_FOLDER, f"{int(time.time())}.jpg"))
    await update.message.reply_text(f"Added Total {len(get_photos())}")
async def status(update, context):
    if update.effective_user.id!=ADMIN_ID: return
    s=get_settings(); await update.message.reply_text(f"Name:{s['name']}\nCode:{s['code']}\nPhotos:{len(get_photos())}\nUsers:{len(load(USERS_FILE))}\n\n{COPYRIGHT}")

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("setname", set_name))
    app.add_handler(CommandHandler("setcode", set_code))
    app.add_handler(CommandHandler("setinsta", set_insta))
    app.add_handler(CommandHandler("add", add_photo))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("photos", status))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, check_code))
    print("Bot started @im_chikuuRobot")
    app.run_polling()

if __name__=="__main__": main()
