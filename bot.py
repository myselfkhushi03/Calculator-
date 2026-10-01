import os
import telebot
from telebot import types

TOKEN = os.environ.get("BOT_TOKEN")  # Render pe Env me daalna
bot = telebot.TeleBot(TOKEN)

user_data = {}

def get_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=4)
    btns = [
        types.InlineKeyboardButton("C", callback_data="C"),
        types.InlineKeyboardButton("⌫", callback_data="⌫"),
        types.InlineKeyboardButton("%", callback_data="%"),
        types.InlineKeyboardButton("÷", callback_data="/"),
        types.InlineKeyboardButton("7", callback_data="7"),
        types.InlineKeyboardButton("8", callback_data="8"),
        types.InlineKeyboardButton("9", callback_data="9"),
        types.InlineKeyboardButton("×", callback_data="*"),
        types.InlineKeyboardButton("4", callback_data="4"),
        types.InlineKeyboardButton("5", callback_data="5"),
        types.InlineKeyboardButton("6", callback_data="6"),
        types.InlineKeyboardButton("-", callback_data="-"),
        types.InlineKeyboardButton("1", callback_data="1"),
        types.InlineKeyboardButton("2", callback_data="2"),
        types.InlineKeyboardButton("3", callback_data="3"),
        types.InlineKeyboardButton("+", callback_data="+"),
        types.InlineKeyboardButton("00", callback_data="00"),
        types.InlineKeyboardButton("0", callback_data="0"),
        types.InlineKeyboardButton(".", callback_data="."),
        types.InlineKeyboardButton("=", callback_data="="),
    ]
    markup.add(*btns)
    return markup

@bot.message_handler(commands=['start'])
def start(m):
    user_data[m.chat.id] = "0"
    bot.send_message(m.chat.id, f"🧮 **Calculator**\n\n`0`", parse_mode="Markdown", reply_markup=get_keyboard())

@bot.callback_query_handler(func=lambda call: True)
def cb(call):
    chat_id = call.message.chat.id
    curr = user_data.get(chat_id, "0")
    data = call.data
    if data == "C": curr = "0"
    elif data == "⌫": curr = curr[:-1] if len(curr) > 1 else "0"
    elif data == "=":
        try: curr = str(eval(curr.replace('%','/100')))
        except: curr = "Error"
    else:
        curr = data if curr in ["0","Error"] else curr + data
    user_data[chat_id] = curr
    try:
        bot.edit_message_text(f"🧮 **Calculator**\n\n`{curr}`", chat_id, call.message.message_id, parse_mode="Markdown", reply_markup=get_keyboard())
    except: pass

def run_bot():
    bot.infinity_polling()
