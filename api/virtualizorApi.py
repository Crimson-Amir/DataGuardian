import aiohttp
import asyncio


class SessionError(Exception):
    def __init__(self, message=None):
        super().__init__(message)


class MakeRequest:
    def __init__(self, session):
        self._session = session

    async def make_get_request(self, url, headers=None, params=None):

        if not self._session:
            raise SessionError("session is not set!")

        async with self._session.get(url, headers=headers, params=params, ssl=False, timeout=10) as response:
            try:
                response.raise_for_status()
                return await response.json(content_type=None)

            except aiohttp.ClientResponseError as e:
                print(f"Request failed with status {e.status}: {e.message}")
                return None


class RequestFactory:
    @staticmethod
    async def run_requests(requests_list, session_header=None, headers=None, params=None, return_exceptions=True):
        if not isinstance(requests_list, list):
            requests_list = [requests_list]

        async with aiohttp.ClientSession(headers=session_header) as session:
            request_manager = MakeRequest(session)
            requests_ = [request_manager.make_get_request(request, headers=headers, params=params) for request in requests_list]
            results = await asyncio.gather(*requests_, return_exceptions=return_exceptions)
            return results


class Virtualizor:
    def __init__(self, api_key, api_pass, ):
        self._api_key = api_key
        self._api_pass = api_pass

        self._params = {
            'act': '',
            'api': 'json',
            'apikey': self._api_key,
            'apipass': self._api_pass
        }


class ListVs(Virtualizor):
    async def execute(self, end_points_list):
        url = "{0}/index.php"
        list_of_url = [url.format(url_format) for url_format in list(end_points_list)]
        self._params['act'] = 'listvs'

        request = RequestFactory()
        make_get_request = await request.run_requests(list_of_url, params=self._params)
        return make_get_request


class VsDetail(Virtualizor):
    async def execute(self, end_points_list, vps_id):
        url = "{0}/index.php"
        list_of_url = [url.format(url_format) for url_format in list(end_points_list)]

        self._params['act'] = 'vpsmanage'
        self._params['svs'] = str(vps_id)

        request = RequestFactory()
        make_get_request = await request.run_requests(list_of_url, params=self._params)
        return make_get_request


async def run_code(class_, api_key, api_pass, **kwargs):
    instance = class_(api_key, api_pass)
    get_result = await instance.execute(**kwargs)
    return get_result



a = asyncio.run(run_code(VsDetail, 'FAQPKPC9GPUJNK84', 'DozkjalXanJStE2bcli2Q6wvjAEIT1Fa',
                         end_points_list=['https://185.215.231.72:4083'], vps_id=73))
print(a)