from psycopg2 import errorcodes, errors
from utilities import FindText, handle_error, posgres_manager, get_boolean_emoji
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from language import countries_and_flags
from notification.check_address_pingsCore import PingNotification

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
async def ip_guardian_setting_menu(update, context):
    ft_instance = FindText(update, context)
    text = await ft_instance.find_text('select_address')
    get_address_from_db = posgres_manager.execute('query', {'query': 'SELECT addressID,address_name,status from Address'})
    if not get_address_from_db:
        text = await ft_instance.find_text('there_is_no_address')
        keyboard = [[InlineKeyboardButton(await ft_instance.find_keyboard('add_ip'), callback_data='add_ip')],
                    [InlineKeyboardButton(await ft_instance.find_keyboard('back_button'), callback_data='setting_menu')]]
        await update.callback_query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='html')
        return
    keyboard = [[InlineKeyboardButton(f'{address[1]} {get_boolean_emoji.get(address[2])}', callback_data=f'address_setting_{address[0]}')] for address in get_address_from_db]
    keyboard.append([InlineKeyboardButton(await ft_instance.find_keyboard('back_button'), callback_data='setting_menu')],)
    await update.callback_query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='html')


@handle_error
async def address_setting(update, context, address_id=None):
    user_detail = update.effective_chat
    query = update.callback_query
    address_id = int(query.data.replace('address_setting_', '')) if not address_id else address_id
    ft_instance = FindText(update, context)
    get_country_from_db = posgres_manager.execute(
        'query', {
            'query': """
            SELECT co.countryID, co.country_name, co.country_short_name, co.city, ac.notifID IS NOT NULL AS is_active 
            FROM Country co LEFT JOIN AddressNotification_Country_Relation ac ON co.countryID = ac.countryID AND ac.status = %s 
            AND ac.notifID IN (SELECT notifID FROM AddressNotification WHERE addressID = %s)""",
            'params': (True, address_id)})

    get_user_rank_detail = posgres_manager.execute(
        'query', {'query': "SELECT max_country_per_address FROM UserRank WHERE userID = %s",'params': (user_detail.id,)})

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
    keyboard.append([InlineKeyboardButton(await ft_instance.find_keyboard('back_button'), callback_data='ip_guardian_setting_menu')],)
    await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='html')


@handle_error
async def country_ping_notification(update, context):
    query = update.callback_query
    data = query.data.replace('country_ping_notification_', '').split('__')
    country_id, address_id, get_status_from_callback, allow_register_country = int(data[0]), int(data[1]), data[2], data[3]
    status = get_status_from_callback == 'True'
    ft_instance = FindText(update, context)

    if allow_register_country == 'denied' and not status:
        await query.answer(await ft_instance.find_text('access_denied_for_register_country'), show_alert=True)
        return

    try:
        posgres_manager.execute(
            'transaction', [{'query': """
            INSERT INTO AddressNotification_Country_Relation (countryID, notifID, status) 
            VALUES (%s, (SELECT notifID FROM AddressNotification WHERE addressID = %s), %s)
            ON CONFLICT (countryID, notifID) DO UPDATE SET status = EXCLUDED.status
            """, 'params': (country_id, address_id, not status)}]
        )
        await query.answer(await ft_instance.find_text('operation_successfull'))
        PingNotification.force_refresh = True
    except errors.lookup(errorcodes.NOT_NULL_VIOLATION):
        await query.answer(await ft_instance.find_text('somthing_wrong_in_address'), show_alert=True)
    except Exception: raise
    finally:
        return await address_setting(update, context, address_id=address_id)


