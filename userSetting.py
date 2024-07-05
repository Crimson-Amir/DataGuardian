from utilities import FindText, handle_error
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

@handle_error
async def setting_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_detail = update.effective_chat
    ft_instance = FindText(update, context)
    text = '⚙️ ' + await ft_instance.find_text('select_section')
    main_keyboard = [
        [InlineKeyboardButton(await ft_instance.find_keyboard('ip_guardian_setting'), callback_data='ip_guardian_setting_menu')],
        [InlineKeyboardButton(await ft_instance.find_keyboard('back_button'), callback_data='main_menu')]]
    if update.callback_query:
        return await update.callback_query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(main_keyboard), parse_mode='html')
    await context.bot.send_message(chat_id=user_detail.id, text=text, reply_markup=InlineKeyboardMarkup(main_keyboard), parse_mode='html')

