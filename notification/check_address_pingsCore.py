from api.checkHostApi import client, PingFactory
from utilities import posgres_manager, Singleton
# from asyncio import run
from ipGuardian.ip_guardianCore import RegisterIP

class ProtoType(metaclass=Singleton):
    def __init__(self): self.copy_objects = {}
    async def register(self, name, value): self.copy_objects.update({name: value})
    async def unregister(self, name): del self.copy_objects[name]

class PingNotification:
    force_refresh = False

    async def get_eligible_notification(self, period_min, refresh=False):
        get_instance = ProtoType()

        if period_min not in get_instance.copy_objects or refresh or self.force_refresh:
            fetch_from_db = posgres_manager.execute(
                'query', {
                    'query': """
                    SELECT subquery.address,subquery.userID,subquery.expected_ping_number_for_notification,LOWER(co.country_short_name) FROM Country co JOIN (
                        SELECT ac.countryID, ad.address, ad.userID, an.expected_ping_number_for_notification 
                        FROM AddressNotification_Country_Relation ac
                        JOIN AddressNotification an ON an.notifID = ac.notifID 
                        JOIN Address ad ON ad.addressID = an.addressID 
                        WHERE an.wait_for_check = %s AND ad.status = %s AND ac.status = %s 
                        AND an.period_check_in_min = %s AND NOW() >= an.run_after 
                    ) subquery ON co.countryID = subquery.countryID""", 'params': (True, True, True, period_min)})

            result_dict = {}
            for index, (domain, user_id, expect_ping_number, country) in enumerate(fetch_from_db):
                if domain not in result_dict:
                    result_dict[domain] = []
                    result_dict[domain].append(user_id)
                    result_dict[domain].append(expect_ping_number)

                result_dict[domain].append(country)
            await get_instance.register(period_min, result_dict)
            PingNotification.force_refresh = False
            return result_dict

        # print('get_instance.copy_objects.get(period_min)', get_instance.copy_objects.get(period_min))
        return get_instance.copy_objects.get(period_min)

    @staticmethod
    async def get_check_request_id(address, nodes: list):
        prepare_nodes = [f'{node}{i}.node.check-host.net' for i in range(1, 10) for node in nodes]
        result = await client(
            check=PingFactory,
            _host=address,
            # max_nodes=55,
            node=prepare_nodes,
            return_request_id = True)
        return result

    @staticmethod
    async def return_final_result(result):
        register_id = RegisterIP()
        get_address_detail = await register_id.format_ping_checker_text(result)
        return get_address_detail

# a = run(PingNotification().get_eligible_notification(10))