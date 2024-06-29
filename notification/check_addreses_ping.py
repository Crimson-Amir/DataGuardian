import copy

from notification.check_address_pingsCore import PingNotification
from queue import PriorityQueue
from abc import ABC, abstractmethod


class Notification:
    async def handle_notification(self, context):
        data = context.job.data
        result = data.get('get_result')
        user_id = data.get('user_id')
        print(result, user_id)


class CheckAbstract(ABC):
    core_instance = PingNotification()
    queue_instance = PriorityQueue(maxsize=50)
    is_queue_running = False
    run_after = 10

    @abstractmethod
    async def execute(self, context): pass

    async def run_queue(self, context):
        while not self.queue_instance.empty():
            ggeet = self.queue_instance.get()
            priority, fetch = ggeet
            for detail in fetch.items():
                context.job_queue.run_once(self.get_request_id, when=self.run_after, data=detail)
                self.run_after += 27
        CheckAbstract.is_queue_running = False

    async def get_request_id(self, context):
        main_data = context.job.data
        data = copy.deepcopy(main_data)
        user_id = data[1].pop(0)
        get_result = await self.core_instance.get_check_request_id(data[0], data[1])
        context.job_queue.run_once(Notification().handle_notification, when=10, data={'get_result': get_result, 'user_id': user_id})


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
