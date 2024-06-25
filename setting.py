from psycopg2 import errorcodes, errors
from utilities import FindText, handle_error, posgres_manager, get_range_emoji
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

@handle_error
async def setting_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_detail = update.effective_chat
    ft_instance = FindText(update, context)
    text = '⚙️ ' + await ft_instance.find_text('select_section')
    main_keyboard = [
        [InlineKeyboardButton(await ft_instance.find_keyboard('ip_guardian_setting'), callback_data='ip_guardian_setting_menu')],
        [InlineKeyboardButton(await ft_instance.find_keyboard('back_button'), callback_data='main_menu')],
    ]
    if update.callback_query:
        await update.callback_query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(main_keyboard), parse_mode='html')
        return
    await context.bot.send_message(chat_id=user_detail.id, text=text, reply_markup=InlineKeyboardMarkup(main_keyboard), parse_mode='html')


@handle_error
async def ip_guardian_setting_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ft_instance = FindText(update, context)
    text = await ft_instance.find_text('select_address')
    get_address_from_db = posgres_manager.execute('query', {'query': 'SELECT address_name,score_percent from Address'})
    if not get_address_from_db:
        text = await ft_instance.find_text('there_is_no_address')
        keyboard = [[InlineKeyboardButton(await ft_instance.find_keyboard('add_ip'), callback_data='add_ip')],
                    [InlineKeyboardButton(await ft_instance.find_keyboard('back_button'), callback_data='main_menu')]]
        await update.callback_query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='html')
        return
    keyboard = [[InlineKeyboardButton(f'{address[0]} [{address[1]}% {get_range_emoji(address[1])}]', callback_data=f'address_setting_{address[0]}')] for address in get_address_from_db]
    keyboard.append([InlineKeyboardButton(await ft_instance.find_keyboard('back_button'), callback_data='main_menu')],)
    await update.callback_query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='html')


