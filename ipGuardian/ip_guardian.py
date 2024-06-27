from utilities import FindText, handle_error, handle_conversetion_error
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler, CallbackQueryHandler, filters, MessageHandler
from api.checkHostApi import client, PingFactory
from ipGuardian.ip_guardian_core import RegisterIP

GET_IP = 0
class FakeUpdate:
    callback_query = None
    class effective_chat: id = None

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
    text = await ft_instance.find_text('add_address_conversation')
    await update.callback_query.answer(text)
    keyboard = [[InlineKeyboardButton(await ft_instance.find_keyboard('cancel_button'), callback_data='cancel_conversation')]]
    await context.bot.send_message(chat_id=chat_id, text=text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='html')
    return GET_IP


@handle_conversetion_error
async def get_ip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_chat.id
    address = update.message.text
    ft_instance = FindText(update, context)
    register_ip_class = RegisterIP()
    if address in register_ip_class.ip_block_list:
        await context.bot.send_message(chat_id=user_id, text=await ft_instance.find_text('address_in_block_list'), parse_mode='html')
        return ConversationHandler.END
    check_host_instance = await client(
        check=PingFactory,
        _host=address,
        max_nodes=55,
        return_request_id = True
    )
    context.job_queue.run_once(register_ip, when=15, name=f'{user_id}_&_{address}')
    text = await ft_instance.find_text('waiting_for_check_address')
    message_id = await context.bot.send_message(chat_id=user_id, text=text, parse_mode='html')
    register_ip_class.message_for_update[str(user_id)] = [check_host_instance, message_id.message_id]
    return ConversationHandler.END


add_ip_conversation = ConversationHandler(
    entry_points=[CallbackQueryHandler(add_ip, pattern=r'add_ip')],
    states={
        GET_IP: [MessageHandler(filters.TEXT, get_ip)],
    },
    fallbacks=[CallbackQueryHandler(cancel_conversation, pattern='cancel_conversation')],
    per_chat=True,
    allow_reentry=True,
    conversation_timeout=1500,
)

async def register_ip(context):
    job_name = context.job.name.split('_&_')
    user_id = job_name[0]
    address = job_name[1]
    update = FakeUpdate().effective_chat.id = user_id
    ft_instance = FindText(update, context)

    register_ip_class = RegisterIP()
    register = await register_ip_class.register_ip(user_id, address)
    message_id = register.get('message_id')
    address_detail_text = register.get('address_detail_text', '')

    if register.get('status', 0):
        text = await ft_instance.find_from_database(user_id, register.get('msg', 'user_error_message'))
        await context.bot.edit_message_text(
            text=text + f'\n\n{address_detail_text}', chat_id=user_id, message_id=message_id)
        return

    erro_msg = await ft_instance.find_from_database(user_id, register.get('error', ''))
    await context.bot.edit_message_text(text=erro_msg + f'\n\n{address_detail_text}', chat_id=user_id, message_id=message_id)