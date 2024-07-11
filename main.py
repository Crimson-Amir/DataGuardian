from create_database import create; create()
from utilities import FindText, handle_functions_error, UserNotFound
from notification.check_addreses_ping import Check10, Check20, Check30
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, CallbackQueryHandler
from private import telegram_bot_token
from ipGuardian.ip_guardian import ip_guardian_menu, add_ip_conversation
from userSetting import setting_menu
from ipGuardian.myIPs import ip_guardian_setting_menu, ContryNotification, ChangeAddressStatus,address_setting
from user.registerCore import RegisterUser
from admin.adminTelegram import notify_admin


logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

@handle_functions_error
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_detail = update.effective_chat
    try:
        ft_instance = FindText(update, context, notify_user=False)
        text = await ft_instance.find_text('start_menu')
        main_keyboard = [
            [InlineKeyboardButton(await ft_instance.find_keyboard('main_menu_ip_guardian'), callback_data='ip_guardian_menu'),
             InlineKeyboardButton(await ft_instance.find_keyboard('main_menu_virtualizor'), callback_data='not_ready_yet')],
            [InlineKeyboardButton(await ft_instance.find_keyboard('setting'), callback_data='setting_menu')],
        ]
        if update.callback_query:
            await update.callback_query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(main_keyboard), parse_mode='html')
            return
        await context.bot.send_message(chat_id=user_detail.id, text=text, reply_markup=InlineKeyboardMarkup(main_keyboard), parse_mode='html')

    except UserNotFound:
        text = '<b>Please choose your language:</b>'
        context.user_data['register_user_referral_code'] = context.args[0] if context.args else None
        keyboard = [[InlineKeyboardButton('English', callback_data='register_user_en'),
                     InlineKeyboardButton('Farsi', callback_data='register_user_fa')]]
        await context.bot.send_message(chat_id=user_detail.id, text=text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='html')

    except Exception as e:
        raise e

@handle_functions_error
async def register_user(update, context):
    user_detail = update.effective_chat
    query = update.callback_query
    selected_language = query.data.replace('register_user_', '')
    user_referral_code = context.user_data.get('register_user_referral_code')
    await RegisterUser().register(user_detail, user_referral_code, selected_language)
    await notify_admin(update, context, selected_language, user_referral_code)
    return await start(update, context)


if __name__ == '__main__':
    application = ApplicationBuilder().token(telegram_bot_token).build()

    # start section
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CallbackQueryHandler(register_user, pattern='register_user_(.*)'))
    application.add_handler(CallbackQueryHandler(start, pattern='main_menu'))

    # ip guardian
    country_notification = ContryNotification()
    change_country_status = ChangeAddressStatus()
    application.add_handler(add_ip_conversation)

    application.add_handler(CallbackQueryHandler(ip_guardian_menu, pattern='ip_guardian_menu'))
    application.add_handler(CallbackQueryHandler(ip_guardian_setting_menu, pattern='ip_guardian_setting_menu'))
    application.add_handler(CallbackQueryHandler(country_notification.country_notification_config, pattern='country_notification_config_(.*)'))
    application.add_handler(CallbackQueryHandler(country_notification.country_ping_notification, pattern='country_ping_notification_(.*)'))
    application.add_handler(CallbackQueryHandler(change_country_status.change_status, pattern='change_address_satus_(.*)'))

    # setting
    application.add_handler(CallbackQueryHandler(setting_menu, pattern='setting_menu'))
    application.add_handler(CallbackQueryHandler(address_setting, pattern='address_setting_(.*)'))

    # notification
    application.job_queue.run_repeating(Check10().execute, interval=60 * 10, first=0)
    application.job_queue.run_repeating(Check20().execute, interval=60 * 20, first=0)
    application.job_queue.run_repeating(Check30().execute, interval=60 * 30, first=0)

    application.run_polling()

