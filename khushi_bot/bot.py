import os
import logging
from telegram import Update
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    filters, ContextTypes
)

# ============ CONFIG ============
BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"
PHOTO_FOLDER = "photos"

VERIFY_CODE = "6118588149"           # user types this to verify
INSTA_USERNAME = "myselfkhushi03"
TG_USERNAME = "myselfkhushi03"

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# verified users store
verified_users = set()


# ============ /start ============
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if user_id in verified_users:
        await update.message.reply_text(
            "✨ <b>You are already verified!</b>\n\n"
            "Now send any <b>username</b> and I'll send your photos 📸",
            parse_mode="HTML"
        )
        return

    await update.message.reply_text(
        "💎 <b>Welcome to Premium Access</b> 💎\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "🔐 <b>Verification Required</b>\n\n"
        "Please send the <b>secret code</b> to unlock all photos 📸\n\n"
        "<i>Only verified users can access the gallery.</i>",
        parse_mode="HTML"
    )


# ============ VERIFY + SEND PHOTOS ============
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text.strip()

    # --- STEP 1: VERIFICATION ---
    if user_id not in verified_users:
        if text == VERIFY_CODE:
            verified_users.add(user_id)
            await update.message.reply_text(
                "✅ <b>Verification Successful!</b>\n"
                "━━━━━━━━━━━━━━━━━━━━\n\n"
                "🎉 <b>Premium Access Unlocked</b>\n\n"
                "Now send any <b>username</b> and your photos will be delivered instantly 📸",
                parse_mode="HTML"
            )
        else:
            await update.message.reply_text(
                "❌ <b>Invalid Code</b>\n\n"
                "Please send the correct secret code to unlock 🔐",
                parse_mode="HTML"
            )
        return

    # --- STEP 2: SEND PHOTOS ---
    username = text

    if not os.path.exists(PHOTO_FOLDER):
        await update.message.reply_text("❌ Photos folder not found!")
        return

    photos = sorted([
        f for f in os.listdir(PHOTO_FOLDER)
        if f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp'))
    ])

    if not photos:
        await update.message.reply_text("❌ No photos found in folder!")
        return

    # Premium intro
    await update.message.reply_text(
        f"💎 <b>Premium Delivery</b> 💎\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 <b>User:</b> <code>{username}</code>\n"
        f"📸 <b>Photos:</b> {len(photos)}\n"
        f"⏳ <i>Sending now...</i>",
        parse_mode="HTML"
    )

    # Send each photo with clickable links in caption
    for i, photo_name in enumerate(photos, 1):
        path = os.path.join(PHOTO_FOLDER, photo_name)
        caption = (
            f"📸 <b>Photo {i} / {len(photos)}</b>\n"
            f"👤 {username}\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f'📷 <a href="https://instagram.com/{INSTA_USERNAME}">Instagram</a> '
            f'| ✈️ <a href="https://t.me/{TG_USERNAME}">Telegram</a>'
        )
        try:
            with open(path, 'rb') as photo:
                await update.message.reply_photo(
                    photo=photo,
                    caption=caption,
                    parse_mode="HTML"
                )
        except Exception as e:
            print(f"Error: {e}")

    # Premium footer
    await update.message.reply_text(
        "✅ <b>All photos delivered!</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f'💌 Follow for more:\n'
        f'📷 <a href="https://instagram.com/{INSTA_USERNAME}">Instagram</a>\n'
        f'✈️ <a href="https://t.me/{TG_USERNAME}">Telegram</a>\n\n'
        "💎 <i>Thanks for using Premium Service</i>",
        parse_mode="HTML"
    )


# ============ MAIN ============
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
    )

    print("🤖 Bot is running... Press Ctrl+C to stop")
    app.run_polling()


if __name__ == '__main__':
    main()
