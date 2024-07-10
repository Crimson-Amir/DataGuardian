from psycopg2 import errorcodes, errors
from utilities import FindText, HandleErrors, posgres_manager, get_boolean_emoji
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from language import countries_and_flags
from notification.check_address_pingsCore import PingNotification
from notification.check_addreses_ping import CheckAbstract

handle_errors = HandleErrors()
handle_function_errors, handle_classes_errors = handle_errors.handle_classes_error, handle_errors.handle_classes_error

@handle_function_errors
async def ip_guardian_setting_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ft_instance = FindText(update, context)
    text = await ft_instance.find_text('select_address')
    get_address_from_db = posgres_manager.execute('query', {'query': 'SELECT addressID,address_name,status from Address'})
    back_button = [InlineKeyboardButton(await ft_instance.find_keyboard('back_button'), callback_data='setting_menu')]
    if not get_address_from_db:
        text = await ft_instance.find_text('there_is_no_address')
        keyboard = [[InlineKeyboardButton(await ft_instance.find_keyboard('add_ip'), callback_data='add_ip')], back_button]
        return await update.callback_query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='html')
    keyboard = [[InlineKeyboardButton(f'{address[1]} {get_boolean_emoji.get(address[2])}', callback_data=f'address_setting_{address[0]}')] for address in get_address_from_db]
    keyboard.append(back_button)
    await update.callback_query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='html')


@handle_function_errors
async def address_setting(update, context, address_id=None):
    query = update.callback_query
    address_id = int(query.data.replace('address_setting_', '')) if not address_id else address_id
    get_address_from_db = posgres_manager.execute('query', {
        'query': 'SELECT address_name,status FROM Address WHERE addressID = %s', 'params': (address_id,)})
    ft_instance = FindText(update, context)
    text = await ft_instance.find_text('address_detail')
    text = text.format(get_address_from_db[0][0], get_address_from_db[0][1])
    change_address_status = 'disable_address' if get_address_from_db[0][1] else 'enable_address'
    keyboard = [
        [InlineKeyboardButton(await ft_instance.find_keyboard('country_notification_config'), callback_data=f'country_notification_config_{address_id}')],
        [InlineKeyboardButton(await ft_instance.find_keyboard(change_address_status), callback_data=f'change_address_satus_{change_address_status}_{address_id}'),
         [InlineKeyboardButton(await ft_instance.find_keyboard('check_ip_my_ip'), callback_data=f'fullcheck_ip_{address_id}')]],
        [InlineKeyboardButton(await ft_instance.find_keyboard('back_button'), callback_data='ip_guardian_menu')]
    ]
    await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='html')


class ContryNotification:
    @handle_classes_errors
    async def country_notification_config(self, update, context, address_id=None):
        user_detail = update.effective_chat
        query = update.callback_query
        address_id = int(query.data.replace('country_notification_config_', '')) if not address_id else address_id
        ft_instance = FindText(update, context)
        get_country_from_db = posgres_manager.execute(
            'query', {
                'query': """
                SELECT co.countryID, co.country_name, co.country_short_name, co.city, ac.notifID IS NOT NULL  
                FROM Country co LEFT JOIN AddressNotification_Country_Relation ac ON co.countryID = ac.countryID AND ac.status = %s 
                AND ac.notifID IN (SELECT notifID FROM AddressNotification WHERE addressID = %s)""",
                'params': (True, address_id)})

        get_user_rank_detail = posgres_manager.execute('query', {
            'query': "SELECT ra.max_country_per_address FROM Rank ra JOIN UserDetail ud ON ud.rankID = ra.rankID WHERE ud.userID = %s",'params': (user_detail.id,)})

        active_country_count = list(map(lambda x: x[4], get_country_from_db)).count(True)
        max_register_allowed = get_user_rank_detail[0][0]

        keyboard, add_to_keyboard, allow_register_country, subscribe_for_more = [], [], 'allow', ''

        if active_country_count >= max_register_allowed:
            allow_register_country = 'denied'
            subscribe_for_more = await ft_instance.find_text('subscribe_for_more_access')

        number_of_register_text = await ft_instance.find_text('register_country_count')
        text = (f"{await ft_instance.find_text('select_country')}"
                f"\n\n{number_of_register_text.format(active_country_count, max_register_allowed)}"
                f"\n{subscribe_for_more}")

        if not get_country_from_db:
            text = await ft_instance.find_text('there_is_no_country')
            keyboard = [[InlineKeyboardButton(await ft_instance.find_keyboard('back_button'), callback_data='main_menu')]]
            await update.callback_query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='html')
            return

        for country in get_country_from_db:
            country_status = '✅' if country[4] else ''
            add_to_keyboard.extend([
                InlineKeyboardButton(f'{countries_and_flags.get(country[1], '')} {country[1]} {country_status}',
                                     callback_data=f'country_ping_notification_{country[0]}__{address_id}__{country[4]}__{allow_register_country}')])
            if len(add_to_keyboard) % 2 == 0:
                keyboard.append(add_to_keyboard)
                add_to_keyboard = []

        keyboard.append(add_to_keyboard)
        keyboard.append([InlineKeyboardButton(await ft_instance.find_keyboard('back_button'), callback_data=f'address_setting_{address_id}')],)
        await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='html')

    @handle_classes_errors
    async def country_ping_notification(self, update, context):
        query = update.callback_query
        data = query.data.replace('country_ping_notification_', '').split('__')
        country_id, address_id, get_status_from_callback, allow_register_country = int(data[0]), int(data[1]), data[2], data[3]
        status = get_status_from_callback == 'True'
        ft_instance = FindText(update, context)

        if allow_register_country == 'denied' and not status:
            await query.answer(await ft_instance.find_text('access_denied_for_register_country'), show_alert=True)
            return
        try:
            posgres_manager.execute('transaction', [{'query': """
                INSERT INTO AddressNotification_Country_Relation (countryID, notifID, status) 
                VALUES (%s, (SELECT notifID FROM AddressNotification WHERE addressID = %s), %s)
                ON CONFLICT (countryID, notifID) DO UPDATE SET status = EXCLUDED.status
                """, 'params': (country_id, address_id, not status)}])

            await query.answer(await ft_instance.find_text('operation_successfull'))
            PingNotification.force_refresh = True
        except errors.lookup(errorcodes.NOT_NULL_VIOLATION):
            await query.answer(await ft_instance.find_text('somthing_wrong_in_address'), show_alert=True)
        except Exception: raise
        finally:
            return await self.country_notification_config(update, context, address_id=address_id)


class ChangeAddressStatus:
    @handle_classes_errors
    async def change_status(self, update, context):
        data = update.callback_query.data.replace('change_address_satus_', '').split('_')
        status, address_id = data[0] == 'enable', data[2]
        ft_instance = FindText(update, context)
        text = await ft_instance.find_text('operation_failed')
        try:
            posgres_manager.execute('transaction', [{
                'query': "UPDATE Address SET status = %s WHERE addressID = %s", 'params': (status, address_id)}])
            text = await ft_instance.find_text('operation_successfull')
        except Exception as e: print(e)
        finally:
            await update.callback_query.answer(text)
            return await address_setting(update, context, address_id=address_id)


class CheckIP:
    @handle_classes_errors
    async def fullcheck_ip(self, update, context):
        address_id = int(update.callback_query.data.replace('fullcheck_ip_', ''))
        user_id = update.effective_chat.id
        query = update.callback_query
        ft_instance = FindText(update, context)

        get_details = posgres_manager.execute('query', {'query': """
        SELECT ad.address,ra.max_ip_fullcheck_per_day,ad.last_fullcheck_at,ad.fullcheck_count 
        CASE 
        WHENE ad.fullcheck_count >= ra.max_ip_fullcheck_per_day 
        AND NOW() + INTERVAL '12 hours' > ad.last_fullcheck_at 
        OR ad.fullcheck_count < ra.max_ip_fullcheck_per_day 
        THEN TRUE ELSE FALSE 
        END AS address_qualified
        FROM Rank ra JOIN UserDetail ud ON ud.rankID = ra.rankID 
        JOIN Address ad ON ad.addressID = %s 
        WHERE ud.userID = %s""" ,'params': (address_id, user_id)})

        if not get_details: raise ValueError('return details from database is empty!')
        is_address_quilified, address, last_check_time, check_count = get_details[0][4], get_details[0][0], get_details[0][2], get_details[0][3]

        if not is_address_quilified:
            return await query.answer((await ft_instance.find_text('fullcheck_is_limited')).format(check_count, last_check_time))

        previous_text = query.message.text
        new_text = (await ft_instance.find_text('waiting_for_check_address')).format(CheckAbstract.run_after)
        await query.edit_message_text(previous_text + '\n\n' + new_text)

        context.job_queue.run_once(None, when=CheckAbstract.run_after, data=None)
