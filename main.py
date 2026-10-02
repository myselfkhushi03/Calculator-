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

USERS_FILE="users.json"; BANNED_FILE="banned.json"; SETTINGS_FILE="settings.json"; ADMINS_FILE="admins.json"
PHOTO_FOLDER="photos"; os.makedirs(PHOTO_FOLDER, exist_ok=True)
PENDING_ADMIN_MSG = {}

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
    "protect": True, # True = forwarding & SS blocked, False = allowed
    "welcome":"✨ Hey {user} ✨\n\nWelcome to {name}'s Premium Vault 💎\n━━━━━━━━━━━━━━━━━━\n\nHey, I'm {name} — glad you found me! 💖\n\nYou've unlocked my exclusive private collection 🔐\nOne last step to get access.\n\n👤 Name: {user}\n🆔 ID: {id}\n\n💌 Send the secret code to unlock the vault."
}

def get_settings():
    s=load(SETTINGS_FILE)
    if not s:
        s=DEFAULT_SETTINGS.copy()
        save(SETTINGS_FILE,s)
    s.setdefault("protect", True)
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
    # Normal admin commands
    cmds=[
        BotCommand("start", "🚀 Start bot"),
        BotCommand("info", "👤 User info"),
        BotCommand("admin", "📩 Contact admin"),
        BotCommand("status", "📊 Bot Status"),
        BotCommand("users", "👥 User List"),
        BotCommand("admins", "👑 Admins List"),
        BotCommand("setname", "✏️ Set name"),
        BotCommand("setcode", "🔐 Set code"),
        BotCommand("setinsta", "🔗 Set Insta"),
        BotCommand("setfont", "🔤 Font"),
        BotCommand("settime", "⏱️ Timer"),
        BotCommand("add", "📸 Add photo"),
        BotCommand("group", "🌐 Group on/off"),
        BotCommand("ban", "🚫 Ban"),
        BotCommand("unban", "✅ Unban"),
        BotCommand("broadcast", "📢 Broadcast")
    ]
    # Master only commands
    if is_master_user or admin_id==ADMIN_ID:
        cmds.extend([
            BotCommand("addadmin", "➕ Add admin (Master)"),
            BotCommand("removeadmin", "➖ Remove admin (Master)"),
            BotCommand("protect", "🔒 Protect on/off (Master)"),
            BotCommand("reset", "♻️ Reset (Master)")
        ])
    try: await bot.set_my_commands(cmds, scope=BotCommandScopeChat(chat_id=admin_id))
    except: pass

async def setup_commands(app):
    # Normal users - NO /info command
    await app.bot.set_my_commands([
        BotCommand("start", "🚀 Start bot"),
        BotCommand("admin", "📩 Contact admin")
    ], scope=BotCommandScopeDefault())

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
    btn=[[InlineKeyboardButton(f"💎 Follow {s['name']} on Instagram", url=s["insta"])]]
    await update.message.reply_text(welcome, reply_markup=InlineKeyboardMarkup(btn), protect_content=s.get("protect", True))

async def check_code(update, context):
    if update.effective_user.id in PENDING_ADMIN_MSG:
        user_msg = update.message.text
        user = update.effective_user
        PENDING_ADMIN_MSG.pop(update.effective_user.id, None)
        for aid in load_admins().get("list", []):
            try:
                await context.bot.send_message(chat_id=aid, text=f"📩 **New User Message**\n━━━━━━━━━━━━━━━\n👤 Name: {user.first_name}\n🆔 ID: `{user.id}`\n🔗 Username: @{user.username if user.username else 'N/A'}\n━━━━━━━━━━━━━━━\n💬 Message: {user_msg}", parse_mode=ParseMode.MARKDOWN)
            except: pass
        await update.message.reply_text("✅ **Your message has been sent to all admins.** 💌", parse_mode=ParseMode.MARKDOWN)
        return
    s=get_settings()
    if is_banned(update.effective_user.id): return
    if update.message.text.strip()!=s["code"]: return
    all_photos=get_photos()
    if len(all_photos)==0:
        await update.message.reply_text(f"📭 No photos yet!", protect_content=s.get("protect", True))
        return
    uid=str(update.effective_user.id)
    users=load(USERS_FILE)
    if uid in users:
        users[uid]["verified"]=True
        save(USERS_FILE,users)
    timer_sec=s.get("timer",0)
    to_send=random.sample(all_photos, min(2, len(all_photos)))
    await update.message.reply_text(f"✨ **Access Granted!** Welcome to {s['name']}'s Premium Vault 💎", parse_mode=ParseMode.MARKDOWN, protect_content=s.get("protect", True))
    for i,p in enumerate(to_send,1):
        cap=apply_font(f"Exclusive for you, {update.effective_user.first_name} 💖 • {i}/{len(to_send)}\nFrom {s['name']} with love ✨", s.get("font","normal"))
        btn=[[InlineKeyboardButton(f"💎 Follow {s['name']}", url=s["insta"])]]
        sent=await update.message.reply_photo(open(p,"rb"), caption=cap, reply_markup=InlineKeyboardMarkup(btn), protect_content=s.get("protect", True))
        if timer_sec>0 and context.job_queue:
            context.job_queue.run_once(delete_job, timer_sec, chat_id=update.effective_chat.id, data=sent.message_id)
    if timer_sec>0: await update.message.reply_text(f"⏳ Auto-delete in {format_timer(timer_sec)}", protect_content=s.get("protect", True))

async def info_cmd(update, context):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ This command is for admins only.")
        return
    if is_banned(update.effective_user.id): return
    target_id = update.effective_user.id
    if context.args:
        try: target_id = int(context.args[0])
        except: pass
    users = load(USERS_FILE)
    data = users.get(str(target_id), {"name": update.effective_user.first_name, "username": update.effective_user.username or "N/A"})
    name = data.get("name","Unknown")
    username = data.get("username","N/A")
    profile_url = f"https://t.me/{username}" if username!="N/A" and username else f"tg://user?id={target_id}"
    text = f"👤 **User Info - Premium**\n━━━━━━━━━━━━━━━━━━\n**Name:** {name}\n**Username:** @{username}\n**ID:** `{target_id}`\n**Profile:** [Click to Open]({profile_url})\n**Direct Link:** [Tap to Chat](tg://user?id={target_id})\n━━━━━━━━━━━━━━━━━━\n_Tap on ID to copy_"
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)

async def admin_contact(update, context):
    if is_banned(update.effective_user.id): return
    if context.args:
        user_msg = " ".join(context.args)
        user = update.effective_user
        for aid in load_admins().get("list", []):
            try: await context.bot.send_message(chat_id=aid, text=f"📩 **New User Message**\n━━━━━━━━━━━━━━━\n👤 Name: {user.first_name}\n🆔 ID: `{user.id}`\n🔗 Username: @{user.username if user.username else 'N/A'}\n━━━━━━━━━━━━━━━\n💬 Message: {user_msg}", parse_mode=ParseMode.MARKDOWN)
            except: pass
        await update.message.reply_text("✅ **Your message has been sent to all admins.** 💌", parse_mode=ParseMode.MARKDOWN)
    else:
        PENDING_ADMIN_MSG[update.effective_user.id] = True
        await update.message.reply_text("✍️ **Send your message now, it will be forwarded to admin.**", parse_mode=ParseMode.MARKDOWN)

async def protect_cmd(update, context):
    if not is_master(update.effective_user.id):
        await update.message.reply_text("❌ Only Master Admin can control forwarding & screenshot protection!")
        return
    if not context.args:
        s=get_settings()
        status = "ON 🔒 (Forwarding & Screenshot Blocked)" if s.get("protect", True) else "OFF 🔓 (Forwarding Allowed)"
        await update.message.reply_text(f"🔒 **Current Protection:** {status}\n\nUsage:\n/protect on - Block forwarding & SS\n/protect off - Allow forwarding", parse_mode=ParseMode.MARKDOWN)
        return
    val = context.args[0].lower()
    s=get_settings()
    if val=="on":
        s["protect"]=True
        save(SETTINGS_FILE,s)
        await update.message.reply_text("🔒 **Protection ON** ✅\nForwarding and Screenshots are now blocked.", parse_mode=ParseMode.MARKDOWN)
    elif val=="off":
        s["protect"]=False
        save(SETTINGS_FILE,s)
        await update.message.reply_text("🔓 **Protection OFF** ✅\nUsers can now forward and take screenshots.", parse_mode=ParseMode.MARKDOWN)
    else:
        await update.message.reply_text("Usage: /protect on or /protect off")

async def status(update, context):
    if not is_admin(update.effective_user.id): return
    s=get_settings(); users=load(USERS_FILE); banned=load(BANNED_FILE)
    verified = sum(1 for u in users.values() if u.get('verified'))
    prot = "ON 🔒" if s.get("protect", True) else "OFF 🔓"
    text = f"📊 **Bot Premium Status**\n━━━━━━━━━━━━━━━━━━\n👑 Name: {s['name']}\n🔗 Insta: {s['insta']}\n🔐 Code: `{s['code']}`\n🔒 Protect: {prot}\n⏱️ Timer: {format_timer(s.get('timer',0))}\n━━━━━━━━━━━━━━━━━━\n📸 Photos: {len(get_photos())}\n👥 Users: {len(users)}\n✅ Verified: {verified}\n🚫 Banned: {len(banned)}\n👑 Admins: {len(load_admins().get('list',[]))}\n━━━━━━━━━━━━━━━━━━"
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)

async def users_list(update, context):
    if not is_admin(update.effective_user.id): return
    users=load(USERS_FILE)
    if not users: await update.message.reply_text("No users yet 📭"); return
    header = f"📊 **Users - Full Details**\n━━━━━━━━━━━━━━━━━━\n👥 Total: {len(users)}\n━━━━━━━━━━━━━━━━━━\n\n"
    msg = header
    for idx, (uid, data) in enumerate(users.items(), 1):
        name = data.get("name","Unknown")
        username = data.get("username","N/A")
        if username!="N/A" and username:
            uname_md = f"[@{username}](https://t.me/{username})"
            open_link = f"https://t.me/{username}"
        else:
            uname_md = "@N/A"
            open_link = f"tg://user?id={uid}"
        msg += f"{idx}. **{name}**\n👤 Username: {uname_md}\n🆔 ID: `{uid}`\n🔗 [Open]({open_link}) | [Direct](tg://user?id={uid})\n\n"
        if len(msg) > 3500:
            await update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=True)
            msg = ""
    if msg!=header: await update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=True)

async def add_admin(update, context):
    if not is_master(update.effective_user.id): await update.message.reply_text("❌ Only Master can add admins!"); return
    if not context.args: await update.message.reply_text("Usage: /addadmin user_id"); return
    try: new_id = int(context.args[0])
    except: await update.message.reply_text("Invalid ID"); return
    admins = load_admins()
    if new_id in admins["list"]: await update.message.reply_text("Already an admin ✅"); return
    admins["list"].append(new_id); save(ADMINS_FILE, admins)
    await refresh_commands_for_admin(context.bot, new_id, is_master_user=False)
    await update.message.reply_text(f"✅ User `{new_id}` is now admin!", parse_mode=ParseMode.MARKDOWN)
    try: await context.bot.send_message(new_id, "🎉 **You are now admin!**\nSend /start to see menu.", parse_mode=ParseMode.MARKDOWN)
    except: pass

async def remove_admin(update, context):
    if not is_master(update.effective_user.id): await update.message.reply_text("❌ Only Master can remove!"); return
    if not context.args: await update.message.reply_text("Usage: /removeadmin user_id"); return
    try: rem_id = int(context.args[0])
    except: await update.message.reply_text("Invalid ID"); return
    if rem_id == ADMIN_ID: await update.message.reply_text("❌ Cannot remove Master!"); return
    admins = load_admins()
    if rem_id not in admins["list"]: await update.message.reply_text("Not an admin"); return
    admins["list"].remove(rem_id); save(ADMINS_FILE, admins)
    try: await context.bot.set_my_commands([BotCommand("start", "🚀 Start bot"), BotCommand("admin", "📩 Contact admin")], scope=BotCommandScopeChat(chat_id=rem_id))
    except: pass
    await update.message.reply_text(f"✅ Admin `{rem_id}` removed.", parse_mode=ParseMode.MARKDOWN)

async def admins_list(update, context):
    if not is_admin(update.effective_user.id): return
    admins = load_admins(); users = load(USERS_FILE)
    msg = "👑 **Admins List**\n━━━━━━━━━━━━━━━━━━\n\n"
    for i, uid in enumerate(admins["list"], 1):
        data = users.get(str(uid), {"name": "Unknown", "username": "N/A"})
        tag = " (Master 👑)" if uid == ADMIN_ID else ""
        msg += f"{i}. {data['name']}{tag}\n👤 @{data['username']}\n🆔 ID: `{uid}`\n\n"
    await update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)

async def reset_bot(update, context):
    if not is_master(update.effective_user.id): await update.message.reply_text("❌ Only Master can reset!"); return
    save(SETTINGS_FILE, DEFAULT_SETTINGS.copy())
    await update.message.reply_text("♻️ Bot reset to default ✅")

async def set_name(update, context):
    if not is_admin(update.effective_user.id): return
    if not context.args: await update.message.reply_text("Usage: /setname Khushi"); return
    s=get_settings(); s["name"]=" ".join(context.args); save(SETTINGS_FILE,s); await update.message.reply_text(f"Name set to {s['name']} ✅")
async def set_code(update, context):
    if not is_admin(update.effective_user.id): return
    if not context.args: await update.message.reply_text("Usage: /setcode 1234"); return
    s=get_settings(); s["code"]=context.args[0]; save(SETTINGS_FILE,s); await update.message.reply_text(f"Code set to {s['code']} ✅")
async def set_insta(update, context):
    if not is_admin(update.effective_user.id): return
    if not context.args: await update.message.reply_text("Usage: /setinsta username"); return
    raw = context.args[0].strip().replace("@","")
    link = raw if "http" in raw else f"https://www.instagram.com/{raw.split('/')[-1]}"
    s=get_settings(); s["insta"]=link; save(SETTINGS_FILE,s); await update.message.reply_text(f"Insta set to {s['insta']} ✅")
async def set_font(update, context):
    if not is_admin(update.effective_user.id): return
    if not context.args: await update.message.reply_text("Usage: /setfont normal/small"); return
    s=get_settings(); s["font"]=context.args[0].lower(); save(SETTINGS_FILE,s); await update.message.reply_text(f"Font set to {s['font']} ✅")
async def set_timer(update, context):
    if not is_admin(update.effective_user.id): return
    if not context.args: await update.message.reply_text(f"Current: {format_timer(get_settings().get('timer',0))}"); return
    sec=parse_timer_str(context.args[0])
    if sec is None: await update.message.reply_text("Invalid, use 1m, 5m, 30s, 0"); return
    s=get_settings(); s["timer"]=sec; save(SETTINGS_FILE,s); await update.message.reply_text(f"Timer set to {format_timer(sec)} ✅")
async def set_group(update, context):
    if not is_admin(update.effective_user.id): return
    if not context.args: await update.message.reply_text(f"Group is {'Enabled' if get_settings().get('group',True) else 'Disabled'}"); return
    s=get_settings(); s["group"]=context.args[0].lower()=="on"; save(SETTINGS_FILE,s); await update.message.reply_text(f"Group {'enabled ✅' if s['group'] else 'disabled ❌'}")
async def add_photo(update, context):
    if not is_admin(update.effective_user.id): return
    if not update.message.reply_to_message or not update.message.reply_to_message.photo: await update.message.reply_text("Reply to a photo with /add"); return
    file=await update.message.reply_to_message.photo[-1].get_file()
    path=os.path.join(PHOTO_FOLDER, f"{int(time.time()*1000)}.jpg")
    await file.download_to_drive(path)
    await update.message.reply_text(f"Photo added ✅ Total: {len(get_photos())}")
async def ban(update, context):
    if not is_admin(update.effective_user.id): return
    if not context.args: await update.message.reply_text("Usage: /ban user_id 1d/perm"); return
    uid=context.args[0]; dur=context.args[1] if len(context.args)>1 else "perm"
    b=load(BANNED_FILE); b[uid]=parse_time(dur); save(BANNED_FILE,b); await update.message.reply_text(f"User {uid} banned for {dur} ✅")
async def unban(update, context):
    if not is_admin(update.effective_user.id): return
    if not context.args: await update.message.reply_text("Usage: /unban user_id"); return
    b=load(BANNED_FILE); b.pop(context.args[0],None); save(BANNED_FILE,b); await update.message.reply_text(f"User {context.args[0]} unbanned ✅")
async def broadcast(update, context):
    if not is_admin(update.effective_user.id): return
    users=load(USERS_FILE)
    if not context.args and not update.message.reply_to_message: await update.message.reply_text("Usage: /broadcast all message"); return
    if update.message.reply_to_message:
        c=0
        for uid in users:
            try: await update.message.reply_to_message.copy(chat_id=int(uid), protect_content=get_settings().get("protect", True)); c+=1
            except: pass
        await update.message.reply_text(f"Broadcast sent to {c} users ✅")
    else:
        text=" ".join(context.args[1:]) if context.args[0].lower()=="all" else " ".join(context.args)
        c=0
        for uid in users:
            try: await context.bot.send_message(chat_id=int(uid), text=text, protect_content=get_settings().get("protect", True)); c+=1
            except: pass
        await update.message.reply_text(f"Broadcast sent to {c} users ✅")

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
    print("Bot started - Premium with protect control")
    app.run_polling(drop_pending_updates=True)

if __name__=="__main__": main()
