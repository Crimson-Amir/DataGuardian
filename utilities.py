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
get_boolean_emoji = {True: '🟢', False: '🔴'}

def get_range_emoji(value):
    if value in status_range_emoji:
        return status_range_emoji[value]
    for key in status_range_emoji:
        if isinstance(key, range) and value in key:
            return status_range_emoji[key]
    return None

class UserNotFound(Exception):
    def __init__(self): super().__init__("user was't register in bot!")


class FindText:
    def __init__(self, update, context, user_id=None, notify_user=True):
        self._update = update
        self._context = context
        self._notify_user = notify_user
        self._user_id = user_id

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
                    await HandleErrors().handle_error_message(self._update, self._context, message_text="Your info was't found, please register with /start command!")
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


class HandleErrors:
    err_msg = "🔴 An error occurred in {}:\n{}\nerror type: {}\nuser chat id: {}"
    def handle_functions_error(self, func):
        @functools.wraps(func)
        async def wrapper(update, context, **kwargs):
            user_detail = update.effective_chat
            try: return await func(update, context, **kwargs)
            except Exception as e:
                if 'Message is not modified' in str(e): return await update.callback_query.answer()
                err = self.err_msg.format(func.__name__, str(e), type(e), user_detail.id)
                await self.report_problem_to_admin(err)
                await self.handle_error_message(update, context)
        return wrapper

    def handle_classes_error(self, func):
        @functools.wraps(func)
        async def wrapper(self_probably, update, context, **kwargs):
            user_detail = update.effective_chat
            try:
                return await func(self_probably, update, context, **kwargs)
            except Exception as e:
                if 'Message is not modified' in str(e): return await update.callback_query.answer()
                err = self.err_msg.format(func.__name__, str(e), type(e), user_detail.id)
                await self.report_problem_to_admin(err)
                await self.handle_error_message(update, context)
        return wrapper

    def handle_queue_error(self, func):
        @functools.wraps(func)
        async def wrapper(context, **kwargs):
            try: return await func(context, **kwargs)
            except Exception as e:
                err = self.err_msg.format(func.__name__, str(e), type(e), None)
                await self.report_problem_to_admin(err)
        return wrapper

    def handle_queue_class_error(self, func):
        @functools.wraps(func)
        async def wrapper(self_pobably, context, **kwargs):
            try: return await func(self_pobably, context, **kwargs)
            except Exception as e:
                err = self.err_msg.format(func.__name__, str(e), type(e), None)
                await self.report_problem_to_admin(err)
        return wrapper

    def handle_conversetion_error(self, func):
        @functools.wraps(func)
        async def wrapper(update, context, **kwargs):
            user_detail = update.effective_chat
            try:
                return await func(update, context, **kwargs)
            except Exception as e:
                err = f"🔴 An error occurred in {func.__name__}:\n{str(e)}\nerror type: {type(e)}\nuser chat id: {user_detail.id}"
                await self.report_problem_to_admin(err)
                await self.handle_error_message(update, context)
                return ConversationHandler.END
        return wrapper

    @staticmethod
    async def report_problem_to_admin(msg):
        requests.post(url=telegram_bot_url, json={'chat_id': admin_chat_ids[0], 'text': msg})

    @staticmethod
    async def handle_error_message(update, context, message_text=None):
        user_id = update.effective_chat.id
        ft_instance = FindText(update, context)
        message_text = message_text if message_text else await ft_instance.find_text('user_error_message')
        if update.callback_query:
            await update.callback_query.answer(message_text)
            return
        await context.bot.send_message(text=message_text, chat_id=user_id)


class Singleton(type):
    _isinstance = {}
    def __call__(cls, *args, **kwargs):
        if cls not in cls._isinstance:
            cls._isinstance[cls] = super().__call__(*args, **kwargs)
        return cls._isinstance[cls]

handle_errors = HandleErrors()
handle_functions_error = handle_errors.handle_functions_error
handle_conversetion_error, handle_queue_error = handle_errors.handle_conversetion_error, handle_errors.handle_queue_error
handle_classes_errors, handle_queue_class_error = handle_errors.handle_classes_error, handle_errors.handle_queue_class_error
