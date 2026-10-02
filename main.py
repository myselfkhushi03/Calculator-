import os, json, time, random, datetime
from threading import Thread
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand, BotCommandScopeDefault, BotCommandScopeChat
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from telegram.constants import ParseMode

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
    s.setdefault("protect", True); return s
def load_admins():
    admins = load(ADMINS_FILE)
    if not admins or "list" not in admins:
        admins = {"master": ADMIN_ID, "list": [ADMIN_ID] if ADMIN_ID!=0 else []}; save(ADMINS_FILE, admins)
    if ADMIN_ID!=0 and ADMIN_ID not in admins["list"]: admins["list"].append(ADMIN_ID); save(ADMINS_FILE, admins)
    return admins
def is_admin(uid): return uid in load_admins().get("list", [])
def is_master(uid): return uid == ADMIN_ID
def premium_box(title, lines):
    box = f"📦 {title}\n━━━━━━━━━━━━━━━━━━\n"
    for l in lines: box += f"{l}\n"
    box += "━━━━━━━━━━━━━━━━━━"; return box
def get_photos(): return [os.path.join(PHOTO_FOLDER,x) for x in os.listdir(PHOTO_FOLDER) if x.lower().endswith(('.jpg','.jpeg','.png','.webp'))]
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
def parse_timer_str(s):
    s=s.lower().strip()
    if s in ["0","off"]: return 0
    try:
        if s[-1]=="s": return max(5,int(s[:-1]))
        if s[-1]=="m": return int(s[:-1])*60
        if s[-1]=="h": return int(s[:-1])*3600
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
async def notify_master(context, admin_user, action, extra_lines):
    if admin_user.id == ADMIN_ID: return
    try:
        lines = [f"👤 Admin: {admin_user.first_name}", f"🆔 ID: {admin_user.id}", f"🔗 @{admin_user.username or 'N/A'}", f"⚡ Action: {action}"] + extra_lines
        await context.bot.send_message(chat_id=ADMIN_ID, text=premium_box("Admin Activity Log", lines))
    except: pass

SMALL_MAP = {'A':'ᴀ','B':'ʙ','C':'ᴄ','D':'ᴅ','E':'ᴇ','F':'ꜰ','G':'ɢ','H':'ʜ','I':'ɪ','J':'ᴊ','K':'ᴋ','L':'ʟ','M':'ᴍ','N':'ɴ','O':'ᴏ','P':'ᴘ','Q':'ǫ','R':'ʀ','S':'ꜱ','T':'ᴛ','U':'ᴜ','V':'ᴠ','W':'ᴡ','X':'x','Y':'ʏ','Z':'ᴢ','a':'ᴀ','b':'ʙ','c':'ᴄ','d':'ᴅ','e':'ᴇ','f':'ꜰ','g':'ɢ','h':'ʜ','i':'ɪ','j':'ᴊ','k':'ᴋ','l':'ʟ','m':'ᴍ','n':'ɴ','o':'ᴏ','p':'ᴘ','q':'ǫ','r':'ʀ','s':'ꜱ','t':'ᴛ','u':'ᴜ','v':'ᴠ','w':'ᴡ','x':'x','y':'ʏ','z':'ᴢ'}
def apply_font(t, f): return "".join(SMALL_MAP.get(c,c) for c in t) if f=="small" else t

async def refresh_commands_for_admin(bot, admin_id, is_master_user=False):
    cmds=[BotCommand("start","🚀 Start"),BotCommand("info","👤 Info"),BotCommand("status","📊 Status"),BotCommand("users","👥 Users"),BotCommand("admins","👑 Admins"),BotCommand("setname","✏️ Name"),BotCommand("setcode","🔐 Code"),BotCommand("setinsta","🔗 Insta"),BotCommand("setfont","🔤 Font"),BotCommand("settime","⏱️ Timer"),BotCommand("add","📸 Add 5 max"),BotCommand("clearphotos","🗑️ Clear all"),BotCommand("group","🌐 Group"),BotCommand("broadcast","📢 Broadcast")]
    if is_master_user or admin_id==ADMIN_ID:
        cmds.extend([BotCommand("ban","🚫 Ban"),BotCommand("unban","✅ Unban"),BotCommand("addadmin","➕ Add admin"),BotCommand("removeadmin","➖ Remove admin"),BotCommand("protect","🔒 Protect"),BotCommand("reset","♻️ Reset")])
    try: await bot.set_my_commands(cmds, scope=BotCommandScopeChat(chat_id=admin_id))
    except: pass

async def setup_commands(app):
    await app.bot.set_my_commands([BotCommand("start","🚀 Start bot"),BotCommand("admin","📩 Contact admin")], scope=BotCommandScopeDefault())
    for aid in load_admins().get("list", []): await refresh_commands_for_admin(app.bot, aid, is_master_user=(aid==ADMIN_ID))

async def start(update, context):
    s=get_settings()
    if is_banned(update.effective_user.id): return
    uid=str(update.effective_user.id); users=load(USERS_FILE)
    if uid not in users:
        users[uid]={"name":update.effective_user.first_name, "username": update.effective_user.username or "N/A", "joined": datetime.datetime.now().strftime("%d-%m-%Y %H:%M"), "verified": False}; save(USERS_FILE,users)
    welcome=apply_font(s["welcome"].replace("{user}",update.effective_user.first_name).replace("{name}",s["name"]).replace("{id}",str(uid)), s.get("font","normal"))
    btn=[[InlineKeyboardButton(f"📸 Follow {s['name']}", url=s["insta"])]]
    await update.message.reply_text(welcome, reply_markup=InlineKeyboardMarkup(btn), protect_content=s.get("protect", True))

async def check_code(update, context):
    if update.effective_user.id in PENDING_ADMIN_MSG:
        PENDING_ADMIN_MSG.pop(update.effective_user.id, None)
        for aid in load_admins().get("list", []):
            try: await context.bot.send_message(chat_id=aid, text=f"📩 New Msg\n👤 {update.effective_user.first_name}\n🆔 {update.effective_user.id}\n💬 {update.message.text}")
            except: pass
        await update.message.reply_text("✅ Message sent to admins 💌"); return
    s=get_settings()
    if is_banned(update.effective_user.id): return
    if not update.message.text or update.message.text.strip()!=s["code"]: return
    all_photos=get_photos()
    if len(all_photos)==0: await update.message.reply_text("📭 No photos yet!", protect_content=s.get("protect", True)); return
    total=len(all_photos)
    await update.message.reply_text(f"✨ Access Granted! 💎 Sending {total} photos...", protect_content=s.get("protect", True))
    for i, p in enumerate(all_photos, 1):
        cap=apply_font(f"For you, {update.effective_user.first_name} 💖 • {i}/{total}\nFrom: {s['name']} ✨", s.get("font","normal"))
        btn=[[InlineKeyboardButton(f"📸 Follow {s['name']}", url=s["insta"])]]
        sent=await update.message.reply_photo(open(p,"rb"), caption=cap, reply_markup=InlineKeyboardMarkup(btn), protect_content=s.get("protect", True))
        if s.get("timer",0)>0 and context.job_queue: context.job_queue.run_once(delete_job, s.get("timer",0), chat_id=update.effective_chat.id, data=sent.message_id)

async def status(update, context):
    if not is_admin(update.effective_user.id): return
    s=get_settings(); users=load(USERS_FILE); banned=load(BANNED_FILE)
    await update.message.reply_text(premium_box("Bot Status", [f"👑 {s['name']}", f"🔐 {s['code']}", f"📸 {len(get_photos())}/{MAX_PHOTOS}", f"👥 {len(users)}", f"🚫 {len(banned)}", f"⏱️ Timer: {format_timer(s.get('timer',0))}"]))

async def info_cmd(update, context):
    if not is_admin(update.effective_user.id): return
    tid = int(context.args[0]) if context.args else update.effective_user.id
    users=load(USERS_FILE); d=users.get(str(tid), {"name":"Unknown", "username":"N/A"})
    await update.message.reply_text(premium_box("User Info", [f"👤 {d.get('name')}", f"🆔 {tid}", f"🔗 @{d.get('username')}"]))

async def users_list(update, context):
    if not is_admin(update.effective_user.id): return
    users=load(USERS_FILE); msg=f"📊 Users: {len(users)}\n\n"
    for idx, (uid, data) in enumerate(users.items(),1):
        msg+=f"{idx}. {data.get('name')} ID:{uid}\n"
        if len(msg)>3500: await update.message.reply_text(msg); msg=""
    if msg: await update.message.reply_text(msg)

async def admins_list(update, context):
    if not is_admin(update.effective_user.id): return
    admins=load_admins(); users=load(USERS_FILE); lines=[]
    for i, uid in enumerate(admins["list"],1):
        lines.append(f"{i}. {users.get(str(uid),{'name':'Unknown'})['name']} ID:{uid} {'(Master)' if uid==ADMIN_ID else ''}")
    await update.message.reply_text(premium_box("Admins List", lines))

async def add_admin(update, context):
    if not is_master(update.effective_user.id): await update.message.reply_text(premium_box("Error", ["❌ Only Master can add admin"])); return
    if not context.args: await update.message.reply_text("Use: /addadmin <user_id>"); return
    try: new_id=int(context.args[0])
    except: await update.message.reply_text("ID number me bhej"); return
    admins=load_admins()
    if new_id not in admins["list"]: admins["list"].append(new_id); save(ADMINS_FILE, admins); await refresh_commands_for_admin(context.bot, new_id, False)
    await update.message.reply_text(premium_box("Admin Added", [f"✅ {new_id} is now admin"]))

async def remove_admin(update, context):
    if not is_master(update.effective_user.id): await update.message.reply_text(premium_box("Error", ["❌ Only Master"])); return
    if not context.args: await update.message.reply_text("Use: /removeadmin <id>"); return
    try: rem_id=int(context.args[0])
    except: return
    if rem_id==ADMIN_ID: await update.message.reply_text(premium_box("Error", ["❌ Cannot remove Master"])); return
    admins=load_admins()
    if rem_id in admins["list"]: admins["list"].remove(rem_id); save(ADMINS_FILE, admins)
    await update.message.reply_text(premium_box("Removed", [f"✅ {rem_id} removed"]))

async def set_name(update, context):
    if not is_admin(update.effective_user.id): return
    if not context.args: await update.message.reply_text("Use: /setname Khushi"); return
    s=get_settings(); old=s["name"]; s["name"]=" ".join(context.args); save(SETTINGS_FILE,s)
    await update.message.reply_text(premium_box("Updated", [f"Name: {s['name']}"]))
    await notify_master(context, update.effective_user, "Set Name", [f"Old: {old}", f"New: {s['name']}"])

async def set_code(update, context):
    if not is_admin(update.effective_user.id): return
    if not context.args: await update.message.reply_text("Use: /setcode 1234"); return
    s=get_settings(); old=s["code"]; s["code"]=context.args[0]; save(SETTINGS_FILE,s)
    await update.message.reply_text(premium_box("Updated", [f"Code: {s['code']}"]))
    await notify_master(context, update.effective_user, "Set Code", [f"Old: {old}", f"New: {s['code']}"])

async def set_insta(update, context):
    if not is_admin(update.effective_user.id): return
    if not context.args: await update.message.reply_text("Use: /setinsta username"); return
    raw=context.args[0].replace("@",""); link=raw if "http" in raw else f"https://www.instagram.com/{raw.split('/')[-1]}"
    s=get_settings(); old=s["insta"]; s["insta"]=link; save(SETTINGS_FILE,s)
    await update.message.reply_text(premium_box("Updated", ["Insta set ✅", link]))
    await notify_master(context, update.effective_user, "Set Insta", [f"Old: {old}", f"New: {link}"])

async def set_font(update, context):
    if not is_admin(update.effective_user.id): return
    if not context.args: await update.message.reply_text("Use: /setfont normal / small"); return
    s=get_settings(); s["font"]=context.args[0].lower(); save(SETTINGS_FILE,s)
    await update.message.reply_text(premium_box("Updated", [f"Font: {s['font']}"]))
    await notify_master(context, update.effective_user, "Set Font", [f"Font: {s['font']}"])

async def set_timer(update, context):
    if not is_admin(update.effective_user.id): return
    if not context.args: await update.message.reply_text("Use: /settime 5m / 30s / off"); return
    sec=parse_timer_str(context.args[0])
    if sec is None: await update.message.reply_text("Valid: 30s, 5m, 1h, off"); return
    s=get_settings(); s["timer"]=sec; save(SETTINGS_FILE,s)
    await update.message.reply_text(premium_box("Timer Set", [f"Timer: {format_timer(sec)} ✅"]))
    await notify_master(context, update.effective_user, "Set Timer", [f"Timer: {format_timer(sec)}"])

async def set_group(update, context):
    if not is_admin(update.effective_user.id): return
    if not context.args: return
    s=get_settings(); s["group"]=context.args[0].lower()=="on"; save(SETTINGS_FILE,s)
    await update.message.reply_text(premium_box("Group", [f"{'ON ✅' if s['group'] else 'OFF ❌'}"]))

async def protect_cmd(update, context):
    if not is_master(update.effective_user.id): await update.message.reply_text(premium_box("Error", ["❌ Only Master"])); return
    if not context.args: await update.message.reply_text("Use: /protect on/off"); return
    s=get_settings(); s["protect"]=context.args[0].lower()=="on"; save(SETTINGS_FILE,s)
    await update.message.reply_text(premium_box("Updated", [f"Protect: {'ON 🔒' if s['protect'] else 'OFF 🔓'}"]))

async def reset_bot(update, context):
    if not is_master(update.effective_user.id): return
    save(SETTINGS_FILE, DEFAULT_SETTINGS.copy())
    await update.message.reply_text(premium_box("Reset", ["♻️ Reset done ✅"]))

async def add_photo(update, context):
    if not is_admin(update.effective_user.id): await update.message.reply_text("❌ Not admin"); return
    target=None
    if update.message.photo: target=update.message
    elif update.message.reply_to_message and update.message.reply_to_message.photo: target=update.message.reply_to_message
    elif update.message.document: target=update.message
    elif update.message.reply_to_message and update.message.reply_to_message.document: target=update.message.reply_to_message
    if not target: await update.message.reply_text(f"📸 Photo bhej ke caption me /add likh\nYa photo ko reply karke /add kar\nLimit: {MAX_PHOTOS}"); return
    current=len(get_photos())
    if current>=MAX_PHOTOS: await update.message.reply_text(premium_box("Limit Reached", [f"❌ Max {MAX_PHOTOS} allowed", f"Current: {current}/{MAX_PHOTOS}", f"Use /clearphotos"])); return
    try:
        file = await (target.photo[-1].get_file() if target.photo else target.document.get_file())
        path=os.path.join(PHOTO_FOLDER, f"{int(time.time()*1000)}.jpg")
        await file.download_to_drive(path)
        await update.message.reply_text(premium_box("Photo Added - Premium", [f"✅ Added: {current+1}/{MAX_PHOTOS}"]))
        await notify_master(context, update.effective_user, "Photo Added", [f"Total: {current+1}/{MAX_PHOTOS}"])
    except Exception as e: await update.message.reply_text(f"Error: {e}")

async def clear_photos(update, context):
    if not is_admin(update.effective_user.id): return
    photos=get_photos()
    if not photos: await update.message.reply_text("📭 No photos"); return
    for p in photos:
        try: os.remove(p)
        except: pass
    await update.message.reply_text(premium_box("Photos Cleared", [f"🗑️ {len(photos)} deleted ✅", f"Now: 0/{MAX_PHOTOS}"]))
    await notify_master(context, update.effective_user, "Clear Photos", [f"Deleted: {len(photos)}", f"Now: 0/{MAX_PHOTOS}"])

async def ban(update, context):
    if not is_master(update.effective_user.id): await update.message.reply_text(premium_box("Error", ["❌ Only Master can ban"])); return
    if not context.args: await update.message.reply_text("Use: /ban <id> <time> e.g. /ban 123 1h"); return
    target_id=int(context.args[0])
    if target_id==ADMIN_ID: await update.message.reply_text(premium_box("Error", ["❌ Cannot ban Master"])); return
    dur=context.args[1] if len(context.args)>1 else "perm"
    b=load(BANNED_FILE); b[str(target_id)]=parse_time(dur) or "perm"; save(BANNED_FILE,b)
    await update.message.reply_text(premium_box("Banned", [f"🚫 {target_id} banned {dur} ✅"]))

async def unban(update, context):
    if not is_master(update.effective_user.id): await update.message.reply_text(premium_box("Error", ["❌ Only Master can unban"])); return
    if not context.args: return
    b=load(BANNED_FILE); b.pop(context.args[0],None); save(BANNED_FILE,b)
    await update.message.reply_text(premium_box("Unbanned", [f"✅ {context.args[0]} unbanned"]))

async def broadcast(update, context):
    if not is_admin(update.effective_user.id): return
    users=load(USERS_FILE); s=get_settings()
    if update.message.reply_to_message:
        c=0
        for uid in users:
            try: await update.message.reply_to_message.copy(chat_id=int(uid), protect_content=s.get("protect", True)); c+=1
            except: pass
        await update.message.reply_text(premium_box("Broadcast", [f"Sent to {c} users ✅"]))
    else:
        if not context.args: await update.message.reply_text("Use: /broadcast message or reply to message"); return
        text=" ".join(context.args); c=0
        for uid in users:
            try: await context.bot.send_message(chat_id=int(uid), text=text, protect_content=s.get("protect", True)); c+=1
            except: pass
        await update.message.reply_text(premium_box("Broadcast", [f"Sent to {c} users ✅"]))

async def admin_contact(update, context):
    if is_banned(update.effective_user.id): return
    if context.args:
        for aid in load_admins().get("list", []):
            try: await context.bot.send_message(chat_id=aid, text=premium_box("New User Message", [f"👤 {update.effective_user.first_name}", f"🆔 {update.effective_user.id}", f"💬 {' '.join(context.args)}"]))
            except: pass
        await update.message.reply_text(premium_box("Success", ["✅ Sent to admins 💌"]))
    else: PENDING_ADMIN_MSG[update.effective_user.id] = True; await update.message.reply_text(premium_box("Contact Admin", ["✍️ Ab apna message bhejo"]))

def main():
    app=Application.builder().token(BOT_TOKEN).post_init(setup_commands).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("info", info_cmd))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("users", users_list))
    app.add_handler(CommandHandler("admins", admins_list))
    app.add_handler(CommandHandler("addadmin", add_admin))
    app.add_handler(CommandHandler("removeadmin", remove_admin))
    app.add_handler(CommandHandler("setname", set_name))
    app.add_handler(CommandHandler("setcode", set_code))
    app.add_handler(CommandHandler("setinsta", set_insta))
    app.add_handler(CommandHandler("setfont", set_font))
    app.add_handler(CommandHandler("settime", set_timer))
    app.add_handler(CommandHandler("settimer", set_timer))
    app.add_handler(CommandHandler("group", set_group))
    app.add_handler(CommandHandler("protect", protect_cmd))
    app.add_handler(CommandHandler("reset", reset_bot))
    app.add_handler(CommandHandler("add", add_photo))
    app.add_handler(CommandHandler("clearphotos", clear_photos))
    app.add_handler(CommandHandler("ban", ban))
    app.add_handler(CommandHandler("unban", unban))
    app.add_handler(CommandHandler("broadcast", broadcast))
    app.add_handler(CommandHandler("admin", admin_contact))
    app.add_handler(MessageHandler(filters.PHOTO & filters.CaptionRegex(r"(?i)/add"), add_photo))
    app.add_handler(MessageHandler(filters.Document.IMAGE & filters.CaptionRegex(r"(?i)/add"), add_photo))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, check_code))
    print(f"Bot started - All commands OK - Max {MAX_PHOTOS}"); app.run_polling(drop_pending_updates=True)

if __name__=="__main__": main()
