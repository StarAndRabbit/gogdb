import aiohttp
from aiohttp.client_exceptions import *
from aiohttp import hdrs, helpers
import codecs
try:
    import cchardet as chardet
except ImportError:
    import chardet
from fake_useragent import UserAgent
import logging
import json
import re
from .gogexceptions import *
import asyncio
import os
from random import randint


def random_UA():
    if not os.path.exists('fakeua.json'):
        with open('fakeua.json', 'w') as uafile:
            fakeua = UserAgent()
            json.dump(fakeua.data, uafile)
            agents = fakeua.data
    else:
        with open('fakeua.json', 'r') as uafile:
            agents = json.load(uafile)

    browser = agents['randomize'][str(randint(0, len(agents['randomize'])))]
    return agents['browsers'][browser][randint(0, len(agents['browsers'][browser]))]


fake_ua = random_UA()


class CoroutinePool:
    """ use this class to limit coroutine concurrency """
    def __init__(self, concurrency: int=16, coro_list: list=[]):
        self.__concurrency = concurrency
        self.__coro_list = coro_list

    async def run_all(self, return_exceptions=True):
        if len(self.__coro_list) <= self.__concurrency:
            return await asyncio.gather(*self.__coro_list, return_exceptions=return_exceptions)
        else:
            steps = range(0, len(self.__coro_list), self.__concurrency)
            results = list()
            for step in steps:
                tmp_result = await asyncio.gather(*self.__coro_list[step:step+self.__concurrency],
                                                  return_exceptions=return_exceptions)
                results.append(tmp_result)
            return sum(results, [])


class Response:
    def __init__(self):
        pass

    @classmethod
    async def initialize(cls, aio_response: aiohttp.ClientResponse):
        self = Response()

        self.__method = aio_response.method
        self.__cookies = aio_response.cookies
        self.__url = aio_response.url
        self.__real_url = aio_response.real_url
        self.__host = aio_response.host
        self.__headers = aio_response.headers
        self.__raw_headers = aio_response.raw_headers
        self.__request_info = aio_response.request_info
        self.__version = aio_response.version
        self.__status = aio_response.status
        self.__reason = aio_response.reason
        self.__body = await aio_response.read()

        return self

    def get_encoding(self):
        ctype = self.__headers.get(hdrs.CONTENT_TYPE, '').lower()
        mimetype = helpers.parse_mimetype(ctype)

        encoding = mimetype.parameters.get('charset')
        if encoding:
            try:
                codecs.lookup(encoding)
            except LookupError:
                encoding = None
        if not encoding:
            if mimetype.type == 'application' and mimetype.subtype == 'json':
                # RFC 7159 states that the default encoding is UTF-8.
                encoding = 'utf-8'
            else:
                encoding = chardet.detect(self.__body)['encoding']
        if not encoding:
            encoding = 'utf-8'

        return encoding

    @staticmethod
    def is_expected_content_type(response_content_type: str,
                                 expected_content_type: str):
        if expected_content_type == 'application/json':
            json_re = re.compile(r'^application/(?:[\w.+-]+?\+)?json')
            return json_re.match(response_content_type) is not None
        return expected_content_type in response_content_type

    @property
    def method(self):
        return self.__method

    @property
    def cookies(self):
        return self.__cookies

    @property
    def url(self):
        return self.__url

    @property
    def real_url(self):
        return self.__real_url

    @property
    def host(self):
        return self.__host

    @property
    def headers(self):
        return self.__headers

    @property
    def raw_headers(self):
        return self.__raw_headers

    @property
    def request_info(self):
        return self.__request_info

    @property
    def version(self):
        return self.__version

    @property
    def status(self):
        return self.__status

    @property
    def reason(self):
        return self.__reason

    @property
    def text(self):
        encoding = self.get_encoding()
        return self.__body.decode(encoding, 'strict')

    @property
    def content(self):
        return self.__body

    @property
    def json(self):
        content_type='application/json'
        ctype = self.headers.get(hdrs.CONTENT_TYPE, '').lower()
        if not Response.is_expected_content_type(ctype, content_type):
            raise ContentTypeError(
                self.__request_info,
                (),
                message=('Attempt to decode JSON with '
                         'unexpected mimetype: %s' % ctype),
                headers=self.headers)
        encoding = self.get_encoding()
        return json.loads(self.__body.decode(encoding))


class Requester:
    def __init__(self, retries: int = 5):
        self.__retries = retries

        self.__ua = fake_ua
        self.__headers = {'User-Agent': self.__ua}
        self.__logger = logging.getLogger('GOGDB.Requester')

    def __except_str(self, event, exp):
        return f'Exception occurred on {event}: {exp}'

    async def __aenter__(self):
        self.__session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, *err):
        await self.__session.close()
        self.__session = None

    async def request(self, method, url, params=None, data=None,
                      json=None, cookies=None, headers=None):
        retries = 0
        event_str = f'{method} {url} with params: {params}, data: {data}, json: {json}, cookies: {cookies}'
        self.__logger.debug(event_str)

        headers = {**self.__headers, **headers} if headers is not None else self.__headers
        while True:
            if retries != 0:
                self.__logger.debug(f'Retry Times {retries}')
            try:
                async with self.__session.request(method, url, params=params, data=data,
                                           json=json,cookies=cookies,headers=headers) as aio_resp:
                    resp =  await Response.initialize(aio_resp)
                    # raise for status after read all from aio_resp
                    # to avoid ssl error
                    aio_resp.raise_for_status()
                    return resp

            except (ClientConnectionError,
                    ClientResponseError,
                    ClientPayloadError,
                    InvalidURL) as e:
                retries += 1
                if retries <= self.__retries and \
                        (isinstance(e, ClientConnectionError) or
                         (isinstance(e, ClientResponseError) and e.status != 404)):
                    self.__logger.debug(f'Network error [ {e} ] , retry...')
                    continue
                else:
                    self.__logger.error(self.__except_str(event_str, e))
                    raise exception_wrap(e)
            except Exception as e:
                self.__logger.error(self.__except_str(event_str, e))
                raise exception_wrap(e)

    async def get(self, url, params=None, cookies=None, headers=None):
        """
        use get method to request url
        :param url: request url
        :param params: get params
        :param cookies: request cookies
        :param headers: request headers
        :return: Response object
        """
        return await self.request('GET', url, params=params, cookies=cookies, headers=headers)

    async def post(self, url, data=None, json=None, cookies=None, headers=None):
        """
        use post method to request url
        :param url: request url
        :param data: post data
        :param json: post json
        :param cookies: request cookies
        :param headers: request headers
        :return: Response object
        """
        return await self.request('POST', url, data=data, json=json, cookies=cookies, headers=headers)

    async def get_json(self, url, params=None, cookies=None, headers=None):
        """
        get json object from url
        :param url: request url
        :param params: request params
        :param cookies: request cookies
        :param headers: request headers
        :return: json object
        """
        response = await self.get(url, params=params, cookies=cookies, headers=headers)
        return response.json


def exception_wrap(exp: Exception):
    exp_map_table = {
        InvalidURL: lambda x: GOGBadRequest(),
        ClientPayloadError: lambda x: GOGBadRequest(),
        ClientConnectionError: lambda x: GOGNetworkError(),
        ClientResponseError: lambda x: GOGResponseError.judge_status(x)
    }
    if exp.__class__ not in exp_map_table:
        return GOGUnknowError(exp)
    else:
        return exp_map_table[exp.__class__](exp)


def get_id_from_url(url):
    t = re.findall(r'\d+', url)
    if t:
        pid = max(t, key=len)
        return pid
    else:
        return None


def get_country_code_from_url(url):
    t = re.findall('countryCode=.*', url)
    if t:
        country_code = max(t, key=len).strip().split('=')[1].lower()
        return country_code
    else:
        return None
