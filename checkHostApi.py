from abc import ABC, abstractmethod
import asyncio
import aiohttp
from utilities import country, headers, hosts


class MakeRequests:
    def __init__(self, session):
        self._session = session
    async def get_request(self, endpoint, params=None):
        async with self._session.get(endpoint, params=params, headers=headers) as request_result:
            results = await request_result.json()
            return results


class CleanData(ABC):
    @abstractmethod
    def __init__(self):
        self._func = None
        self._ip_index = None

    def get_host_ip(self, iter_value, ip_index, max_try=10) -> str:

        for _ in range(max_try):
            try:

                if self.__class__.__name__ == 'CleanPingFactory':
                    return next(iter_value)[0][0][ip_index]

                return next(iter_value)[0][ip_index]


            except (TypeError, StopIteration, IndexError):
                continue
        else:
            return 'no ip found'

    async def clean_data(self, result):

        final_result = {}

        iter_value = iter(result.values())
        host_ip = self.get_host_ip(iter_value, ip_index=self._ip_index)

        for key, value in result.items():
            country_domain = key.split('.')[0]
            country_number = country_domain[-1]
            country_name = country.get(country_domain[:-1])

            try:
                clean_data_dict = await self._func(value)
                clean_data_dict['host'] = host_ip
            except Exception as e:
                clean_data_dict = {'error': e}

            final_result[f'{country_name} {country_number}'] = clean_data_dict

        print(final_result)
        return final_result


class CleanDataCore:
    @staticmethod
    async def clean_ping_data_core(value):
        status_list, time_list, ok_request_count, min_time, avg_time, max_time = [], [], 0, 0, 0, 0

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

        return {
            'status_list': status_list,
            'ok_request_count': ok_request_count,
            'min_time': min_time,
            'avg_time': avg_time,
            'max_time': max_time,
        }


    @staticmethod
    async def clean_http_data_core(value):
        status, time, binary = '', 0, 0

        try:
            status = value[0][2]
            time = value[0][1]
            binary = value[0][0]

        except TypeError:
            status = ['Bad Request']

        return {
            'status': status,
            'time': time,
            'binary': binary,
        }


class CleanPingFactory(CleanData):
    def __init__(self):
        self._func = CleanDataCore().clean_ping_data_core
        self._ip_index = 2


class CleanHttpFactory(CleanData):
    def __init__(self):
        self._func = CleanDataCore().clean_http_data_core
        self._ip_index = 4


class AbstractSubFactory(ABC):
    api_endpoint = 'https://check-host.net/check-'

    @abstractmethod
    def __init__(self, max_nodes):
        self._max_nodes = max_nodes
        self.endpoint = None
        self.clean_data = None


    async def check(self, _hosts):
        endpoint = self.api_endpoint + self.endpoint

        async with aiohttp.ClientSession() as session:
            make_requests = MakeRequests(session)
            _check_result = CheckResult()

            for parameter in _hosts:
                result = await make_requests.get_request(endpoint, {'host': parameter, 'max_nodes': self._max_nodes})
                await asyncio.sleep(10)

                get_result = await _check_result.check_result(result)
                create_task = asyncio.create_task(self.clean_data(get_result))

                await asyncio.sleep(2)
                await create_task


class PingFactory(AbstractSubFactory):
    def __init__(self, max_nodes):
        super().__init__(max_nodes)
        clean_data = CleanPingFactory()
        self.endpoint = 'ping'
        self.clean_data = clean_data.clean_data


class HttpFactory(AbstractSubFactory):
    def __init__(self, max_nodes):
        super().__init__(max_nodes)
        clean_data = CleanHttpFactory()
        self.endpoint = 'http'
        self.clean_data = clean_data.clean_data


class CheckResult:
    check_result_endpoint = 'https://check-host.net/check-result/{}'

    async def check_result(self, check_data):

        if check_data.get('error'):
            raise ValueError(f'Error in check data: {check_data.get("error")}')

        request_id = check_data.get('request_id')
        if not request_id:
            raise ValueError('No request id in check data')

        async with aiohttp.ClientSession() as session:
            make_requests = MakeRequests(session)

            request_list = await make_requests.get_request(self.check_result_endpoint.format(request_id))
            return request_list


async def main():
    ping_factory = HttpFactory(max_nodes=10)
    await ping_factory.check(hosts)


if __name__ == "__main__":
    asyncio.run(main())