import os, json, time, random, datetime
from threading import Thread
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand, BotCommandScopeDefault, BotCommandScopeChat
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.constants import ParseMode

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

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

# ===== YAHI WELCOME MSG LOCK HAI - SCREENSHOT WALA =====
DEFAULT_SETTINGS = {
    "name":"Khushi",
    "insta":"https://www.instagram.com/myselfkhushi03",
    "code":"6118588149",
    "font":"normal",
    "timer":0,
    "group":True,
    "protect": True,
    "welcome":"Hey {user} 💖💖💖 ✨\n\nWelcome to {name}'s private vault 💌\n--------------------------------------------\n\nI'm {name}, so glad you're here!\n\nYou've found my exclusive collection 📸\nJust one step to unlock.\n\n👤 Your Name: {user}\n🆔 Your ID: {id}\n\n🔐 Send the secret code to unlock"
}

def get_settings():
    s=load(SETTINGS_FILE)
    if not s:
        s=DEFAULT_SETTINGS.copy()
        save(SETTINGS_FILE,s)
    # Agar purana welcome hai to force update nahi karenge, par pehli baar yahi save hoga
    s.setdefault("protect", True)
    if "welcome" not in s or "private vault" not in s.get("welcome",""):
        s["welcome"] = DEFAULT_SETTINGS["welcome"]
        save(SETTINGS_FILE,s)
    return s

def load_admins():
    admins = load(ADMINS_FILE)
    if not admins or "list" not in admins:
        admins = {"master": ADMIN_ID, "list": [ADMIN_ID] if ADMIN_ID!=0 else []}
        save(ADMINS_FILE, admins)
    if ADMIN_ID!=0 and ADMIN_ID not in admins["list"]:
        admins["list"].append(ADMIN_ID)
        save(ADMINS_FILE, admins)
    return admins

def is_admin(uid): return uid in load_admins().get("list", [])
def is_master(uid): return uid == ADMIN_ID

def premium_box(title, lines):
    box = f"📦 {title}\n━━━━━━━━━━━━━━━━━━\n"
    for l in lines: box += f"{l}\n"
    box += "━━━━━━━━━━━━━━━━━━"
    return box

async def send_welcome_preview(chat_id, bot):
    s=get_settings()
    preview = s["welcome"].replace("{user}","TestUser").replace("{name}",s["name"]).replace("{id}","123456789")
    btn=[[InlineKeyboardButton(f"📸 Follow {s['name']}", url=s["insta"])]]
    try: await bot.send_message(chat_id=chat_id, text=f"👁️ **Welcome Preview:**\n\n{preview}", reply_markup=InlineKeyboardMarkup(btn), protect_content=s.get("protect", True))
    except: await bot.send_message(chat_id=chat_id, text=preview, reply_markup=InlineKeyboardMarkup(btn), protect_content=s.get("protect", True))

SMALL_MAP = {'A':'ᴀ','B':'ʙ','C':'ᴄ','D':'ᴅ','E':'ᴇ','F':'ꜰ','G':'ɢ','H':'ʜ','I':'ɪ','J':'ᴊ','K':'ᴋ','L':'ʟ','M':'ᴍ','N':'ɴ','O':'ᴏ','P':'ᴘ','Q':'ǫ','R':'ʀ','S':'ꜱ','T':'ᴛ','U':'ᴜ','V':'ᴠ','W':'ᴡ','X':'x','Y':'ʏ','Z':'ᴢ','a':'ᴀ','b':'ʙ','c':'ᴄ','d':'ᴅ','e':'ᴇ','f':'ꜰ','g':'ɢ','h':'ʜ','i':'ɪ','j':'ᴊ','k':'ᴋ','l':'ʟ','m':'ᴍ','n':'ɴ','o':'ᴏ','p':'ᴘ','q':'ǫ','r':'ʀ','s':'ꜱ','t':'ᴛ','u':'ᴜ','v':'ᴠ','w':'ᴡ','x':'x','y':'ʏ','z':'ᴢ'}
def apply_font(t, f): return "".join(SMALL_MAP.get(c,c) for c in t) if f=="small" else t
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

async def refresh_commands_for_admin(bot, admin_id, is_master_user=False):
    cmds=[
        BotCommand("start", "🚀 Start bot"), BotCommand("info", "👤 User info"),
        BotCommand("status", "📊 Bot Status"), BotCommand("users", "👥 User List"),
        BotCommand("admins", "👑 Admins List"), BotCommand("setname", "✏️ Set name"),
        BotCommand("setcode", "🔐 Set code"), BotCommand("setinsta", "🔗 Set Insta"),
        BotCommand("setfont", "🔤 Font"), BotCommand("settime", "⏱️ Timer"),
        BotCommand("add", "📸 Add photo"), BotCommand("group", "🌐 Group on/off"),
        BotCommand("broadcast", "📢 Broadcast")
    ]
    if is_master_user or admin_id==ADMIN_ID:
        cmds.extend([
            BotCommand("ban", "🚫 Ban user (Master)"), BotCommand("unban", "✅ Unban user (Master)"),
            BotCommand("addadmin", "➕ Add admin (Master)"), BotCommand("removeadmin", "➖ Remove admin (Master)"),
            BotCommand("protect", "🔒 Protect on/off (Master)"), BotCommand("reset", "♻️ Reset (Master)")
        ])
    try: await bot.set_my_commands(cmds, scope=BotCommandScopeChat(chat_id=admin_id))
    except: pass

async def setup_commands(app):
    await app.bot.set_my_commands([BotCommand("start", "🚀 Start bot"), BotCommand("admin", "📩 Contact admin")], scope=BotCommandScopeDefault())
    for aid in load_admins().get("list", []):
        await refresh_commands_for_admin(app.bot, aid, is_master_user=(aid==ADMIN_ID))

async def start(update, context):
    s=get_settings()
    if is_banned(update.effective_user.id): return
    uid=str(update.effective_user.id)
    users=load(USERS_FILE)
    now_str = datetime.datetime.now().strftime("%d-%m-%Y %H:%M")
    username = update.effective_user.username or "N/A"
    if uid not in users:
        users[uid]={"name":update.effective_user.first_name, "username": username, "joined": now_str, "verified": False}
        save(USERS_FILE,users)
    welcome_raw=s["welcome"].replace("{user}",update.effective_user.first_name).replace("{name}",s["name"]).replace("{id}",str(uid))
    welcome=apply_font(welcome_raw,s.get("font","normal"))
    btn=[[InlineKeyboardButton(f"📸 Follow {s['name']}", url=s["insta"])]]
    await update.message.reply_text(welcome, reply_markup=InlineKeyboardMarkup(btn), protect_content=s.get("protect", True))

async def check_code(update, context):
    if update.effective_user.id in PENDING_ADMIN_MSG:
        user_msg = update.message.text
        user = update.effective_user
        PENDING_ADMIN_MSG.pop(update.effective_user.id, None)
        for aid in load_admins().get("list", []):
            try: await context.bot.send_message(chat_id=aid, text=f"📩 **New User Message**\n━━━━━━━━━━━━━━━━━━\n👤 Name: {user.first_name}\n🆔 ID: `{user.id}`\n💬 Message: {user_msg}", parse_mode=ParseMode.MARKDOWN)
            except: pass
        await update.message.reply_text("✅ **Message sent to admins** 💌", parse_mode=ParseMode.MARKDOWN)
        return
    s=get_settings()
    if is_banned(update.effective_user.id): return
    if update.message.text.strip()!=s["code"]: return
    all_photos=get_photos()
    if len(all_photos)==0:
        await update.message.reply_text("📭 No photos yet!", protect_content=s.get("protect", True))
        return
    uid=str(update.effective_user.id)
    users=load(USERS_FILE)
    if uid in users:
        users[uid]["verified"]=True
        save(USERS_FILE,users)
    timer_sec=s.get("timer",0)
    to_send=random.sample(all_photos, min(2, len(all_photos)))
    await update.message.reply_text(f"✨ **Access Granted!** 💎", parse_mode=ParseMode.MARKDOWN, protect_content=s.get("protect", True))
    for i,p in enumerate(to_send,1):
        cap=apply_font(f"For you, {update.effective_user.first_name} 💖 • {i}/{len(to_send)}\nFrom: {s['name']} ✨", s.get("font","normal"))
        btn=[[InlineKeyboardButton(f"💎 Follow {s['name']}", url=s["insta"])]]
        sent=await update.message.reply_photo(open(p,"rb"), caption=cap, reply_markup=InlineKeyboardMarkup(btn), protect_content=s.get("protect", True))
        if timer_sec>0 and context.job_queue:
            context.job_queue.run_once(delete_job, timer_sec, chat_id=update.effective_chat.id, data=sent.message_id)
    if timer_sec>0: await update.message.reply_text(f"⏳ Auto-delete in {format_timer(timer_sec)}", protect_content=s.get("protect", True))

async def info_cmd(update, context):
    if not is_admin(update.effective_user.id): return
    target_id = update.effective_user.id
    if context.args:
        try: target_id = int(context.args[0])
        except: pass
    users = load(USERS_FILE)
    data = users.get(str(target_id), {"name": update.effective_user.first_name, "username": update.effective_user.username or "N/A"})
    text = premium_box("User Info - Premium", [f"👤 Name: {data.get('name','Unknown')}", f"🆔 ID: {target_id}", f"🔗 Username: @{data.get('username','N/A')}", f"💬 Direct: tg://user?id={target_id}", "", f"ID: `{target_id}` - Tap to copy"])
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)

async def admin_contact(update, context):
    if is_banned(update.effective_user.id): return
    if context.args:
        user_msg = " ".join(context.args)
        user = update.effective_user
        for aid in load_admins().get("list", []):
            try: await context.bot.send_message(chat_id=aid, text=premium_box("New User Message", [f"👤 Name: {user.first_name}", f"🆔 ID: `{user.id}`", f"💬 Message: {user_msg}"]), parse_mode=ParseMode.MARKDOWN)
            except: pass
        await update.message.reply_text(premium_box("Success", ["✅ Your message sent to all admins 💌"]), parse_mode=ParseMode.MARKDOWN)
    else:
        PENDING_ADMIN_MSG[update.effective_user.id] = True
        await update.message.reply_text(premium_box("Contact Admin", ["✍️ Send your message now", "Next message will go to admin"]))

async def protect_cmd(update, context):
    if not is_master(update.effective_user.id): await update.message.reply_text(premium_box("Error", ["❌ Only Master can control protection!"])); return
    if not context.args:
        s=get_settings()
        status = "ON 🔒 (Blocked)" if s.get("protect", True) else "OFF 🔓 (Allowed)"
        await update.message.reply_text(premium_box("Protection Status", [f"🔒 Current: {status}", "", "Usage:", "/protect on - Block forwarding & SS", "/protect off - Allow"]), parse_mode=ParseMode.MARKDOWN)
        return
    val = context.args[0].lower()
    s=get_settings()
    if val=="on": s["protect"]=True; save(SETTINGS_FILE,s); await update.message.reply_text(premium_box("Protection Updated", ["🔒 Protection ON ✅", "Forwarding & SS blocked now"])); await send_welcome_preview(update.effective_chat.id, context.bot)
    elif val=="off": s["protect"]=False; save(SETTINGS_FILE,s); await update.message.reply_text(premium_box("Protection Updated", ["🔓 Protection OFF ✅", "Forwarding allowed now"])); await send_welcome_preview(update.effective_chat.id, context.bot)

async def status(update, context):
    if not is_admin(update.effective_user.id): return
    s=get_settings(); users=load(USERS_FILE); banned=load(BANNED_FILE)
    prot = "ON 🔒" if s.get("protect", True) else "OFF 🔓"
    await update.message.reply_text(premium_box("Bot Premium Status", [f"👑 Name: {s['name']}", f"🔗 Insta: {s['insta']}", f"🔐 Code: {s['code']}", f"🔒 Protect: {prot}", f"⏱️ Timer: {format_timer(s.get('timer',0))}", f"📸 Photos: {len(get_photos())}", f"👥 Users: {len(users)}", f"🚫 Banned: {len(banned)}", f"👑 Admins: {len(load_admins().get('list',[]))}"]))

async def users_list(update, context):
    if not is_admin(update.effective_user.id): return
    users=load(USERS_FILE)
    if not users: await update.message.reply_text("No users yet 📭"); return
    header = f"📊 Users - Full Details\n━━━━━━━━━━━━━━━━━━\n👥 Total: {len(users)}\n━━━━━━━━━━━━━━━━━━\n\n"
    msg = header
    for idx, (uid, data) in enumerate(users.items(), 1):
        msg += f"{idx}. {data.get('name','Unknown')}\n👤 Username: @{data.get('username','N/A')}\n🆔 ID: `{uid}`\n\n"
        if len(msg) > 3500:
            await update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=True)
            msg = ""
    if msg!=header: await update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=True)

async def add_admin(update, context):
    if not is_master(update.effective_user.id): await update.message.reply_text(premium_box("Error", ["❌ Only Master can add admins!"])); return
    if not context.args: await update.message.reply_text(premium_box("Usage", ["/addadmin user_id"])); return
    try: new_id = int(context.args[0])
    except: await update.message.reply_text("Invalid ID"); return
    admins = load_admins()
    if new_id in admins["list"]: await update.message.reply_text(premium_box("Info", ["Already admin ✅"])); return
    admins["list"].append(new_id); save(ADMINS_FILE, admins)
    await refresh_commands_for_admin(context.bot, new_id, is_master_user=False)
    await update.message.reply_text(premium_box("Admin Added - Premium", [f"✅ User `{new_id}` is now admin!"]), parse_mode=ParseMode.MARKDOWN)

async def remove_admin(update, context):
    if not is_master(update.effective_user.id): await update.message.reply_text(premium_box("Error", ["❌ Only Master can remove!"])); return
    if not context.args: await update.message.reply_text(premium_box("Usage", ["/removeadmin user_id"])); return
    try: rem_id = int(context.args[0])
    except: await update.message.reply_text("Invalid ID"); return
    if rem_id == ADMIN_ID: await update.message.reply_text(premium_box("Error", ["❌ Cannot remove Master!"])); return
    admins = load_admins()
    if rem_id not in admins["list"]: await update.message.reply_text(premium_box("Error", ["Not an admin"])); return
    admins["list"].remove(rem_id); save(ADMINS_FILE, admins)
    try: await context.bot.set_my_commands([BotCommand("start", "🚀 Start bot"), BotCommand("admin", "📩 Contact admin")], scope=BotCommandScopeChat(chat_id=rem_id))
    except: pass
    await update.message.reply_text(premium_box("Admin Removed", [f"✅ Admin `{rem_id}` removed"]), parse_mode=ParseMode.MARKDOWN)

async def admins_list(update, context):
    if not is_admin(update.effective_user.id): return
    admins = load_admins(); users = load(USERS_FILE)
    lines=[]
    for i, uid in enumerate(admins["list"], 1):
        data = users.get(str(uid), {"name": "Unknown", "username": "N/A"})
        tag = " (Master 👑)" if uid == ADMIN_ID else " (Admin)"
        lines.append(f"{i}. {data['name']}{tag} - @{data['username']} ID: `{uid}`")
    await update.message.reply_text(premium_box("Admins List - Premium", lines), parse_mode=ParseMode.MARKDOWN)

async def reset_bot(update, context):
    if not is_master(update.effective_user.id): return
    save(SETTINGS_FILE, DEFAULT_SETTINGS.copy())
    await update.message.reply_text(premium_box("Reset Done", ["♻️ Bot reset to default ✅"]))

async def set_name(update, context):
    if not is_admin(update.effective_user.id): return
    if not context.args: return
    s=get_settings(); s["name"]=" ".join(context.args); save(SETTINGS_FILE,s)
    await update.message.reply_text(premium_box("Updated - Premium", [f"✏️ Name set to {s['name']} ✅"]))
    await send_welcome_preview(update.effective_chat.id, context.bot)

async def set_code(update, context):
    if not is_admin(update.effective_user.id): return
    if not context.args: return
    s=get_settings(); s["code"]=context.args[0]; save(SETTINGS_FILE,s)
    await update.message.reply_text(premium_box("Updated - Premium", [f"🔐 Code set to `{s['code']}` ✅"]), parse_mode=ParseMode.MARKDOWN)

async def set_insta(update, context):
    if not is_admin(update.effective_user.id): return
    if not context.args: return
    raw = context.args[0].strip().replace("@","")
    link = raw if "http" in raw else f"https://www.instagram.com/{raw.split('/')[-1]}"
    s=get_settings(); s["insta"]=link; save(SETTINGS_FILE,s)
    await update.message.reply_text(premium_box("Updated - Premium", [f"🔗 Insta set ✅"]))
    await send_welcome_preview(update.effective_chat.id, context.bot)

async def set_font(update, context):
    if not is_admin(update.effective_user.id): return
    if not context.args: return
    s=get_settings(); s["font"]=context.args[0].lower(); save(SETTINGS_FILE,s)
    await update.message.reply_text(premium_box("Updated", [f"🔤 Font set to {s['font']} ✅"]))
    await send_welcome_preview(update.effective_chat.id, context.bot)

async def set_timer(update, context):
    if not is_admin(update.effective_user.id): return
    if not context.args: return
    sec=parse_timer_str(context.args[0])
    if sec is None: return
    s=get_settings(); s["timer"]=sec; save(SETTINGS_FILE,s)
    await update.message.reply_text(premium_box("Timer Set", [f"⏱️ Timer: {format_timer(sec)} ✅"]))

async def set_group(update, context):
    if not is_admin(update.effective_user.id): return
    s=get_settings()
    if not context.args: return
    s["group"]=context.args[0].lower()=="on"; save(SETTINGS_FILE,s)
    await update.message.reply_text(premium_box("Group Updated", [f"Group {'enabled ✅' if s['group'] else 'disabled ❌'}"]))

async def add_photo(update, context):
    if not is_admin(update.effective_user.id): return
    if not update.message.reply_to_message or not update.message.reply_to_message.photo: return
    file=await update.message.reply_to_message.photo[-1].get_file()
    path=os.path.join(PHOTO_FOLDER, f"{int(time.time()*1000)}.jpg")
    await file.download_to_drive(path)
    await update.message.reply_text(premium_box("Photo Added - Premium", [f"📸 Added ✅ Total: {len(get_photos())}"]))

async def ban(update, context):
    if not is_master(update.effective_user.id): await update.message.reply_text(premium_box("Error - Premium", ["❌ Only Master can ban users 👑"])); return
    if not context.args: return
    try: target_id = int(context.args[0])
    except: return
    if target_id == ADMIN_ID or target_id == update.effective_user.id: await update.message.reply_text(premium_box("Error", ["❌ Cannot ban Master/yourself"])); return
    dur=context.args[1] if len(context.args)>1 else "perm"
    b=load(BANNED_FILE); b[str(target_id)]=parse_time(dur); save(BANNED_FILE,b)
    await update.message.reply_text(premium_box("Banned - Premium", [f"🚫 User `{target_id}` banned", f"Duration: {dur} ✅"]), parse_mode=ParseMode.MARKDOWN)

async def unban(update, context):
    if not is_master(update.effective_user.id): await update.message.reply_text(premium_box("Error - Premium", ["❌ Only Master can unban 👑"])); return
    if not context.args: return
    b=load(BANNED_FILE); b.pop(context.args[0],None); save(BANNED_FILE,b)
    await update.message.reply_text(premium_box("Unbanned - Premium", [f"✅ User `{context.args[0]}` unbanned"]), parse_mode=ParseMode.MARKDOWN)

async def broadcast(update, context):
    if not is_admin(update.effective_user.id): return
    users=load(USERS_FILE); s=get_settings()
    if not context.args and not update.message.reply_to_message: return
    if update.message.reply_to_message:
        c=0
        for uid in users:
            try: await update.message.reply_to_message.copy(chat_id=int(uid), protect_content=s.get("protect", True)); c+=1
            except: pass
        await update.message.reply_text(premium_box("Broadcast - Premium", [f"📢 Sent to {c} users ✅"]))
    else:
        text=" ".join(context.args[1:]) if context.args[0].lower()=="all" else " ".join(context.args)
        c=0
        for uid in users:
            try: await context.bot.send_message(chat_id=int(uid), text=text, protect_content=s.get("protect", True)); c+=1
            except: pass
        await update.message.reply_text(premium_box("Broadcast - Premium", [f"📢 Sent to {c} users ✅"]))

def main():
    app=Application.builder().token(BOT_TOKEN).post_init(setup_commands).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("info", info_cmd))
    app.add_handler(CommandHandler("admin", admin_contact))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("users", users_list))
    app.add_handler(CommandHandler("admins", admins_list))
    app.add_handler(CommandHandler("addadmin", add_admin))
    app.add_handler(CommandHandler("removeadmin", remove_admin))
    app.add_handler(CommandHandler("protect", protect_cmd))
    app.add_handler(CommandHandler("setname", set_name))
    app.add_handler(CommandHandler("setcode", set_code))
    app.add_handler(CommandHandler("setinsta", set_insta))
    app.add_handler(CommandHandler("setfont", set_font))
    app.add_handler(CommandHandler("settimer", set_timer))
    app.add_handler(CommandHandler("settime", set_timer))
    app.add_handler(CommandHandler("group", set_group))
    app.add_handler(CommandHandler("add", add_photo))
    app.add_handler(CommandHandler("reset", reset_bot))
    app.add_handler(CommandHandler("ban", ban))
    app.add_handler(CommandHandler("unban", unban))
    app.add_handler(CommandHandler("broadcast", broadcast))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, check_code))
    print("Bot started - Welcome locked to screenshot version")
    app.run_polling(drop_pending_updates=True)

if __name__=="__main__": main()
