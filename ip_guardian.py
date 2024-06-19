from utilities import FindText, handle_error, posgres_manager, handle_conversetion_error
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler, CallbackQueryHandler, filters, MessageHandler

GET_IP = 0

@handle_error
async def ip_guardian_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_detail = update.effective_chat
    ft_instance = FindText(update, context)
    text = await ft_instance.find_text('select_section')
    main_keyboard = [
        [InlineKeyboardButton(await ft_instance.find_keyboard('add_ip'), callback_data='add_ip')],
        [InlineKeyboardButton(await ft_instance.find_keyboard('view_ips'), callback_data='view_ips'),
         InlineKeyboardButton(await ft_instance.find_keyboard('help_button'), callback_data='help_ip')],
        [InlineKeyboardButton(await ft_instance.find_keyboard('back_button'), callback_data='main_menu')],
    ]
    if update.callback_query:
        await update.callback_query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(main_keyboard), parse_mode='html')
        return
    await context.bot.send_message(chat_id=user_detail.id, text=text, reply_markup=InlineKeyboardMarkup(main_keyboard), parse_mode='html')


@handle_error
async def ip_guardian_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_detail = update.effective_chat
    ft_instance = FindText(update, context)
    text = await ft_instance.find_text('select_section')
    main_keyboard = [
        [InlineKeyboardButton(await ft_instance.find_keyboard('add_ip'), callback_data='add_ip')],
        [InlineKeyboardButton(await ft_instance.find_keyboard('view_ips'), callback_data='view_ips'),
         InlineKeyboardButton(await ft_instance.find_keyboard('help_button'), callback_data='help_ip')],
        [InlineKeyboardButton(await ft_instance.find_keyboard('back_button'), callback_data='main_menu')],
    ]
    if update.callback_query:
        await update.callback_query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(main_keyboard), parse_mode='html')
        return
    await context.bot.send_message(chat_id=user_detail.id, text=text, reply_markup=InlineKeyboardMarkup(main_keyboard), parse_mode='html')


@handle_error
async def cancel_conversation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    ft_instance = FindText(update, context)
    text = await ft_instance.find_text('cancel_message')
    await query.delete_message()
    await query.answer(text)
    return ConversationHandler.END


@handle_conversetion_error
async def add_ip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    ft_instance = FindText(update, context)
    text = await ft_instance.find_text('add_ip_conversation')
    await update.callback_query.answer(text)
    keyboard = [[InlineKeyboardButton(await ft_instance.find_keyboard('cancel_button'), callback_data='cancel_conversation')]]
    await context.bot.send_message(chat_id=chat_id, text=text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='html')
    return GET_IP

@handle_conversetion_error
async def get_ip_and_register(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    address = update.message.text
    await context.bot.send_message(chat_id=chat_id, text=address, parse_mode='html')
    return ConversationHandler.END


add_ip_conversation = ConversationHandler(
    entry_points=[CallbackQueryHandler(add_ip, pattern=r'add_ip')],
    states={
        GET_IP: [MessageHandler(filters.TEXT, get_ip_and_register)],
    },
    fallbacks=[CallbackQueryHandler(cancel_conversation, pattern='cancel_conversation')],
    per_chat=True,
    allow_reentry=True,
    conversation_timeout=1500,
)
