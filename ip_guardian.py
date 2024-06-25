from psycopg2 import errorcodes, errors
from utilities import FindText, handle_error, posgres_manager, handle_conversetion_error, status_emoji, get_range_emoji
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler, CallbackQueryHandler, filters, MessageHandler
from api.checkHostApi import client, PingFactory, CleanPingFactory
from language import countries_and_flags

GET_IP = 0
calcuate_percentage_formula = lambda a, b: round((a / b) * 100, 2)

class FakeUpdate:
    callback_query = None
    class effective_chat:
        id = None


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
    context.job_queue.run_once(register_ip_class.register_ip, when=15, name=f'{user_id}_&_{address}')
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


class Singleton(type):
    _instance = {}
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instance:
            cls._instance[cls] = super().__call__(*args, **kwargs)
        return cls._instance[cls]

class RegisterIP(metaclass=Singleton):
    message_for_update = {}
    ip_block_list = []

    @staticmethod
    async def register_to_database(user_id, address, score_percent):
        posgres_manager.execute(
            'transaction', [{
                'query': 'INSERT INTO Address (userID,address,address_name,score_percent) VALUES (%s,%s,%s,%s)',
                'params': (int(user_id), address, address, score_percent)}]
        )
    async def register_ip(self, context):
        job_name = context.job.name.split('_&_')
        user_id = job_name[0]
        address = job_name[1]
        result, message_id = self.message_for_update.pop(user_id)
        update = FakeUpdate().effective_chat.id = user_id
        ft_instance = FindText(update, context)
        get_address_detail = await self.format_ping_checker_text(result)
        try:
            if not get_address_detail: raise ValueError
            score_present, address_detail_text = get_address_detail[2], get_address_detail[1]
            if score_present < 50:
                self.ip_block_list.append(address)
                text = await ft_instance.find_from_database(user_id, 'address_score_not_enough')
                await context.bot.edit_message_text(text=text + f'\n\n{address_detail_text}', chat_id=user_id, message_id=int(message_id))
                return
            text = await ft_instance.find_from_database(user_id, 'address_register_successfull')
            await self.register_to_database(user_id, address, score_present)
            await context.bot.edit_message_text(text=text + f'\n\n{address_detail_text}', chat_id=user_id, message_id=int(message_id))

        except errors.lookup(errorcodes.UNIQUE_VIOLATION):
            await context.bot.edit_message_text(text=await ft_instance.find_from_database(user_id, 'address_is_not_unique'), chat_id=user_id, message_id=int(message_id))
            self.ip_block_list.append(address)
        except Exception as e:
            await context.bot.edit_message_text(text=await ft_instance.find_from_database(user_id, 'user_error_message'), chat_id=user_id, message_id=int(message_id))
            print(e)

    @staticmethod
    async def find_ip_host(result):
        iterable_host = iter(result.values())
        host_ip = 'no ip found'
        for i in range(10):
            host_ip = next(iterable_host).get("host")
            if host_ip != 'no ip found': break
        return host_ip

    async def format_ping_checker_text(self, result):
        get_result = CleanPingFactory()
        result = await get_result.clean_data(result)
        earned_score = result.get("general_score")
        general_scoer = result.get("number_of_country") * 4
        score_present = calcuate_percentage_formula(earned_score, general_scoer)
        host_ip = await self.find_ip_host(result)
        if host_ip == 'no hip found': raise ValueError
        final_text = (f'Host IP: {host_ip}\n'
                      f'Points Received: {earned_score}/{general_scoer} ({score_present}% {get_range_emoji(int(score_present))})\n\n')
        for key, value in result.items():
            if not isinstance(value, dict): continue
            final_text += (
                f'{countries_and_flags.get(key.split(', ')[0], "")} {key}: {value.get("ok_request_count")}/{len(value.get("status_list"))}'
                f' | {round(value.get("min_time"), 2)} - {round(value.get("avg_time"), 2)} - {round(value.get("max_time"), 2)} '
                f'{status_emoji.get(value.get("ok_request_count"), 0)}\n')
        return result, final_text, score_present, host_ip
