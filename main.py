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

SMALL_MAP = {'A':'ᴀ','B':'ʙ','C':'ᴄ','D':'ᴅ','E':'ᴇ','F':'ꜰ','G':'ɢ','H':'ʜ','I':'ɪ','J':'ᴊ','K':'ᴋ','L':'ʟ','M':'ᴍ','N':'ɴ','O':'ᴏ','P':'ᴘ','Q':'ǫ','R':'ʀ','S':'ꜱ','T':'ᴛ','U':'ᴜ','V':'ᴠ','W':'ᴡ','X':'x','Y':'ʏ','Z':'ᴢ','a':'ᴀ','b':'ʙ','c':'ᴄ','d':'ᴅ','e':'ᴇ','f':'ꜰ','g':'ɢ','h':'ʜ','i':'ɪ','j':'ᴊ','k':'ᴋ','l':'ʟ','m':'ᴍ','n':'ɴ','o':'ᴏ','p':'ᴘ','q':'ǫ','r':'ʀ','s':'ꜱ','t':'ᴛ','u':'ᴜ','v':'ᴠ','w':'ᴡ','x':'x','y':'ʏ','z':'ᴢ'}
def apply_font(t, f): return "".join(SMALL_MAP.get(c,c) for c in t) if f=="small" else t

def get_photos():
    if not os.path.exists(PHOTO_FOLDER): os.makedirs(PHOTO_FOLDER, exist_ok=True)
    return [os.path.join(PHOTO_FOLDER,x) for x in os.listdir(PHOTO_FOLDER) if x.lower().endswith(('.jpg','.jpeg','.png','.webp'))]

def is_banned(uid):
    b=load(BANNED_FILE)
    if str(uid) not in b: return False
    exp=b[str(uid)]
    if exp=="perm": return True
    if time.time()>exp: b.pop(str(uid)); save(BANNED_FILE,b); return False
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
    s=s.lower().strip()
    if s=="0" or s=="off": return 0
    try:
        if s[-1]=="s": return max(5, int(s[:-1]))
        if s[-1]=="m": return int(s[:-1])*60
        if s[-1]=="h": return int(s[:-1])*3600
        if s[-1]=="d": return int(s[:-1])*86400
        return int(s)*60
    except: return None

def format_timer(sec):
    if sec==0: return "OFF"
    if sec<60: return f"{sec}s"
    if sec<3600: return f"{sec//60}m"
    return f"{sec//3600}h"

async def delete_job(context):
    try: await context.bot.delete_message(chat_id=context.job.chat_id, message_id=context.job.data)
    except: pass

async def setup_commands(app):
    await app.bot.set_my_commands([BotCommand("start", "Start")], scope=BotCommandScopeDefault())
    if ADMIN_ID!=0:
        cmds=[BotCommand("start","Start bot"),BotCommand("setname","Change name"),BotCommand("setcode","Change code"),BotCommand("setinsta","Set insta: username only"),BotCommand("setfont","Font: normal/small"),BotCommand("settimer","Timer: 1m/5m/0=off"),BotCommand("settime","Timer alias 1m/5m"),BotCommand("add","Add photo: /add or /add 1m"),BotCommand("group","Group on/off"),BotCommand("status","Check status"),BotCommand("ban","Ban user"),BotCommand("unban","Unban user"),BotCommand("broadcast","Broadcast all or ID")]
        await app.bot.set_my_commands(cmds, scope=BotCommandScopeChat(chat_id=ADMIN_ID))

async def start(update, context):
    s=get_settings()
    if update.effective_chat.type in ["group","supergroup"] and not s.get("group",True): return
    if is_banned(update.effective_user.id): return
    uid=str(update.effective_user.id); users=load(USERS_FILE)
    if uid not in users: users[uid]={"name":update.effective_user.first_name}; save(USERS_FILE,users)
    welcome_raw=s["welcome"].replace("{user}",update.effective_user.first_name).replace("{name}",s["name"]).replace("{id}",str(uid))
    welcome=apply_font(welcome_raw,s.get("font","normal"))
    btn=[[InlineKeyboardButton(f"Follow {s['name']}", url=s["insta"])]]
    await update.message.reply_text(welcome, reply_markup=InlineKeyboardMarkup(btn), protect_content=True)

async def check_code(update, context):
    s=get_settings()
    if update.effective_chat.type in ["group","supergroup"] and not s.get("group",True): return
    if is_banned(update.effective_user.id): return
    txt=update.message.text.strip()
    if txt!=s["code"]:
        if txt.isdigit() and len(txt)>=4: await update.message.reply_text("Wrong code! Try again 🥺", protect_content=True)
        return

    all_photos=get_photos()
    if len(all_photos)==0:
        await update.message.reply_text(f"No photos added yet! Use /add to add photos. Timer: {format_timer(s.get('timer',0))}", protect_content=True)
        return

    timer_sec=s.get("timer",0)
    to_send=random.sample(all_photos, min(2, len(all_photos)))

    await update.message.reply_text(f"Access granted! Sending {len(to_send)} photos from {s['name']}...", protect_content=True)

    for i,p in enumerate(to_send,1):
        cap=apply_font(f"For you, {update.effective_user.first_name} - {i}/{len(to_send)}\nFrom: {s['name']}", s.get("font","normal"))
        btn=[[InlineKeyboardButton(f"Follow {s['name']}", url=s["insta"])]]
        sent=await update.message.reply_photo(open(p,"rb"), caption=cap, reply_markup=InlineKeyboardMarkup(btn), protect_content=True)
        if timer_sec>0 and context.job_queue:
            try: context.job_queue.run_once(delete_job, timer_sec, chat_id=update.effective_chat.id, data=sent.message_id)
            except: pass

    if timer_sec>0:
        await update.message.reply_text(f"Auto delete in {format_timer(timer_sec)}", protect_content=True)

async def set_name(update, context):
    if update.effective_user.id!=ADMIN_ID: return
    if not context.args: await update.message.reply_text("Usage: /setname YourName"); return
    s=get_settings(); s["name"]=" ".join(context.args); save(SETTINGS_FILE,s); await update.message.reply_text(f"Name updated to {s['name']}")

async def set_code(update, context):
    if update.effective_user.id!=ADMIN_ID: return
    if not context.args: await update.message.reply_text("Usage: /setcode 1234"); return
    s=get_settings(); s["code"]=context.args[0]; save(SETTINGS_FILE,s); await update.message.reply_text(f"Code updated to {s['code']}")

async def set_insta(update, context):
    if update.effective_user.id!=ADMIN_ID: return
    if not context.args:
        await update.message.reply_text("Usage:\n/setinsta myselfkhushi03 - just username\n/setinsta @myselfkhushi03\n/setinsta https://instagram.com/myselfkhushi03")
        return
    raw = context.args[0].strip().replace("@","")
    if "instagram.com" in raw or "http" in raw:
        link = raw
        if not link.startswith("http"):
            link = "https://" + link
    else:
        username = raw.split("/")[-1].replace("@","")
        link = f"https://www.instagram.com/{username}"
    s=get_settings(); s["insta"]=link; save(SETTINGS_FILE,s)
    await update.message.reply_text(f"Instagram updated to {s['insta']}")

async def set_font(update, context):
    if update.effective_user.id!=ADMIN_ID: return
    if not context.args: await update.message.reply_text("Usage: /setfont normal or /setfont small"); return
    f=context.args[0].lower()
    if f not in ["normal","small"]: await update.message.reply_text("Use normal or small"); return
    s=get_settings(); s["font"]=f; save(SETTINGS_FILE,s); await update.message.reply_text(f"Font updated to {f}")

async def set_timer(update, context):
    if update.effective_user.id!=ADMIN_ID: return
    if not context.args:
        s=get_settings()
        await update.message.reply_text(f"Current timer: {format_timer(s.get('timer',0))}\n\nUsage:\n/settime 1m - 1 minute\n/settime 5m - 5 minutes\n/settime 30s - 30 seconds\n/settime 1h - 1 hour\n/settime 0 - OFF"); return
    sec=parse_timer_str(context.args[0])
    if sec is None: await update.message.reply_text("Invalid format! Use: 1m, 5m, 30s, 1h, 0"); return
    s=get_settings(); s["timer"]=sec; save(SETTINGS_FILE,s)
    await update.message.reply_text(f"Timer set to {format_timer(sec)}")

async def set_group(update, context):
    if update.effective_user.id!=ADMIN_ID: return
    if not context.args:
        s=get_settings(); st="ON" if s.get("group",True) else "OFF"
        await update.message.reply_text(f"Group mode is {st}\n/group on - Enable\n/group off - Disable"); return
    val=context.args[0].lower(); s=get_settings()
    if val=="on": s["group"]=True; save(SETTINGS_FILE,s); await update.message.reply_text("Group mode ON")
    else: s["group"]=False; save(SETTINGS_FILE,s); await update.message.reply_text("Group mode OFF")

async def add_photo(update, context):
    if update.effective_user.id!=ADMIN_ID: return
    if not update.message.reply_to_message or not update.message.reply_to_message.photo:
        await update.message.reply_text("Reply to a photo with:\n/add - Add normally\n/add 1m - Add with 1 min timer"); return
    sec=None
    if context.args: sec=parse_timer_str(context.args[0])
    file=await update.message.reply_to_message.photo[-1].get_file()
    path=os.path.join(PHOTO_FOLDER, f"{int(time.time()*1000)}.jpg")
    await file.download_to_drive(path)
    s=get_settings()
    if sec is not None:
        s["timer"]=sec; save(SETTINGS_FILE,s)
        await update.message.reply_text(f"Photo added with timer {format_timer(sec)}! Total: {len(get_photos())}")
    else:
        await update.message.reply_text(f"Photo added! Total: {len(get_photos())} Timer: {format_timer(s.get('timer',0))}")

async def status(update, context):
    if update.effective_user.id!=ADMIN_ID: return
    s=get_settings()
    await update.message.reply_text(f"STATUS\n\nName: {s['name']}\nInsta: {s['insta']}\nCode: {s['code']}\nFont: {s['font']}\nTimer: {format_timer(s.get('timer',0))}\nGroup: {'ON' if s['group'] else 'OFF'}\nPhotos: {len(get_photos())}\nUsers: {len(load(USERS_FILE))}\nBanned: {len(load(BANNED_FILE))}")

async def ban(update, context):
    if update.effective_user.id!=ADMIN_ID: return
    if not context.args: await update.message.reply_text("Usage: /ban USER_ID 1d/2d/perm"); return
    uid=context.args[0]; dur=context.args[1] if len(context.args)>1 else "perm"
    exp=parse_time(dur); b=load(BANNED_FILE); b[uid]=exp; save(BANNED_FILE,b); await update.message.reply_text(f"User {uid} banned for {dur}")

async def unban(update, context):
    if update.effective_user.id!=ADMIN_ID: return
    if not context.args: await update.message.reply_text("Usage: /unban USER_ID"); return
    b=load(BANNED_FILE); b.pop(context.args[0],None); save(BANNED_FILE,b); await update.message.reply_text(f"User {context.args[0]} unbanned")

async def broadcast(update, context):
    if update.effective_user.id!=ADMIN_ID: return
    users=load(USERS_FILE)
    if not context.args and not update.message.reply_to_message: await update.message.reply_text("Usage:\n/broadcast all Your message"); return
    target=context.args[0].lower() if context.args else "all"
    if update.message.reply_to_message:
        msg=update.message.reply_to_message
        if target=="all":
            c=0
            for uid in users:
                try: await msg.copy(chat_id=int(uid), protect_content=True); c+=1
                except: pass
            await update.message.reply_text(f"Broadcast done to {c} users")
        else:
            try: await msg.copy(chat_id=int(target), protect_content=True); await update.message.reply_text(f"Sent to {target}")
            except Exception as e: await update.message.reply_text(f"Failed: {e}")
        return
    if target=="all":
        text=" ".join(context.args[1:])
        if not text: await update.message.reply_text("Usage: /broadcast all Hello"); return
        c=0
        for uid in users:
            try: await context.bot.send_message(chat_id=int(uid), text=text, protect_content=True); c+=1
            except: pass
        await update.message.reply_text(f"Broadcast done to {c} users")
    else:
        try:
            uid=int(target); text=" ".join(context.args[1:])
            if not text: await update.message.reply_text("Usage: /broadcast USER_ID message"); return
            await context.bot.send_message(chat_id=uid, text=text, protect_content=True)
            await update.message.reply_text(f"Sent to {uid}")
        except: await update.message.reply_text("Invalid ID")

def main():
    app=Application.builder().token(BOT_TOKEN).post_init(setup_commands).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("setname", set_name))
    app.add_handler(CommandHandler("setcode", set_code))
    app.add_handler(CommandHandler("setinsta", set_insta))
    app.add_handler(CommandHandler("setfont", set_font))
    app.add_handler(CommandHandler("settimer", set_timer))
    app.add_handler(CommandHandler("settime", set_timer))
    app.add_handler(CommandHandler("group", set_group))
    app.add_handler(CommandHandler("add", add_photo))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("ban", ban))
    app.add_handler(CommandHandler("unban", unban))
    app.add_handler(CommandHandler("broadcast", broadcast))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, check_code))
    print("Bot started - myselfkhushi03 - username only insta fix")
    app.run_polling(drop_pending_updates=True)

if __name__=="__main__": main()
