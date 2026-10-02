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
        s={"name":"Khushi","insta":"https://www.instagram.com/myselfkhushi03","code":"6118588149","font":"normal","timer":0,"group":True,"welcome":"Hey {user} ✨\n\nWelcome to {name}'s private vault 💌\n______________________________\n\nI'm {name}, so glad you're here!\n\nYou've found my exclusive collection 📸\nJust one step to unlock.\n\n👤 Your Name: {user}\n🆔 Your ID: {id}\n\n🔐 Send the secret code to unlock"}
        save(SETTINGS_FILE,s)
    s.setdefault("font","normal"); s.setdefault("timer",0); s.setdefault("group",True)
    return s

SMALL_MAP = {
    'A':'ᴀ','B':'ʙ','C':'ᴄ','D':'ᴅ','E':'ᴇ','F':'ꜰ','G':'ɢ','H':'ʜ','I':'ɪ','J':'ᴊ','K':'ᴋ','L':'ʟ','M':'ᴍ','N':'ɴ','O':'ᴏ','P':'ᴘ','Q':'ǫ','R':'ʀ','S':'ꜱ','T':'ᴛ','U':'ᴜ','V':'ᴠ','W':'ᴡ','X':'x','Y':'ʏ','Z':'ᴢ',
    'a':'ᴀ','b':'ʙ','c':'ᴄ','d':'ᴅ','e':'ᴇ','f':'ꜰ','g':'ɢ','h':'ʜ','i':'ɪ','j':'ᴊ','k':'ᴋ','l':'ʟ','m':'ᴍ','n':'ɴ','o':'ᴏ','p':'ᴘ','q':'ǫ','r':'ʀ','s':'ꜱ','t':'ᴛ','u':'ᴜ','v':'ᴠ','w':'ᴡ','x':'x','y':'ʏ','z':'ᴢ',
}
def apply_font(text, font_type):
    if font_type=="small": return "".join(SMALL_MAP.get(c,c) for c in text)
    return text

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

def parse_timer_str(s):
    # 1m, 5m, 30s, 1h, 2d, 0
    s=s.lower().strip()
    if s=="0" or s=="off": return 0
    try:
        if s[-1]=="s": return max(1, int(s[:-1])) # seconds
        if s[-1]=="m": return int(s[:-1])*60
        if s[-1]=="h": return int(s[:-1])*3600
        if s[-1]=="d": return int(s[:-1])*86400
        return int(s)*60 # sirf number likha to minute samjho
    except: return None

def format_timer(sec):
    if sec<60: return f"{sec}s"
    if sec<3600: return f"{sec//60}m"
    if sec<86400: return f"{sec//3600}h"
    return f"{sec//86400}d"

async def delete_job(context: ContextTypes.DEFAULT_TYPE):
    try: await context.bot.delete_message(chat_id=context.job.chat_id, message_id=context.job.data)
    except: pass

async def setup_commands(app: Application):
    await app.bot.set_my_commands([BotCommand("start", "Start the bot")], scope=BotCommandScopeDefault())
    if ADMIN_ID!=0:
        admin_cmds = [
            BotCommand("start", "Start bot"),
            BotCommand("setname", "Change name"),
            BotCommand("setcode", "Change secret code"),
            BotCommand("setinsta", "Change insta link"),
            BotCommand("setfont", "Change font: normal / small"),
            BotCommand("settimer", "Timer: /settimer 1m / 5m / 1h / 0=off"),
            BotCommand("add", "Add: /add or /add 1m / 5m"),
            BotCommand("group", "Group on/off"),
            BotCommand("status", "Check status"),
            BotCommand("ban", "Ban user"),
            BotCommand("unban", "Unban user"),
            BotCommand("broadcast", "Send all or ID"),
        ]
        await app.bot.set_my_commands(admin_cmds, scope=BotCommandScopeChat(chat_id=ADMIN_ID))

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    s=get_settings()
    if update.effective_chat.type in ["group","supergroup"] and not s.get("group",True): return
    if is_banned(update.effective_user.id): return
    uid=str(update.effective_user.id)
    users=load(USERS_FILE)
    if uid not in users:
        users[uid]={"name":update.effective_user.first_name}; save(USERS_FILE,users)
    welcome_raw = s["welcome"].replace("{user}", update.effective_user.first_name).replace("{name}", s["name"]).replace("{id}", str(uid))
    welcome = apply_font(welcome_raw, s.get("font","normal"))
    btn = [[InlineKeyboardButton(f"📷 Follow {s['name']}", url=s["insta"])]]
    await update.message.reply_text(welcome, reply_markup=InlineKeyboardMarkup(btn), protect_content=True)

async def check_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    s=get_settings()
    if update.effective_chat.type in ["group","supergroup"] and not s.get("group",True): return
    if is_banned(update.effective_user.id): return
    txt=update.message.text.strip()
    if txt==s["code"]:
        all_photos=get_photos()
        if not all_photos:
            await update.message.reply_text("No photos yet", protect_content=True); return
        to_send = random.sample(all_photos, min(2, len(all_photos)))
        timer_sec = s.get("timer",0)
        msg = await update.message.reply_text(f"Yayy! Access granted ✅", protect_content=True)
        if timer_sec>0:
            context.job_queue.run_once(delete_job, timer_sec, chat_id=update.effective_chat.id, data=msg.message_id)
        for i, p in enumerate(to_send, 1):
            cap_raw = f"For you, {update.effective_user.first_name} 💖 • {i}/{len(to_send)}\nFrom: {s['name']} ✨"
            cap = apply_font(cap_raw, s.get("font","normal"))
            btn = [[InlineKeyboardButton(f"📷 Follow {s['name']}", url=s["insta"])]]
            sent = await update.message.reply_photo(open(p,"rb"), caption=cap, reply_markup=InlineKeyboardMarkup(btn), protect_content=True)
            if timer_sec>0:
                context.job_queue.run_once(delete_job, timer_sec, chat_id=update.effective_chat.id, data=sent.message_id)
        if timer_sec>0:
            await update.message.reply_text(f"⏳ Photos auto delete in {format_timer(timer_sec)}", protect_content=True)
    elif txt.isdigit() and len(txt)>=4:
        await update.message.reply_text("Oops! Wrong code 😑", protect_content=True)

async def set_name(update, context):
    if update.effective_user.id!=ADMIN_ID: return
    if not context.args: await update.message.reply_text("Use: /setname Khushi", parse_mode="Markdown"); return
    s=get_settings(); s["name"]=" ".join(context.args); save(SETTINGS_FILE,s)
    await update.message.reply_text(f"✅ Name -> {s['name']}")

async def set_code(update, context):
    if update.effective_user.id!=ADMIN_ID: return
    if not context.args: await update.message.reply_text("Use: /setcode 1234", parse_mode="Markdown"); return
    s=get_settings(); s["code"]=context.args[0]; save(SETTINGS_FILE,s)
    await update.message.reply_text(f"✅ Code -> {s['code']}")

async def set_insta(update, context):
    if update.effective_user.id!=ADMIN_ID: return
    if not context.args: await update.message.reply_text("Use: /setinsta LINK", parse_mode="Markdown"); return
    s=get_settings(); s["insta"]=context.args[0]; save(SETTINGS_FILE,s)
    await update.message.reply_text("✅ Insta updated")

async def set_font(update, context):
    if update.effective_user.id!=ADMIN_ID: return
    if not context.args: await update.message.reply_text("Use: /setfont normal or /setfont small", parse_mode="Markdown"); return
    font = context.args[0].lower()
    if font not in ["normal","small"]: await update.message.reply_text("Use: normal / small"); return
    s=get_settings(); s["font"]=font; save(SETTINGS_FILE,s)
    await update.message.reply_text(f"✅ Font -> {font}")

async def set_timer(update, context):
    if update.effective_user.id!=ADMIN_ID: return
    if not context.args:
        await update.message.reply_text("⏱️ Use:\n`/settimer 1m` - 1 min\n`/settimer 5m` - 5 min\n`/settimer 30s` - 30 sec\n`/settimer 1h` - 1 hour\n`/settimer 0` - off", parse_mode="Markdown"); return
    sec = parse_timer_str(context.args[0])
    if sec is None: await update.message.reply_text("Galat format! Use: 1m, 5m, 30s, 1h"); return
    s=get_settings(); s["timer"]=sec; save(SETTINGS_FILE,s)
    if sec==0: await update.message.reply_text("✅ Timer OFF")
    else: await update.message.reply_text(f"✅ Timer set {format_timer(sec)}")

async def set_group(update, context):
    if update.effective_user.id!=ADMIN_ID: return
    if not context.args:
        s=get_settings(); st="ON" if s.get("group",True) else "OFF"
        await update.message.reply_text(f"Group: {st}\nUse: /group on / off", parse_mode="Markdown"); return
    val=context.args[0].lower(); s=get_settings()
    if val=="on": s["group"]=True; save(SETTINGS_FILE,s); await update.message.reply_text("✅ Group ON")
    elif val=="off": s["group"]=False; save(SETTINGS_FILE,s); await update.message.reply_text("✅ Group OFF")
    else: await update.message.reply_text("Use: /group on / off")

async def add_photo(update, context):
    if update.effective_user.id!=ADMIN_ID: return
    if not update.message.reply_to_message or not update.message.reply_to_message.photo:
        await update.message.reply_text("Photo pe reply karke:\n`/add` - normal\n`/add 1m` - 1 min timer\n`/add 5m` - 5 min\n`/add 1h` - 1 hour", parse_mode="Markdown"); return
    sec=None
    if context.args:
        sec=parse_timer_str(context.args[0])
    file=await update.message.reply_to_message.photo[-1].get_file()
    await file.download_to_drive(os.path.join(PHOTO_FOLDER, f"{int(time.time())}.jpg"))
    s=get_settings()
    if sec and sec>0:
        s["timer"]=sec; save(SETTINGS_FILE,s)
        await update.message.reply_text(f"✅ Added + Timer {format_timer(sec)} set! Total: {len(get_photos())}")
    else:
        await update.message.reply_text(f"✅ Added! Total: {len(get_photos())} Timer: {format_timer(s.get('timer',0)) if s.get('timer',0)>0 else 'OFF'}")

async def status(update, context):
    if update.effective_user.id!=ADMIN_ID: return
    s=get_settings()
    timer_txt = format_timer(s.get('timer',0)) if s.get('timer',0)>0 else "OFF"
    await update.message.reply_text(f"Name:{s['name']}\nCode:{s['code']}\nFont:{s['font']}\nTimer:{timer_txt}\nGroup:{'ON' if s['group'] else 'OFF'}\nPhotos:{len(get_photos())}\nUsers:{len(load(USERS_FILE))}")

async def ban(update, context):
    if update.effective_user.id!=ADMIN_ID: return
    if len(context.args)<1: await update.message.reply_text("Use: /ban ID 1d/perm", parse_mode="Markdown"); return
    uid=context.args[0]; dur=context.args[1] if len(context.args)>1 else "perm"
    exp=parse_time(dur)
    if not exp: await update.message.reply_text("Time: 1d,2d,perm"); return
    b=load(BANNED_FILE); b[uid]=exp; save(BANNED_FILE,b)
    await update.message.reply_text(f"✅ Banned {uid} for {dur}")

async def unban(update, context):
    if update.effective_user.id!=ADMIN_ID: return
    if len(context.args)<1: await update.message.reply_text("Use: /unban ID", parse_mode="Markdown"); return
    b=load(BANNED_FILE); b.pop(context.args[0],None); save(BANNED_FILE,b)
    await update.message.reply_text(f"✅ Unbanned {context.args[0]}")

async def broadcast(update, context):
    if update.effective_user.id!=ADMIN_ID: return
    users = load(USERS_FILE)
    if not context.args and not update.message.reply_to_message:
        await update.message.reply_text("Use: /broadcast all hi or /broadcast ID hi", parse_mode="Markdown"); return
    target = context.args[0].lower() if context.args else "all"
    if update.message.reply_to_message:
        msg = update.message.reply_to_message
        if target == "all":
            count=0
            for uid in users.keys():
                try: await msg.copy(chat_id=int(uid), protect_content=True); count+=1
                except: pass
            await update.message.reply_text(f"✅ Done {count}")
        else:
            try: await msg.copy(chat_id=int(target), protect_content=True); await update.message.reply_text(f"✅ Sent to {target}")
            except Exception as e: await update.message.reply_text(f"❌ {e}")
        return
    if target == "all":
        text = " ".join(context.args[1:])
        if not text: await update.message.reply_text("Msg likh"); return
        count=0
        for uid in users.keys():
            try: await context.bot.send_message(chat_id=int(uid), text=text, protect_content=True); count+=1
            except: pass
        await update.message.reply_text(f"✅ Done {count}")
    else:
        try:
            uid = int(target); text = " ".join(context.args[1:])
            if not text: await update.message.reply_text("Msg likh"); return
            await context.bot.send_message(chat_id=uid, text=text, protect_content=True)
            await update.message.reply_text(f"✅ Sent to {uid}")
        except: await update.message.reply_text("ID galat")

def main():
    app = Application.builder().token(BOT_TOKEN).post_init(setup_commands).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("setname", set_name))
    app.add_handler(CommandHandler("setcode", set_code))
    app.add_handler(CommandHandler("setinsta", set_insta))
    app.add_handler(CommandHandler("setfont", set_font))
    app.add_handler(CommandHandler("settimer", set_timer))
    app.add_handler(CommandHandler("group", set_group))
    app.add_handler(CommandHandler("add", add_photo))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("ban", ban))
    app.add_handler(CommandHandler("unban", unban))
    app.add_handler(CommandHandler("broadcast", broadcast))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, check_code))
    app.run_polling(drop_pending_updates=True)

if __name__=="__main__":
    main()
