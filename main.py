import os, json, time, random, datetime
from threading import Thread
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand, BotCommandScopeDefault, BotCommandScopeChat
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.constants import ParseMode

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

web = Flask(__name__)
@web.route('/')
def home(): return "Bot Alive"
def run_web(): web.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
Thread(target=run_web, daemon=True).start()

USERS_FILE="users.json"; BANNED_FILE="banned.json"; SETTINGS_FILE="settings.json"; ADMINS_FILE="admins.json"
PHOTO_FOLDER="photos"; os.makedirs(PHOTO_FOLDER, exist_ok=True)

def load(f):
    try: return json.load(open(f,"r"))
    except: return {}
def save(f,d): json.dump(d, open(f,"w"), indent=2)

DEFAULT_SETTINGS = {
    "name":"Khushi",
    "insta":"https://www.instagram.com/myselfkhushi03",
    "code":"6118588149",
    "font":"normal",
    "timer":0,
    "group":True,
    "welcome":"Hey {user} ✨\n\nWelcome to {name}'s private vault 💌\n______________________________\n\nI'm {name}, so glad you're here!\n\nYou've found my exclusive collection 📸\nJust one step to unlock.\n\n👤 Your Name: {user}\n🆔 Your ID: {id}\n\n🔐 Send the secret code to unlock"
}

def get_settings():
    s=load(SETTINGS_FILE)
    if not s:
        s=DEFAULT_SETTINGS.copy()
        save(SETTINGS_FILE,s)
    s.setdefault("font","normal"); s.setdefault("timer",0); s.setdefault("group",True)
    return s

def load_admins():
    admins = load(ADMINS_FILE)
    if not admins or "list" not in admins:
        admins = {"master": ADMIN_ID, "list": [ADMIN_ID]}
        save(ADMINS_FILE, admins)
    if ADMIN_ID not in admins["list"]:
        admins["list"].append(ADMIN_ID)
        save(ADMINS_FILE, admins)
    return admins

def is_admin(uid):
    admins = load_admins()
    return uid in admins.get("list", [])

def is_master(uid):
    return uid == ADMIN_ID

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

def get_ban_info(uid):
    b=load(BANNED_FILE)
    if str(uid) not in b: return None
    exp=b[str(uid)]
    if exp=="perm": return "Permanent"
    if time.time()>exp: b.pop(str(uid)); save(BANNED_FILE,b); return None
    remaining = exp - time.time()
    if remaining < 3600: return f"{int(remaining//60)}m left"
    if remaining < 86400: return f"{int(remaining//3600)}h left"
    return f"{int(remaining//86400)}d left"

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
    await app.bot.set_my_commands([BotCommand("start", "🚀 Start bot"), BotCommand("info", "👤 User info"), BotCommand("admin", "📩 Contact admin")], scope=BotCommandScopeDefault())
    for aid in load_admins().get("list", [ADMIN_ID]):
        try:
            cmds=[
                BotCommand("start", "🚀 Start bot"),
                BotCommand("info", "👤 User info"),
                BotCommand("admin", "📩 Contact admin"),
                BotCommand("status", "📊 Bot Status"),
                BotCommand("users", "👥 User List"),
                BotCommand("admins", "👑 Admins List"),
                BotCommand("addadmin", "➕ Add admin (Master)"),
                BotCommand("removeadmin", "➖ Remove admin (Master)"),
                BotCommand("setname", "✏️ Set name"),
                BotCommand("setcode", "🔐 Set code"),
                BotCommand("setinsta", "🔗 Set Insta"),
                BotCommand("setfont", "🔤 Font"),
                BotCommand("settime", "⏱️ Timer"),
                BotCommand("add", "📸 Add photo"),
                BotCommand("group", "🌐 Group on/off"),
                BotCommand("reset", "♻️ Reset"),
                BotCommand("ban", "🚫 Ban"),
                BotCommand("unban", "✅ Unban"),
                BotCommand("broadcast", "📢 Broadcast")
            ]
            await app.bot.set_my_commands(cmds, scope=BotCommandScopeChat(chat_id=aid))
        except: pass

async def start(update, context):
    s=get_settings()
    if update.effective_chat.type in ["group","supergroup"] and not s.get("group",True): return
    if is_banned(update.effective_user.id): return
    uid=str(update.effective_user.id)
    users=load(USERS_FILE)
    now_str = datetime.datetime.now().strftime("%d-%m-%Y %H:%M")
    username = update.effective_user.username or "N/A"
    if uid not in users:
        users[uid]={"name":update.effective_user.first_name, "username": username, "joined": now_str, "verified": False}
        save(USERS_FILE,users)
    else:
        users[uid]["username"] = username
        users[uid]["name"] = update.effective_user.first_name
        save(USERS_FILE,users)
    welcome_raw=s["welcome"].replace("{user}",update.effective_user.first_name).replace("{name}",s["name"]).replace("{id}",str(uid))
    welcome=apply_font(welcome_raw,s.get("font","normal"))
    btn=[[InlineKeyboardButton(f"📸 Follow {s['name']}", url=s["insta"])]]
    await update.message.reply_text(welcome, reply_markup=InlineKeyboardMarkup(btn), protect_content=True)

async def check_code(update, context):
    s=get_settings()
    if update.effective_chat.type in ["group","supergroup"] and not s.get("group",True): return
    if is_banned(update.effective_user.id): return
    txt=update.message.text.strip()
    if txt!=s["code"]:
        if txt.isdigit() and len(txt)>=4: await update.message.reply_text("Oops! Wrong code 🥺 Try again", protect_content=True)
        return
    all_photos=get_photos()
    if len(all_photos)==0:
        await update.message.reply_text(f"📭 No photos yet! Timer: {format_timer(s.get('timer',0))}", protect_content=True)
        return
    uid=str(update.effective_user.id)
    users=load(USERS_FILE)
    if uid in users:
        users[uid]["verified"]=True
        save(USERS_FILE,users)
    timer_sec=s.get("timer",0)
    to_send=random.sample(all_photos, min(2, len(all_photos)))
    await update.message.reply_text(f"Yayy! Access granted ✅\nSending photos from {s['name']}...", protect_content=True)
    for i,p in enumerate(to_send,1):
        cap=apply_font(f"For you, {update.effective_user.first_name} 💖 • {i}/{len(to_send)}\nFrom: {s['name']} ✨", s.get("font","normal"))
        btn=[[InlineKeyboardButton(f"📸 Follow {s['name']}", url=s["insta"])]]
        sent=await update.message.reply_photo(open(p,"rb"), caption=cap, reply_markup=InlineKeyboardMarkup(btn), protect_content=True)
        if timer_sec>0 and context.job_queue:
            try: context.job_queue.run_once(delete_job, timer_sec, chat_id=update.effective_chat.id, data=sent.message_id)
            except: pass
    if timer_sec>0:
        await update.message.reply_text(f"⏳ Auto-delete in {format_timer(timer_sec)}", protect_content=True)

async def info_cmd(update, context):
    s=get_settings()
    if update.effective_chat.type in ["group","supergroup"] and not s.get("group",True): return
    if is_banned(update.effective_user.id): return
    target_id = update.effective_user.id
    if context.args:
        try: target_id = int(context.args[0])
        except: pass
    users = load(USERS_FILE)
    data = users.get(str(target_id), {"name": update.effective_user.first_name, "username": update.effective_user.username or "N/A"})
    name = data.get("name","Unknown")
    username = data.get("username","N/A")
    if username!= "N/A" and username:
        profile_url = f"https://t.me/{username}"
        uname_text = f"@{username}"
    else:
        profile_url = f"tg://user?id={target_id}"
        uname_text = "@N/A"
    text = (
        f"👤 **User info**\n\n"
        f"**ID:** `{target_id}`\n"
        f"**Name:** {name}\n"
        f"**Username:** {uname_text}\n"
        f"**Profile:** [open]({profile_url})\n"
        f"**TG Link:** `tg://user?id={target_id}`\n\n"
        f"_ID pe tap karke copy karo_"
    )
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)

async def admin_contact(update, context):
    if is_banned(update.effective_user.id): return
    if not context.args:
        await update.message.reply_text("Usage: /admin mujhe help chahiye")
        return
    user_msg = " ".join(context.args)
    user = update.effective_user
    users = load(USERS_FILE)
    udata = users.get(str(user.id), {})
    for aid in load_admins().get("list", [ADMIN_ID]):
        try:
            await context.bot.send_message(
                chat_id=aid,
                text=f"📩 **New Admin Msg**\n\n👤 Name: {user.first_name}\n🆔 ID: `{user.id}`\n🔗 Username: @{user.username if user.username else 'N/A'}\n📅 Joined: {udata.get('joined','N/A')}\n\n💬 Message:\n{user_msg}",
                parse_mode=ParseMode.MARKDOWN
            )
        except: pass
    await update.message.reply_text("✅ Message sab admins ko bhej diya 💌")

async def status(update, context):
    if not is_admin(update.effective_user.id): return
    s=get_settings()
    users=load(USERS_FILE)
    banned=load(BANNED_FILE)
    verified = sum(1 for u in users.values() if u.get('verified'))
    text = (
        f"📊 Bot Status\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"👑 Name : {s['name']}\n"
        f"🔗 Insta : {s['insta']}\n"
        f"🔐 Code : {s['code']}\n"
        f"🔤 Font : {s['font']}\n"
        f"⏱️ Timer : {format_timer(s.get('timer',0))}\n"
        f"🌐 Group : {'Enabled ✅' if s.get('group',True) else 'Disabled ❌'}\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"📸 Photos : {len(get_photos())}\n"
        f"👥 Users : {len(users)}\n"
        f"✅ Verified : {verified}\n"
        f"🚫 Banned : {len(banned)}\n"
        f"👑 Admins : {len(load_admins().get('list',[]))}\n"
        f"━━━━━━━━━━━━━━━━━━"
    )
    await update.message.reply_text(text)

async def users_list(update, context):
    if not is_admin(update.effective_user.id): return
    users=load(USERS_FILE)
    if not users:
        await update.message.reply_text("No users yet 📭")
        return
    total = len(users)
    banned_dict = load(BANNED_FILE)
    photos_count = len(get_photos())
    verified_count = sum(1 for u in users.values() if u.get('verified'))
    header = (
        f"📊 Bot Stats - Full Details\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"👥 Total Users: {total}\n"
        f"📸 Total Photos: {photos_count}\n"
        f"✅ Verified: {verified_count}\n"
        f"🚫 Banned: {len(banned_dict)}\n"
        f"━━━━━━━━━━━━━━━━━━\n\n"
    )
    msg = header
    for idx, (uid, data) in enumerate(users.items(), 1):
        name = data.get("name","Unknown")
        username = data.get("username","N/A")
        joined = data.get("joined","N/A")
        verified = data.get("verified", False)
        ban_info = get_ban_info(uid)
        if username!= "N/A" and username:
            uname_md = f"[@{username}](https://t.me/{username})"
            prof_line = f"🔗 Profile: [open](https://t.me/{username}) | [TG](tg://user?id={uid})"
        else:
            uname_md = "@N/A"
            prof_line = f"🔗 Profile: [TG](tg://user?id={uid})"
        msg += f"{idx}. {name}\n👤 Username: {uname_md}\n🆔 ID: `{uid}`\n📅 Joined: {joined}\n{prof_line}\n"
        if ban_info: msg += f"🚫 Banned: {ban_info}\n"
        else: msg += f"{'✅ Verified' if verified else '⏳ Not Verified'}\n"
        msg += f"\n"
        if len(msg) > 3500:
            await update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=True)
            msg = ""
    if msg.strip()!= header.strip():
        await update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=True)

async def add_admin(update, context):
    if not is_master(update.effective_user.id):
        await update.message.reply_text("❌ Sirf Master hi admin bana sakta hai!")
        return
    if not context.args:
        await update.message.reply_text("Usage: /addadmin user_id")
        return
    try: new_id = int(context.args[0])
    except:
        await update.message.reply_text("Sahi ID do")
        return
    admins = load_admins()
    if new_id in admins["list"]:
        await update.message.reply_text("Wo pehle se admin hai ✅")
        return
    admins["list"].append(new_id)
    save(ADMINS_FILE, admins)
    await update.message.reply_text(f"✅ User `{new_id}` ko admin bana diya!", parse_mode=ParseMode.MARKDOWN)
    try: await context.bot.send_message(new_id, "🎉 Tumhe admin bana diya gaya hai!")
    except: pass

async def remove_admin(update, context):
    if not is_master(update.effective_user.id):
        await update.message.reply_text("❌ Sirf Master hi hata sakta hai!")
        return
    if not context.args:
        await update.message.reply_text("Usage: /removeadmin user_id")
        return
    try: rem_id = int(context.args[0])
    except:
        await update.message.reply_text("Sahi ID do")
        return
    if rem_id == ADMIN_ID:
        await update.message.reply_text("❌ Master ko nahi hata sakte!")
        return
    admins = load_admins()
    if rem_id not in admins["list"]:
        await update.message.reply_text("Wo admin hi nahi hai")
        return
    admins["list"].remove(rem_id)
    save(ADMINS_FILE, admins)
    await update.message.reply_text(f"✅ User `{rem_id}` ko admin se hata diya!", parse_mode=ParseMode.MARKDOWN)

async def admins_list(update, context):
    if not is_admin(update.effective_user.id): return
    admins = load_admins()
    users = load(USERS_FILE)
    msg = "👑 **Admins List**\n━━━━━━━━━━━━━━━━━━\n\n"
    for i, uid in enumerate(admins["list"], 1):
        data = users.get(str(uid), {"name": "Unknown", "username": "N/A"})
        tag = " (Master 👑)" if uid == ADMIN_ID else ""
        uname = f"@{data['username']}" if data['username']!="N/A" else "@N/A"
        msg += f"{i}. {data['name']}{tag}\n👤 {uname}\n🆔 ID: `{uid}`\n\n"
    msg += "_ID pe tap karke copy karo_"
    await update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)

async def reset_bot(update, context):
    if not is_master(update.effective_user.id): return
    save(SETTINGS_FILE, DEFAULT_SETTINGS.copy())
    await update.message.reply_text("♻️ Bot Reset Done ✅")

async def set_name(update, context):
    if not is_admin(update.effective_user.id): return
    if not context.args: await update.message.reply_text("Usage: /setname Khushi"); return
    s=get_settings(); s["name"]=" ".join(context.args); save(SETTINGS_FILE,s); await update.message.reply_text(f"✏️ Name set to {s['name']} ✅")

async def set_code(update, context):
    if not is_admin(update.effective_user.id): return
    if not context.args: await update.message.reply_text("Usage: /setcode 6118588149"); return
    s=get_settings(); s["code"]=context.args[0]; save(SETTINGS_FILE,s); await update.message.reply_text(f"🔐 Code set to {s['code']} ✅")

async def set_insta(update, context):
    if not is_admin(update.effective_user.id): return
    if not context.args: await update.message.reply_text("Usage: /setinsta myselfkhushi03"); return
    raw = context.args[0].strip().replace("@","")
    if "instagram.com" in raw or "http" in raw:
        link = raw
        if not link.startswith("http"): link = "https://" + link
    else:
        username = raw.split("/")[-1].replace("@","")
        link = f"https://www.instagram.com/{username}"
    s=get_settings(); s["insta"]=link; save(SETTINGS_FILE,s)
    await update.message.reply_text(f"🔗 Insta set to {s['insta']} ✅")

async def set_font(update, context):
    if not is_admin(update.effective_user.id): return
    if not context.args: await update.message.reply_text("Usage: /setfont normal OR small"); return
    f=context.args[0].lower()
    if f not in ["normal","small"]: await update.message.reply_text("Use: normal / small"); return
    s=get_settings(); s["font"]=f; save(SETTINGS_FILE,s); await update.message.reply_text(f"🔤 Font set to {f} ✅")

async def set_timer(update, context):
    if not is_admin(update.effective_user.id): return
    if not context.args:
        s=get_settings()
        await update.message.reply_text(f"⏱️ Current timer: {format_timer(s.get('timer',0))}"); return
    sec=parse_timer_str(context.args[0])
    if sec is None: await update.message.reply_text("Use: 1m, 5m, 30s, 1h, 0"); return
    s=get_settings(); s["timer"]=sec; save(SETTINGS_FILE,s)
    await update.message.reply_text(f"⏱️ Timer set to {format_timer(sec)} ✅")

async def set_group(update, context):
    if not is_admin(update.effective_user.id): return
    if not context.args:
        s=get_settings(); st="Enabled ✅" if s.get("group",True) else "Disabled ❌"
        await update.message.reply_text(f"Group is {st}"); return
    val=context.args[0].lower(); s=get_settings()
    if val=="on": s["group"]=True; save(SETTINGS_FILE,s); await update.message.reply_text("🌐 Group enabled ✅")
    else: s["group"]=False; save(SETTINGS_FILE,s); await update.message.reply_text("🌐 Group disabled ❌")

async def add_photo(update, context):
    if not is_admin(update.effective_user.id): return
    if not update.message.reply_to_message or not update.message.reply_to_message.photo:
        await update.message.reply_text("Reply to a photo with /add"); return
    sec=None
    if context.args: sec=parse_timer_str(context.args[0])
    file=await update.message.reply_to_message.photo[-1].get_file()
    path=os.path.join(PHOTO_FOLDER, f"{int(time.time()*1000)}.jpg")
    await file.download_to_drive(path)
    s=get_settings()
    if sec is not None:
        s["timer"]=sec; save(SETTINGS_FILE,s)
        await update.message.reply_text(f"📸 Photo added with timer {format_timer(sec)} ✅ Total: {len(get_photos())}")
    else:
        await update.message.reply_text(f"📸 Photo added ✅ Total: {len(get_photos())}")

async def ban(update, context):
    if not is_admin(update.effective_user.id): return
    if not context.args: await update.message.reply_text("Usage: /ban user_id 1d / perm"); return
    uid=context.args[0]; dur=context.args[1] if len(context.args)>1 else "perm"
    exp=parse_time(dur); b=load(BANNED_FILE); b[uid]=exp; save(BANNED_FILE,b); await update.message.reply_text(f"🚫 User {uid} banned for {dur} ✅")

async def unban(update, context):
    if not is_admin(update.effective_user.id): return
    if not context.args: await update.message.reply_text("Usage: /unban user_id"); return
    b=load(BANNED_FILE); b.pop(context.args[0],None); save(BANNED_FILE,b); await update.message.reply_text(f"✅ User {context.args[0]} unbanned")

async def broadcast(update, context):
    if not is_admin(update.effective_user.id): return
    users=load(USERS_FILE)
    if not context.args and not update.message.reply_to_message: await update.message.reply_text("Usage: /broadcast all message"); return
    target=context.args[0].lower() if context.args else "all"
    if update.message.reply_to_message:
        msg=update.message.reply_to_message
        if target=="all":
            c=0
            for uid in users:
                try: await msg.copy(chat_id=int(uid), protect_content=True); c+=1
                except: pass
            await update.message.reply_text(f"📢 Broadcast sent to {c} users ✅")
        else:
            try: await msg.copy(chat_id=int(target), protect_content=True); await update.message.reply_text(f"✅ Sent to {target}")
            except Exception as e: await update.message.reply_text(f"Failed: {e}")
        return
    if target=="all":
        text=" ".join(context.args[1:])
        if not text: await update.message.reply_text("Usage: /broadcast all Hello"); return
        c=0
        for uid in users:
            try: await context.bot.send_message(chat_id=int(uid), text=text, protect_content=True); c+=1
            except: pass
        await update.message.reply_text(f"📢 Broadcast sent to {c} users ✅")
    else:
        try:
            uid=int(target); text=" ".join(context.args[1:])
            if not text: await update.message.reply_text("Usage: /broadcast user_id message"); return
            await context.bot.send_message(chat_id=uid, text=text, protect_content=True)
            await update.message.reply_text(f"✅ Sent to {uid}")
        except: await update.message.reply_text("Invalid ID")

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
    print("Bot started - Master Admin System")
    app.run_polling(drop_pending_updates=True)

if __name__=="__main__": main()
