import os, sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utilities import posgres_manager

rankID, max_allow_ip_register, max_country_per_address = 1, 2, 2

class RegisterUser:

    async def register(self, user_detail, user_referral_code, selected_language):
        connect, backtopool, connection_pool = posgres_manager.execute('custom', None)
        try:
            with connect as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        'INSERT INTO UserDetail (first_name,last_name,username,userID,entered_with_referral_link,language) VALUES (%s,%s,%s,%s,%s,%s)',
                        (user_detail.first_name, user_detail.last_name, user_detail.username, user_detail.id, user_referral_code, selected_language))

                    cursor.execute('INSERT INTO UserRank (userID,rankID,max_allow_ip_register,max_country_per_address) VALUES (%s,%s,%s,%s)',
                                   (user_detail.id, rankID, max_allow_ip_register, max_country_per_address))
                    connection.commit()
        except Exception:
            connect.rollback()
            raise
        finally:
            backtopool.back_to_pool(connection_pool, connect)