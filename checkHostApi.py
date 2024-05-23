from abc import ABC, abstractmethod
import asyncio
import aiohttp

hosts = ['finland.ggkala.shop']

headers = {
    'Accept': 'application/json'
}

country = {
    'ae': 'United Arab Emirates',
    'bg': 'Bulgaria',
    'br': 'Brazil',
    'ch': 'Switzerland',
    'cz': 'Czech Republic',
    'de': 'Germany',
    'es': 'Spain',
    'fi': 'Finland',
    'fr': 'France',
    'hk': 'Hong Kong',
    'hr': 'Croatia',
    'il': 'Israel',
    'ir': 'Iran',
    'it': 'Italy',
    'jp': 'Japan',
    'kz': 'Kazakhstan',
    'lt': 'Lithuania',
    'md': 'Moldova',
    'nl': 'Netherlands',
    'pl': 'Poland',
    'pt': 'Portugal',
    'rs': 'Serbia',
    'ru': 'Russia',
    'se': 'Sweden',
    'tr': 'Turkey',
    'ua': 'Ukraine',
    'uk': 'United Kingdom',
    'us': 'United States',
}


class MakeRequests:
    def __init__(self, session):
        self._session = session
    async def get_request(self, endpoint, params=None):
        async with self._session.get(endpoint, params=params, headers=headers) as request_result:
            results = await request_result.json()
            return results


class AbstractSubFactory(ABC):
    def __init__(self, max_nodes):
        self._max_nodes = max_nodes

    @abstractmethod
    def check(self):
        pass


class CleanData:
    def clean_result(self, result):
        for key, value in result.items():
            country_domain = key.split('.')[0]
            country_number = country_domain[-1]
            country_name = country.get(country_domain[:-1])
            print(country_name)


class PingFactory(AbstractSubFactory):
    endpoint = 'https://check-host.net/check-ping'

    async def check(self):
        async with aiohttp.ClientSession() as session:
            make_requests = MakeRequests(session)
            _check_result = CheckResult()
            clean_data = CleanData()

            for parameter in hosts:
                result = await make_requests.get_request(self.endpoint, {'host': parameter, 'max_nodes': self._max_nodes})
                await asyncio.sleep(10)

                get_result = await _check_result.check_result(result)
                print(get_result)
                create_task = asyncio.create_task(clean_data.clean_result(get_result))

                await asyncio.sleep(5)
                await create_task


class CheckResult:
    check_result_endpoint = 'https://check-host.net/check-result/{}'

    async def check_result(self, check_data):
        async with aiohttp.ClientSession() as session:
            make_requests = MakeRequests(session)

            if check_data.get('error'): raise ValueError(f'an Error in check data: {check_data.get("error")}')

            request_list = await make_requests.get_request(self.check_result_endpoint.format(check_data.get('request_id')))
            return request_list


ping = PingFactory(1000)
a = asyncio.run(ping.check())
print(a)
