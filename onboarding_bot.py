# onboarding_bot.py
# Run: pip install python-telegram-bot==20.3
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# -----------------------------
# CONFIG (from environment variables)
# -----------------------------
BOT_TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_ID = int(os.environ.get("ADMIN_ID", 0))

if not BOT_TOKEN or not ADMIN_ID:
    raise Exception("BOT_TOKEN or ADMIN_ID environment variable not set!")

# -----------------------------
# In-memory storage
# -----------------------------
user_steps = {}       # { user_id: step_number }
user_choices = {}     # { user_id: broker_choice }

# Onboarding steps
steps = [
    "✅ *Step 1: Choose Your Broker*\n\nPick one of the brokers below to sign up and create your account.",
    "✅ *Step 2: Open a Live Account*\n\nOnce logged in, go to *Open Live Account* and set your leverage to *200X*.",
    "✅ *Step 3: Make Your Deposit*\n\n1. Fund your account with a minimum of *$100* to get started.\n2. Recommended: at least $100 to see decent profit.",
    "✅ *Step 4: DM Me on Telegram*\n\nSend me a message 👉 @AbelMelendez with a screenshot once you’re done.\nI’ll add you into the *Free Trading Signals Group* 🚀"
]

# -----------------------------
# Welcome Message
# -----------------------------
async def send_welcome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_steps[user_id] = -1
    welcome_text = (
        "👋 *Welcome to the Free Trading Community!*\n\n"
        "Here you’ll learn how to:\n"
        "• Join our free signals group 📊\n"
        "• Follow chart markups and signals 📈\n"
        "• Occasionally join live trading sessions 🎥\n\n"
        "Ready to get started?"
    )
    keyboard = [[InlineKeyboardButton("🚀 Get Started", callback_data="begin")]]
    if update.message:
        await update.message.reply_text(welcome_text, parse_mode="Markdown",
                                        reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        await update.callback_query.message.edit_text(welcome_text, parse_mode="Markdown",
                                                      reply_markup=InlineKeyboardMarkup(keyboard))

# -----------------------------
# Start / Restart Commands
# -----------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await send_welcome(update, context)

async def restart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await send_welcome(update, context)

# -----------------------------
# Send Steps
# -----------------------------
async def send_step(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int):
    step = user_steps[user_id]
    text = steps[step]

    if step == 0:
        keyboard = [
            [InlineKeyboardButton("✅ Select Hankotrade", callback_data="broker_hanko"),
             InlineKeyboardButton("🌐 Open Link", url="https://login.hankotrade.com/register?refLink=NTc=&refRm=11")],
            [InlineKeyboardButton("✅ Select AAAFX", callback_data="broker_aaafx"),
             InlineKeyboardButton("🌐 Open Link", url="https://app.aaafx.com/register?refLink=NTI0OA==&refRm=11")],
            [InlineKeyboardButton("➡️ Next", callback_data="next")]
        ]
    elif step < len(steps) - 1:
        keyboard = [[InlineKeyboardButton("➡️ Next", callback_data="next")]]
    else:
        keyboard = [[InlineKeyboardButton("✅ Done", callback_data="done")]]

    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.callback_query:
        await update.callback_query.message.edit_text(text, parse_mode="Markdown",
                                                      reply_markup=reply_markup, disable_web_page_preview=True)
    else:
        await update.message.reply_text(text, parse_mode="Markdown",
                                        reply_markup=reply_markup, disable_web_page_preview=True)

# -----------------------------
# Handle Button Clicks
# -----------------------------
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()

    if query.data == "begin":
        user_steps[user_id] = 0
        await send_step(update, context, user_id)

    elif query.data == "next":
        if user_steps[user_id] == 0 and user_id not in user_choices:
            await query.answer("⚠️ Please select a broker before continuing!", show_alert=True)
            return
        user_steps[user_id] += 1
        await send_step(update, context, user_id)

    elif query.data == "done":
        if user_steps.get(user_id, -1) < len(steps) - 1:
            await query.answer("⚠️ Please finish all steps first!", show_alert=True)
            return

        choice_text = user_choices.get(user_id, "No broker selected 🤔")

        try:
            await context.bot.send_message(
                chat_id=ADMIN_ID,
                text=f"🆕 New signup!\nUser: @{query.from_user.username}\nBroker: {choice_text}\nCompleted onboarding ✅"
            )
        except Exception as e:
            print("Failed to notify admin:", e)

        keyboard = [[InlineKeyboardButton("🔄 Start Over", callback_data="restart")]]
        await query.message.edit_text(
            f"🎉 Awesome! You’ve completed all steps.\n\n"
            f"👉 Don’t forget to DM @AbelMelendez with your screenshot so you can be added!\n\n"
            f"📌 Broker you chose: *{choice_text}*",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    elif query.data == "broker_hanko":
        user_choices[user_id] = "Hankotrade - ACT Trader"
        await query.answer("✅ Saved: Hankotrade selected")

    elif query.data == "broker_aaafx":
        user_choices[user_id] = "AAAFX - MT4/5"
        await query.answer("✅ Saved: AAAFX selected")

    elif query.data == "restart":
        await send_welcome(update, context)

# -----------------------------
# MAIN
# -----------------------------
def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("restart", restart))
    app.add_handler(CallbackQueryHandler(button))
    app.run_polling()

if __name__ == "__main__":
    main()
