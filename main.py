import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler, ConversationHandler
import os

BOT_TOKEN = os.getenv("BOT_TOKEN")
API_BASE = "https://xpsmm.com/api/v2"

user_api_keys = {}
pending_action = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in user_api_keys:
        await update.message.reply_text("👋 Welcome! Please send your API Key to continue:")
        return 1
    else:
        await show_main_menu(update, context)
        return ConversationHandler.END

async def save_api_key(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_api_keys[user_id] = update.message.text.strip()
    await update.message.reply_text("✅ API Key saved successfully.")
    await show_main_menu(update, context)
    return ConversationHandler.END

async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("📦 Order Status", callback_data="status"),
         InlineKeyboardButton("♻️ Refill", callback_data="refill")],
        [InlineKeyboardButton("❌ Cancel", callback_data="cancel"),
         InlineKeyboardButton("⚡ Speed Up", callback_data="speedup")],
        [InlineKeyboardButton("💰 Balance", callback_data="balance")]
    ]
    await update.message.reply_text("Choose an action:", reply_markup=InlineKeyboardMarkup(keyboard))

async def handle_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    if user_id not in user_api_keys:
        await query.edit_message_text("⚠️ API Key not found. Please use /start to enter it.")
        return

    action = query.data
    if action == "balance":
        await send_balance(query, user_api_keys[user_id])
    else:
        pending_action[user_id] = action
        await query.edit_message_text(f"📩 Please send the Order ID for {action.capitalize()}:")

async def handle_order_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in pending_action or user_id not in user_api_keys:
        return

    order_id = update.message.text.strip()
    action = pending_action.pop(user_id)
    api_key = user_api_keys[user_id]

    if action == "status":
        await send_order_status(update, api_key, order_id)
    elif action == "cancel":
        await cancel_order(update, api_key, order_id)
    elif action == "refill":
        await refill_order(update, api_key, order_id)
    elif action == "speedup":
        await speedup_order(update, api_key, order_id)

async def send_balance(update, api_key):
    res = requests.post(API_BASE, data={"key": api_key, "action": "balance"})
    try:
        data = res.json()
        currency = data.get("currency", "USD")
        balance = data.get("balance", 0)
        await update.edit_message_text(f"💰 Balance: {balance} {currency}")
    except:
        await update.edit_message_text("❌ Failed to fetch balance. Check your API key.")

async def send_order_status(update, api_key, order_id):
    res = requests.post(API_BASE, data={"key": api_key, "action": "status", "order": order_id})
    try:
        data = res.json()
        if "error" in data:
            await update.message.reply_text(f"❌ {data['error']}")
        else:
            status = data.get("status")
            link = data.get("link", "N/A")
            service = data.get("service")
            await update.message.reply_text(
                f"📦 Order Status:\nID: {order_id}\nService: {service}\nLink: {link}\nStatus: {status}")
    except:
        await update.message.reply_text("❌ Failed to fetch status.")

async def cancel_order(update, api_key, order_id):
    res = requests.post(API_BASE, data={"key": api_key, "action": "cancel", "order": order_id})
    try:
        data = res.json()
        if "error" in data:
            await update.message.reply_text(f"❌ {data['error']}")
        else:
            await update.message.reply_text("❌ Cancel request sent!")
    except:
        await update.message.reply_text("❌ Failed to cancel order.")

async def refill_order(update, api_key, order_id):
    res = requests.post(API_BASE, data={"key": api_key, "action": "refill", "order": order_id})
    try:
        data = res.json()
        if "error" in data:
            await update.message.reply_text("♻️ Refill not allowed.")
        else:
            await update.message.reply_text("♻️ Refill request sent!")
    except:
        await update.message.reply_text("❌ Failed to send refill request.")

async def speedup_order(update, api_key, order_id):
    res = requests.post(API_BASE, data={"key": api_key, "action": "status", "order": order_id})
    try:
        data = res.json()
        if "error" in data:
            await update.message.reply_text(f"❌ {data['error']}")
        else:
            await update.message.reply_text("⚡ Speed Up Started ✅")
    except:
        await update.message.reply_text("❌ Failed to process speed up.")

def run_bot():
    app = Application.builder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={1: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_api_key)]},
        fallbacks=[],
    )

    app.add_handler(conv_handler)
    app.add_handler(CallbackQueryHandler(handle_button))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_order_id))

    app.run_polling()

if __name__ == "__main__":
    run_bot()
