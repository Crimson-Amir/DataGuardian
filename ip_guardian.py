from utilities import FindText, handle_error, posgres_manager, handle_conversetion_error
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler, CallbackQueryHandler, filters, MessageHandler
from api.checkHostApi import client, PingFactory, CleanPingFactory
from language import countries_and_flags

GET_IP = 0
calcuate_percentage_formula = lambda a, b: round((a / b) * 100, 2)

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

message_for_update = {}

@handle_conversetion_error
async def get_ip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_chat.id
    address = update.message.text
    check_host_instance = await client(
        check=PingFactory,
        _host=address,
        max_nodes=55,
        return_request_id = True
    )
    context.job_queue.run_once(register_ip, when=15, name=str(user_id))
    ft_instance = FindText(update, context)
    text = await ft_instance.find_text('waiting_for_check_ip')
    message_id = await context.bot.send_message(chat_id=user_id, text=text, parse_mode='html')
    message_for_update[str(user_id)] = [check_host_instance, message_id.message_id]
    return ConversationHandler.END


async def register_ip(context):
    job = context.job
    user_id = job.name
    result, message_id = message_for_update.pop(user_id)
    try:
        get_address_detail = await format_ping_checker_text(result)
        score_present = get_address_detail[2]
        await context.bot.edit_message_text(text=get_address_detail[1], chat_id=user_id, message_id=int(message_id))
    except Exception as e:
        await context.bot.edit_message_text(text='Sorry, Somthing went Wrong!', chat_id=user_id, message_id=int(message_id))
        print(e)


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

async def format_ping_checker_text(result):
    get_result = CleanPingFactory()
    result = await get_result.clean_data(result)
    status_emoji = {0: '❌', 1: '🔴', 2: '🟠', 3: '🟡', 4: '🟢'}
    earned_score = result.get("general_score")
    general_scoer = result.get("number_of_country") * 4
    score_present = calcuate_percentage_formula(earned_score, general_scoer)

    final_text = (f'Host IP: {next(iter(result.values())).get("host")}\n'
                  f'Points Received: {earned_score}/{general_scoer} ({score_present}%)\n\n')
    for key, value in result.items():
        if not isinstance(value, dict): continue
        final_text += (
            f'{countries_and_flags.get(key.split('.')[0][:-1], "")} {key}: {value.get("ok_request_count")}/{len(value.get("status_list"))}'
            f' | {round(value.get("min_time"), 2)} - {round(value.get("avg_time"), 2)} - {round(value.get("max_time"), 2)} '
            f'{status_emoji.get(value.get("ok_request_count"), 0)}\n')
    return result, final_text, score_present

