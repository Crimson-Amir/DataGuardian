from utilities import FindText, HandleErrors, posgres_manager
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler, CallbackQueryHandler, filters, MessageHandler
from api.checkHostApi import client, PingFactory
from ipGuardian.ip_guardianCore import RegisterIP
from notification.check_addreses_ping import CheckAbstract

GET_IP = 0
handle_errors = HandleErrors()
handle_function_errors, handle_classes_errors = handle_errors.handle_classes_error, handle_errors.handle_classes_error
handle_conversetion_error, handle_queue_error = handle_errors.handle_conversetion_error, handle_errors.handle_queue_error

class FakeUpdate:
    callback_query = None
    class effective_chat: id = None


@handle_function_errors
async def ip_guardian_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_detail = update.effective_chat
    ft_instance = FindText(update, context)
    text = await ft_instance.find_text('select_section')
    main_keyboard = [
        [InlineKeyboardButton(await ft_instance.find_keyboard('add_ip'), callback_data='add_ip')],
        [InlineKeyboardButton(await ft_instance.find_keyboard('view_ips'), callback_data='ip_guardian_setting_menu'),
         InlineKeyboardButton(await ft_instance.find_keyboard('help_button'), callback_data='help_ip')],
        [InlineKeyboardButton(await ft_instance.find_keyboard('back_button'), callback_data='main_menu')],
    ]
    if update.callback_query:
        await update.callback_query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(main_keyboard), parse_mode='html')
        return
    await context.bot.send_message(chat_id=user_detail.id, text=text, reply_markup=InlineKeyboardMarkup(main_keyboard), parse_mode='html')


async def is_user_eligible_to_add_address(user_id):
    fetch_from_db = posgres_manager.execute('query', {'query': """
            SELECT COALESCE(COUNT(a.addressID), 0), ra.max_allow_ip_register 
            FROM Rank ra JOIN UserDetail ud ON ud.rankID = ra.rankID 
            LEFT JOIN Address a ON ud.userID = a.userID 
            WHERE ud.userID = %s
            GROUP BY ur.max_allow_ip_register""", 'params': (user_id,)})

    print(fetch_from_db)
    if fetch_from_db[0][0] < fetch_from_db[0][1]: return True
    return False


@handle_function_errors
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

    if not await is_user_eligible_to_add_address(chat_id):
        text = await ft_instance.find_text('access_denied_for_register_address')
        return await update.callback_query.answer(text, show_alert=True)

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

    get_time = CheckAbstract.run_after
    text = await ft_instance.find_text('waiting_for_check_address')
    text = text.format(get_time + 15)
    message_id = await context.bot.send_message(chat_id=user_id, text=text, parse_mode='html')

    data = {'address': address, 'register_ip_class': register_ip_class, 'user_id': user_id, 'message_id': message_id}
    context.job_queue.run_once(get_ip_request_id, when=get_time, data=data)

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


@handle_queue_error
async def get_ip_request_id(context):
    address = context.job.data.get('address')
    register_ip_class = context.job.data.get('register_ip_class')
    user_id = context.job.data.get('user_id')
    message_id = context.job.data.get('message_id')

    check_host_instance = await client(
        check=PingFactory,
        _host=address,
        max_nodes=55,
        return_request_id = True)

    context.job_queue.run_once(register_ip, when=15, data={'user_id': user_id, 'address': address})
    register_ip_class.message_for_update[user_id] = [check_host_instance, message_id.message_id]


@handle_queue_error
async def register_ip(context):
    data = context.job.data
    user_id = data.get('user_id')
    address = data.get('address')
    update = FakeUpdate().effective_chat.id = user_id
    ft_instance = FindText(update, context)

    register_ip_class = RegisterIP()
    register = await register_ip_class.register_ip(user_id, address)
    message_id = register.get('message_id')
    address_detail_text = register.get('address_detail_text', '')

    if register.get('status', 0):
        text = await ft_instance.find_from_database(user_id, register.get('msg', 'user_error_message'))
        return await context.bot.edit_message_text(
            text=text + f'\n\n{address_detail_text}', chat_id=user_id, message_id=message_id)

    erro_msg = await ft_instance.find_from_database(user_id, register.get('error', ''))
    await context.bot.edit_message_text(text=erro_msg + f'\n\n{address_detail_text}', chat_id=user_id, message_id=message_id)
