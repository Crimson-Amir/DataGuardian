from utilities import FindText, handle_error, UserNotFound, posgres_manager
from create_database import create
create()
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, CallbackQueryHandler
from private import telegram_bot_token
from ip_guardian import ip_guardian_menu, add_ip_conversation

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

@handle_error
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_detail = update.effective_chat
    try:
        ft_instance = FindText(update, context, notify_user=False)
        text = await ft_instance.find_text('start_menu')
        main_keyboard = [
            [InlineKeyboardButton(await ft_instance.find_keyboard('main_menu_ip_guardian'), callback_data='ip_guardian_menu'),
             InlineKeyboardButton(await ft_instance.find_keyboard('main_menu_virtualizor'), callback_data='virtualizor')],
            [InlineKeyboardButton(await ft_instance.find_keyboard('setting'), callback_data='setting')],
        ]
        if update.callback_query:
            await update.callback_query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(main_keyboard), parse_mode='html')
            return
        await context.bot.send_message(chat_id=user_detail.id, text=text, reply_markup=InlineKeyboardMarkup(main_keyboard), parse_mode='html')

    except UserNotFound:
        text = '<b>Please choose your language:</b>'
        context.user_data['register_user_referral_code'] = context.args[0] if context.args else None
        keyboard = [
            [InlineKeyboardButton('English', callback_data='register_user_en'),
             InlineKeyboardButton('Farsi', callback_data='register_user_fa')]
        ]
        await context.bot.send_message(chat_id=user_detail.id, text=text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='html')

    except Exception as e:
        raise e

@handle_error
async def register_user(update, context):
    user_detail = update.effective_chat
    query = update.callback_query
    selected_language = query.data.replace('register_user_', '')
    user_referral_code = context.user_data.get('register_user_referral_code')
    posgres_manager.execute(
        'transaction', [
            {'query': 'INSERT INTO UserDetail (first_name,last_name,username,userID,entered_with_refral_link,language) VALUES (%s,%s,%s,%s,%s,%s)',
             'params':
                 (user_detail.first_name, user_detail.last_name, user_detail.username, user_detail.id, user_referral_code, selected_language)
             }])
    return await start(update, context)


if __name__ == '__main__':
    application = ApplicationBuilder().token(telegram_bot_token).build()

    # start section
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CallbackQueryHandler(register_user, pattern='register_user_(.*)'))
    application.add_handler(CallbackQueryHandler(start, pattern='main_menu'))

    # ip guardian
    application.add_handler(CallbackQueryHandler(ip_guardian_menu, pattern='ip_guardian_menu'))
    application.add_handler(add_ip_conversation)

    # application.job_queue.run_repeating(notification_job, interval=check_every_min * 60, first=0)

    application.run_polling()

