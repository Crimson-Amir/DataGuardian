from abc import ABC, abstractmethod
import asyncio
import aiohttp
import sys, os
# sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from api.checkHostApi_utilities import country, headers
from urllib import parse


class MakeRequests:
    def __init__(self, session):
        self._session = session
    async def get_request(self, endpoint, params=None):
        url = f'{endpoint}?{parse.urlencode(params, doseq=True)}' if params else endpoint
        async with self._session.get(url, headers=headers) as request_result:
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
        _check_result = CheckResult()
        country_detail = result.get('nodes', {})
        get_result = await _check_result.check_result(check_data=result)
        final_result = {}
        iter_value = iter(get_result.values())
        host_ip = self.get_host_ip(iter_value, ip_index=self._ip_index)
        general_score = 0
        for key, value in get_result.items():
            country_info = country_detail.get(key)
            country_name, city = country_info[1], country_info[2]
            # country_ip, country_id = country_info[3], country_info[4]
            try:
                clean_data_dict = await self._func(value)
                general_score += clean_data_dict.get('ok_request_count', 0)
                clean_data_dict['host'] = host_ip
            except Exception as e:
                clean_data_dict = {'error': e}
            final_result[f'{country_name}, {city}'] = clean_data_dict
        final_result['general_score'] = general_score
        final_result['number_of_country'] = len(final_result)
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
    def __init__(self):
        self.endpoint = None
        self.clean_data = None
    async def check(self, _host, **kwargs):
        """
        :param _host: ip or address ypu want to check
        :param kwargs:
        max_nodes: get random country check with limit you enter here
        node: list of country you want like: ['us1.node.check-host.net', 'ch1.node.check-host.net']
        """
        endpoint = self.api_endpoint + self.endpoint
        async with aiohttp.ClientSession() as session:
            make_requests = MakeRequests(session)
            result = await make_requests.get_request(endpoint, params={'host': _host, **kwargs})
            if kwargs.get('return_request_id'): return result
            # first_dict_value = next(iter(kwargs.values()))
            # sleep_secon = len(first_dict_value) if isinstance(first_dict_value, list) else first_dict_value
            await asyncio.sleep(10)
            create_task = asyncio.create_task(self.clean_data(result))
            return await create_task

class PingFactory(AbstractSubFactory):
    def __init__(self):
        clean_data = CleanPingFactory()
        self.endpoint = 'ping'
        self.clean_data = clean_data.clean_data

class HttpFactory(AbstractSubFactory):
    def __init__(self):
        clean_data = CleanHttpFactory()
        self.endpoint = 'http'
        self.clean_data = clean_data.clean_data

class CheckResult:
    check_result_endpoint = 'https://check-host.net/check-result/{}'
    async def check_result(self, check_data):
        if check_data.get('error'): raise ValueError(f'Error in check data: {check_data.get("error")}')
        request_id = check_data.get('request_id')
        if not request_id: raise ValueError('No request id in check data')
        async with aiohttp.ClientSession() as session:
            make_requests = MakeRequests(session)
            request_list = await make_requests.get_request(self.check_result_endpoint.format(request_id))
            return request_list

async def client(check, **kwargs):
    ping_factory = check()
    return await ping_factory.check(**kwargs)

if __name__ == "__main__":
    a = asyncio.run(
        client(
            check=PingFactory,
            _host='finland.ggkala.shop',
            # node=[f'ir{3}.node.check-host.net'],
            max_nodes=80,
            # return_request_id = True
        )
    )
    print(a)
    # clean = CleanPingFactory()
    # print(asyncio.run(clean.clean_data(request_id='1aea8626k862')))

