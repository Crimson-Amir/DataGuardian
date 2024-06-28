import functools
from private import telegram_bot_url, admin_chat_ids, database_detail
# import aiohttp
import requests
from language import text_transaction, keyboard_transaction
from posgres_manager import Client
from telegram.ext import ConversationHandler

default_language = 'en'
posgres_manager = Client(**database_detail)
status_emoji = {0: '❌', 1: '🔴', 2: '🟠', 3: '🟡', 4: '🟢'}
status_range_emoji = {0: '❌', range(1, 50): '🔴', range(50, 70): '🟠', range(70, 85): '🟡', range(85, 100 + 1): '🟢'}

def get_range_emoji(value):
    if value in status_range_emoji:
        return status_range_emoji[value]
    for key in status_range_emoji:
        if isinstance(key, range) and value in key:
            return status_range_emoji[key]
    return None

class UserNotFound(Exception):
    def __init__(self):
        super().__init__("user was't register in bot!")


class FindText:
    def __init__(self, update, context, notify_user=True):
        self._update = update
        self._context = context
        self._notify_user = notify_user

    @staticmethod
    async def language_transaction(text_key, language_code=default_language, section="text") -> str:
        transaction = text_transaction
        if section == "keyboard": transaction = keyboard_transaction
        return transaction.get(text_key, 'user_error_message').get(language_code, 'en')

    @staticmethod
    async def get_language_from_database(user_id):
        return posgres_manager.execute('query', {'query': 'SELECT language FROM UserDetail WHERE userID = %s', 'params': (user_id,)})

    async def find_user_language(self):
        user_id = self._update.effective_chat.id
        user_language = self._context.user_data.get('user_language')
        if not user_language:
            get_user_language_from_db = await self.get_language_from_database(user_id)
            if not get_user_language_from_db:
                if self._notify_user:
                    await handle_error_message(self._update, self._context, message_text="Your info was't found, please register with /start command!")
                raise UserNotFound()
            user_language = get_user_language_from_db[0][0]
            self._context.user_data['user_language'] = user_language
        return user_language

    async def find_text(self, text_key):
        return await self.language_transaction(text_key, await self.find_user_language())
    async def find_keyboard(self, text_key):
        return await self.language_transaction(text_key, await self.find_user_language(), section='keyboard')
    async def find_from_database(self, user_id, text_key, section='text'):
        result = await self.get_language_from_database(user_id)
        user_language = result[0][0]
        return await self.language_transaction(text_key, user_language, section=section)


async def report_problem_to_admin(msg):
    requests.post(url=telegram_bot_url, json={'chat_id': admin_chat_ids[0], 'text': msg})

async def handle_error_message(update, context, message_text=None):
    user_id = update.effective_chat.id
    ft_instance = FindText(update, context)
    message_text = message_text if message_text else await ft_instance.find_text('user_error_message')
    if update.callback_query:
        await update.callback_query.answer(message_text)
        return
    await context.bot.send_message(text=message_text, chat_id=user_id)


def handle_error(func):
    @functools.wraps(func)
    async def warpper(update, context, **kwargs):
        user_detail = update.effective_chat
        try:
            return await func(update, context, **kwargs)
        except Exception as e:
            if 'Message is not modified' in str(e): return await update.callback_query.answer()
            err = f"🔴 An error occurred in {func.__name__}:\n{str(e)}\nerror type: {type(e)}\nuser chat id: {user_detail.id}"
            await report_problem_to_admin(err)
            await handle_error_message(update, context)
    return warpper

def handle_conversetion_error(func):
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            await report_problem_to_admin(f'Errot in {func.__name__}\nError Type: {type(e)}\nError: {e}')
            await handle_error_message(*args)
            return ConversationHandler.END

    return wrapper