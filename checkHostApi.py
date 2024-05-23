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

    def get_host_ip(self, iter_value, max_try=1):
        if max_try <= 10:

            try:
                return next(iter_value)[0][0][2]
            except TypeError:
                return self.get_host_ip(iter_value, max_try + 1)

        else:
            raise EOFError('The first 10 requests do not have correct results')

    async def clean_ping_data(self, result):
        final_result = {}

        iter_value = iter(result.values())
        host_ip = self.get_host_ip(iter_value)

        for key, value in result.items():
            country_domain = key.split('.')[0]
            country_number = country_domain[-1]
            country_name = country.get(country_domain[:-1])

            status_list, time_list, ok_request_count = [], [], 0
            min_time, avg_time, max_time = 0, 0, 0

            try:
                for final in value[0]:
                    status_list.append(final[0])
                    time_list.append(final[1])

                ok_request_count = len(list(filter(lambda x: x == 'OK', status_list)))
                min_time = min(time_list)
                avg_time = sum(time_list) / len(time_list)
                max_time = max(time_list)

            except TypeError:
                status_list = ['Bad Request']

            final_result[f'{country_name} {country_number}'] = {
                'host_ip': host_ip,
                'status_list': status_list,
                'ok_request_count': ok_request_count,
                'min_time': min_time,
                'avg_time': avg_time,
                'max_time': max_time,
            }

        return final_result

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
                create_task = asyncio.create_task(clean_data.clean_ping_data(get_result))

                await asyncio.sleep(2)
                await create_task


class CheckResult:
    check_result_endpoint = 'https://check-host.net/check-result/{}'

    async def check_result(self, check_data):
        async with aiohttp.ClientSession() as session:
            make_requests = MakeRequests(session)

            if check_data.get('error'): raise ValueError(f'an Error in check data: {check_data.get("error")}')

            request_list = await make_requests.get_request(self.check_result_endpoint.format(check_data.get('request_id')))
            return request_list


async def main():
    ping_factory = PingFactory(max_nodes=10)
    await ping_factory.check()


if __name__ == "__main__":
    asyncio.run(main())