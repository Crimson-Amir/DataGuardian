from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from private import admin_chat_ids

async def notify_admin(update: Update, context: ContextTypes.DEFAULT_TYPE, selected_language, entered_with_refferal_link=None):
    user_detail = update.effective_chat

    text = (f'New start bot in {update.callback_query.message.chat.type} chat:'
            f'\n\nFirst name: {user_detail.first_name}'
            f'\nLast name: {user_detail.last_name}'
            f'\nUserName: {user_detail.username}'
            f'\nUserID: <a href=\"tg://user?id={user_detail.id}\">{user_detail.id}</a>'
            f'\nEnered with refferal link: <a href=\"tg://user?id={entered_with_refferal_link}\">{entered_with_refferal_link}</a>'
            f'\nSelected language: {selected_language}')

    await context.bot.send_message(chat_id=admin_chat_ids[0], text=text, parse_mode='html')
