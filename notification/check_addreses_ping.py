import copy
from notification.check_address_pingsCore import PingNotification
from queue import PriorityQueue
from abc import ABC, abstractmethod
from ipGuardian.ip_guardianCore import RegisterIP
from utilities import posgres_manager, FindText
from datetime import datetime, timedelta


class Notification:
    country_block_count = []
    location_deleted = []

    async def disable_country(self, country_and_result, domain):
        country_name = country_and_result[0].split(',')[0]
        posgres_manager.execute('transaction', [{
            'query': """
            UPDATE AddressNotification_Country_Relation SET status = %s WHERE
            countryID = (SELECT countryID FROM Country WHERE country_name = %s)
            AND notifID = (SELECT an.notifID FROM AddressNotification an JOIN Address ad ON ad.address = %s)
            """,
            'params': (False, country_name, domain)}])
        PingNotification.force_refresh = True
        self.location_deleted.append(country_name)

    async def handle_notification(self, context):
        data = context.job.data
        result = data.get('get_result')
        user_id = data.get('user_id')
        domain = data.get('domain')
        expect_ping_number = data.get('expect_ping_number')
        ft_instance = FindText(1, context)
        get_result = RegisterIP()
        final = await get_result.format_ping_checker_text(result)
        some_ids_has_problem = False

        for country_and_result in final[0].items():
            if not isinstance(country_and_result[1], dict): continue
            if country_and_result[1].get('ok_request_count', 0) <= expect_ping_number:
                if Notification.country_block_count.count(country_and_result[0]) >= 2:
                    await self.disable_country(country_and_result, domain)
                else: Notification.country_block_count.append(country_and_result[0])
                some_ids_has_problem = True

        if some_ids_has_problem:
            text = await ft_instance.find_from_database(user_id, 'ping_notification_text')
            text.format(domain)
            text += '\n\n' + final[1]
            if self.location_deleted:
                text += '\n\n' + await ft_instance.find_from_database(user_id, 'some_id_deleted')
                text += '\n' + '\n'.join(self.location_deleted)
            await context.bot.send_message(user_id, text=text)


class CheckAbstract(ABC):
    core_instance = PingNotification()
    queue_instance = PriorityQueue(maxsize=50)
    count_of_check_address_in_last_24_hourse = []
    is_queue_running = False
    run_after = 30

    @abstractmethod
    async def execute(self, context): pass

    async def run_queue(self, context):
        while not self.queue_instance.empty():
            queue_fetch = self.queue_instance.get()
            priority, fetch = queue_fetch
            for detail in fetch.items():
                context.job_queue.run_once(self.get_request_id, when=CheckAbstract.run_after, data=detail)
                CheckAbstract.run_after += 30

        CheckAbstract.is_queue_running = False

    async def get_request_id(self, context):
        main_data = context.job.data
        data = copy.deepcopy(main_data)
        user_id = data[1].pop(0)
        expect_ping_number = data[1].pop(0)
        domain = data[0]
        await self.check_notif_count(domain)
        get_result = await self.core_instance.get_check_request_id(data[0], data[1])
        context.job_queue.run_once(Notification().handle_notification, when=12, data={
            'get_result': get_result, 'user_id': user_id, 'domain': domain, 'expect_ping_number': expect_ping_number})

        left_queue = [job for job in context.job_queue.jobs() if job.callback == self.get_request_id]
        if len(left_queue) == 0: CheckAbstract.run_after = 30

    @staticmethod
    async def check_notif_count(domain):
        address_count = CheckAbstract.count_of_check_address_in_last_24_hourse.count(domain)
        hour_per_count = {2: 1, 3: 12}
        hours_later = datetime.now() + timedelta(hours=hour_per_count.get(address_count, 12))
        if address_count >= 1:
            posgres_manager.execute('transaction', [{
                'query': 'UPDATE AddressNotification SET run_after = %s WHERE addressID = (SELECT addressID FROM Address WHERE address = %s)',
                'params': (hours_later, domain)}])


class Check10(CheckAbstract):
    async def execute(self, context):
        fetch = await self.core_instance.get_eligible_notification(10)

        self.queue_instance.put((10, fetch))
        if not CheckAbstract.is_queue_running:
            CheckAbstract.is_queue_running = True
            await self.run_queue(context)

class Check20(CheckAbstract):
    async def execute(self, context):
        fetch = await self.core_instance.get_eligible_notification(20)
        self.queue_instance.put((20, fetch))
        if not CheckAbstract.is_queue_running:
            CheckAbstract.is_queue_running = True
            await self.run_queue(context)

class Check30(CheckAbstract):
    async def execute(self, context):
        fetch = await self.core_instance.get_eligible_notification(30)
        self.queue_instance.put((30, fetch))
        if not CheckAbstract.is_queue_running:
            CheckAbstract.is_queue_running = True
            await self.run_queue(context)
