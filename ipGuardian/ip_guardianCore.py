from psycopg2 import errorcodes, errors
from utilities import posgres_manager, status_emoji, get_range_emoji
from api.checkHostApi import CleanPingFactory
from language import countries_and_flags

calcuate_percentage_formula = lambda a, b: round((a / b) * 100, 2)

class Singleton(type):
    _instance = {}
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instance:
            cls._instance[cls] = super().__call__(*args, **kwargs)
        return cls._instance[cls]

class RegisterIP(metaclass=Singleton):
    message_for_update, ip_block_list = {}, []

    async def register_to_database(self, user_id, address, score_percent):
        connect, backtopool, connection_pool = posgres_manager.execute('custom', None)
        try:
            with connect as connection:
                with connection.cursor() as cursor:
                    cursor.execute('INSERT INTO Address (userID,address,address_name,last_score_percent) VALUES (%s,%s,%s,%s) RETURNING addressID', (int(user_id), address, address, score_percent))
                    address_id = cursor.fetchone()
                    cursor.execute('INSERT INTO AddressNotification (userID,addressID) VALUES (%s,%s)', (user_id,address_id[0]))
                    connection.commit()
        except Exception:
            connect.rollback()
            raise
        finally:
            backtopool.back_to_pool(connection_pool, connect)

        self.ip_block_list.append(address)

    async def register_ip(self, user_id, address):
        result, message_id = self.message_for_update.pop(user_id)
        message_id = int(message_id)
        get_address_detail = await self.format_ping_checker_text(result)
        try:
            if not get_address_detail: return {'status': 0, 'error': 'user_error_message', 'message_id': message_id}
            score_present, address_detail_text = get_address_detail[2], get_address_detail[1]
            if score_present < 50:
                self.ip_block_list.append(address)
                return {'status': 0, 'error': 'address_score_not_enough', 'address_detail_text': address_detail_text, 'message_id': message_id}

            await self.register_to_database(user_id, address, score_present)
            return {'status': 1, 'msg': 'address_register_successfull', 'address_detail_text': address_detail_text, 'message_id': message_id}

        except errors.lookup(errorcodes.UNIQUE_VIOLATION):
            self.ip_block_list.append(address)
            return {'status': 0, 'error': 'address_is_not_unique', 'message_id': message_id}
        except Exception as e:
            print(e)
            return {'status': 0, 'error': 'user_error_message', 'error_detail': e, 'message_id': message_id}


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
