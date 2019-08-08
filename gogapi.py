#!/usr/bin/env python
# encoding: utf-8

import aiohttp
from aiohttp.client_exceptions import *
import asyncio
from fake_useragent import UserAgent
import logging
import html5lib
import json
import re
from datetime import datetime
from decimal import Decimal
import inspect
from .gogexceptions import *


class APIRequester:

    def __init__(self, retries=5, concurrency=10, headers=None):
        self.__retries = retries
        self.__concurrency = concurrency
        self.__ua = UserAgent().random
        self.__headers = {'User-Agent': self.__ua}
        if headers is not None:
            self.__headers.update(headers)
        self.__logger = logging.getLogger('GOGDB.Requester')

    @staticmethod
    def except_str(event, exp):
        return f'Exception occurred on {event}: {exp}'

    async def __aenter__(self):
        self.__session = aiohttp.ClientSession(headers=self.__headers)
        return self

    async def __aexit__(self, *err):
        await self.__session.close()
        self.__session = None

    async def post(self, url, params=None, cookies=None):
        retries = 0
        event_str = f'post {url} with params {params} and cookies {cookies}'
        self.__logger.debug(event_str)
        while True:
            if retries != 0:
                self.__logger.debug(f'Retry Times {retries}')
            try:
                async with self.__session.post(url, data=params, cookies=cookies) as resp:
                    try:
                        resp.raise_for_status()
                    except Exception as e:
                        retries += 1
                        if retries <= self.__retries:
                            continue
                        else:
                            self.__logger.error(APIRequester.except_str(event_str, e))
                            return e
                    try:
                        return {
                            'headers': resp.headers,
                            'cookies': resp.cookies,
                            'text': await resp.text(),
                            'history': resp.history,
                            'url': resp.url
                        }
                    except Exception as e:
                        self.__logger.error(APIRequester.except_str(event_str, e))
                        return e

            except ClientConnectionError as e:
                retries += 1
                if retries <= self.__retries:
                    self.__logger.debug('Network error, retry...')
                    continue
                else:
                    self.__logger.error(APIRequester.except_str(event_str, e))
                    return e

    async def get(self, url, params=None, cookies=None):
        retries = 0
        event_str = f'get {url} with params {params}'
        self.__logger.debug(event_str)
        while True:
            if retries != 0:
                self.__logger.debug(f'Retry Times {retries}')
            try:
                async with self.__session.get(url, params=params, cookies=cookies) as resp:
                    try:
                        resp.raise_for_status()
                    except Exception as e:
                        retries += 1
                        if retries <= self.__retries:
                            continue
                        else:
                            self.__logger.error(APIRequester.except_str(event_str, e))
                            return e
                    try:
                        return {
                            'headers': resp.headers,
                            'cookies': resp.cookies,
                            'text': await resp.text(),
                            'history': resp.history,
                            'url': resp.url
                        }
                    except UnicodeDecodeError:
                        return {
                            'headers': resp.headers,
                            'cookies': resp.cookies,
                            'text': await resp.read(),
                            'history': resp.history,
                            'url': resp.url
                        }
                    except Exception as e:
                        self.__logger.error(APIRequester.except_str(event_str, e))
                        return e
            except ClientConnectionError as e:
                retries += 1
                if retries <= self.__retries:
                    self.__logger.debug('Network error, retry...')
                    continue
                else:
                    self.__logger.error(APIRequester.except_str(event_str, e))
                    return e

    async def get_json(self, url, params=None):
        if isinstance(url, str) and (isinstance(params, dict) or params is None):
            return await self.__get_json(url, params)
        elif isinstance(url, list) and (isinstance(params, dict) or params is None):
            return await self.__get_json_multi_urls(url, params)
        elif isinstance(url, str) and isinstance(params, list):
            return await self.__get_json_multi_params(url, params)

    async def __get_json(self, url, params):
        retries = 0
        event_str = f'get json from {url} with params {params}'
        self.__logger.debug(event_str)
        while True:
            if retries != 0:
                self.__logger.debug(f'Retry Times {retries}')
            try:
                async with self.__session.get(url, params=params) as resp:
                    try:
                        resp.raise_for_status()
                    except Exception as e:
                        retries += 1
                        if retries <= self.__retries:
                            continue
                        else:
                            self.__logger.error(APIRequester.except_str(event_str, e))
                            return e
                    try:
                        return await resp.json()
                    except Exception as e:
                        self.__logger.error(APIRequester.except_str(event_str, e))
                        return e
            except ClientConnectionError as e:
                retries += 1
                if retries <= self.__retries:
                    self.__logger.debug('Network error, retry...')
                    continue
                else:
                    self.__logger.error(APIRequester.except_str(event_str, e))
                    return e

    async def __get_json_multi_urls(self, urls, params):
        if len(urls) <= self.__concurrency:
            return await asyncio.gather(*[self.__get_json(url, params) for url in urls], return_exceptions=True)
        else:
            result = list()
            url_start = 0
            url_end = self.__concurrency
            while True:
                result.extend(await asyncio.gather(*[self.__get_json(url, params) for url in urls[url_start:url_end]],
                                                   return_exceptions=True))
                if url_end > len(urls):
                    return result
                else:
                    url_start = url_end
                    url_end += self.__concurrency

    async def __get_json_multi_params(self, url, params):
        if len(params) <= self.__concurrency:
            return await asyncio.gather(*[self.__get_json(url, param) for param in params], return_exceptions=True)
        else:
            result = list()
            para_start = 0
            para_end = self.__concurrency
            while True:
                result.extend(
                    await asyncio.gather(*[self.__get_json(url, param) for param in params[para_start:para_end]],
                                         return_exceptions=True))
                if para_end > len(params):
                    return result
                else:
                    para_start = para_end
                    para_end += self.__concurrency


class APIUtility:

    def __init__(self):
        self.__logger = logging.getLogger('GOGDB.Utility')

    @staticmethod
    def raise_or_return_exception(is_raise, exception):
        if is_raise:
            raise exception
        else:
            return exception

    @staticmethod
    def error_handler(data, product_id=None, is_raise=False):

        if isinstance(data, Exception):
            if isinstance(data, InvalidURL) or isinstance(data, ClientPayloadError):
                return APIUtility.raise_or_return_exception(is_raise, GOGBadRequest())
            elif isinstance(data, ClientConnectionError):
                return APIUtility.raise_or_return_exception(is_raise, GOGNetworkError())
            elif isinstance(data, ClientResponseError):
                if data.status == 404 and product_id is not None:
                    return APIUtility.raise_or_return_exception(is_raise, GOGProductNotFound(product_id))
                else:
                    return APIUtility.raise_or_return_exception(is_raise, GOGNetworkError())
            else:
                return APIUtility.raise_or_return_exception(is_raise, GOGUnknowError(data))
        else:
            return data

    def price_parse(self, price_string):
        """
        format price string into dict
        :param price_string: price string format like "999 USD"
        :return: Decimal object
        """
        self.__logger.debug(f'parse price from {price_string}')
        price_tmp = price_string.strip().split(' ')
        price_tmp[0] = price_tmp[0][:len(price_tmp[0])-2] + '.' + price_tmp[0][len(price_tmp[0])-2:]
        return Decimal(price_tmp[0]).quantize(Decimal('.00'))

    def get_id_from_url(self, url):
        t = re.findall(r'\d+', url)
        if t:
            pid = max(t, key=len)
            self.__logger.debug(f'Get product id {pid} from {url}')
            return pid
        else:
            self.__logger.warning(f'Can not get product id from {url}')
            return None

    def get_country_code_from_url(self, url):
        t = re.findall('countryCode=.*', url)
        if t:
            country_code = max(t, key=len).strip().split('=')[1].lower()
            self.__logger.debug(f'Get country code {country_code} from {url}')
            return country_code
        else:
            self.__logger.warning(f'Can not get country code from {url}')
            return None

    @staticmethod
    def func_name():
        call_stack = inspect.stack()
        if len(call_stack) < 3:
            return ''
        else:
            return call_stack[1].function


class API:

    def __init__(self, retries=5, concurrency=10):
        self.__hosts = dict()
        self.__hosts['detail'] = 'https://api.gog.com/v2/games'
        self.__hosts['price'] = 'https://api.gog.com/products/{productid}/prices'
        self.__hosts['multiprice'] = 'https://api.gog.com/products/prices'
        self.__hosts['region'] = 'https://countrycode.org/api/countryCode/countryMenu'
        self.__hosts['rating'] = 'https://reviews.gog.com/v1/products/{productid}/averageRating?reviewer=verified_owner'
        self.__hosts['auth'] = 'https://auth.gog.com/auth'
        self.__hosts['login'] = 'https://login.gog.com/login_check'
        self.__hosts['token'] = 'https://auth.gog.com/token'
        self.__hosts['extend_detail'] = 'https://api.gog.com/products'
        self.__hosts['achievement'] = 'https://gameplay.gog.com/clients/{clientid}/users/{userid}/achievements'

        self.__client_id = '46899977096215655'
        self.__client_secret = '9d85c43b1482497dbbce61f6e4aa173a433796eeae2ca8c5f6129f2dc4de46d9'
        self.__redirect_uri = 'https://embed.gog.com/on_login_success?origin=client'

        self.__auth = dict()
        self.__auth['auth'] = {
            'client_id': self.__client_id,
            'redirect_uri': self.__redirect_uri,
            'response_type': 'code',
            'layout': 'default'
        }
        self.__auth['login'] = {
            'login[username]': '',
            'login[password]': '',
            'login[login_flow]': 'default',
            'login[_token]': ''
        }
        self.__auth['token'] = {
            'client_id': self.__client_id,
            'client_secret': self.__client_secret,
            'grant_type': 'authorization_code',
            'code': '',
            'redirect_uri': self.__redirect_uri
        }
        self.__auth['refresh'] = {
            'client_id': self.__client_id,
            'client_secret': self.__client_secret,
            'grant_type': 'refresh_token',
            'refresh_token': ''
        }

        self.__retries = retries
        self.__concurrency = concurrency
        self.__logger = logging.getLogger('GOGDB.GOGAPI')

        self.__utl = APIUtility()

    @property
    def retries(self):
        return self.__retries

    @retries.setter
    def retries(self, value):
        self.__retries = value

    @property
    def concurrency(self):
        return self.__concurrency

    @concurrency.setter
    def concurrency(self, value):
        self.__concurrency = value

    @property
    def logger(self):
        return self.__logger

    @property
    def hosts(self):
        return self.__hosts

    async def get_total_num(self):
        self.__logger.debug(f"Call {APIUtility.func_name()}")
        async with APIRequester(self.__retries, self.__concurrency) as request:
            fst_page = await request.get_json(self.__hosts['detail'])

            APIUtility.error_handler(fst_page, is_raise=True)
            try:
                limit = fst_page['limit']
                pages = fst_page['pages']
                lst_page_url = fst_page['_links']['last']['href']
            except Exception as e:
                self.__logger.error(f"{APIUtility.func_name()} {type(e).__name__} {e}")
                raise

            lst_page = await request.get_json(lst_page_url)
            APIUtility.error_handler(lst_page, is_raise=True)
            try:
                lst_num = len(lst_page['_embedded']['items'])
            except Exception as e:
                self.__logger.error(f"[{APIUtility.func_name()}] {type(e).__name__} {e}")
                raise

            return limit * (pages - 1) + lst_num

    async def get_product_id_in_page(self, page, limit=50):
        self.__logger.debug(f"Call {APIUtility.func_name()}")
        params = {'page': page, 'limit': limit, 'locale': 'en-US'}
        async with APIRequester(self.__retries, self.__concurrency) as request:
            page_data = await request.get_json(self.hosts['detail'], params=params)
            page_data = APIUtility.error_handler(page_data)
            if isinstance(page_data, GOGBaseException):
                raise type(page_data)
            try:
                items = page_data['_embedded']['items']
            except Exception as e:
                self.__logger.error(f"[{APIUtility.func_name()}] {type(e).__name__} {e}")
                raise

            result = list()
            for item in items:
                try:
                    result.append(item['_embedded']['product']['id'])
                except Exception as e:
                    self.__logger.error(f"{APIUtility.func_name()} {type(e).__name__} {e}")
                    result.append(-1)           # Error Flag
            return result

    async def get_all_product_id(self):
        self.__logger.debug(f"Call {APIUtility.func_name()}")
        async with APIRequester(self.__retries, self.__concurrency) as request:
            pages_data = await request.get_json(self.__hosts['detail'])
            APIUtility.error_handler(pages_data, is_raise=True)
            try:
                pages = pages_data['pages']
            except Exception as e:
                self.__logger.error(f"{APIUtility.func_name()} {type(e).__name__} {e}")
                raise

            params = [{'page': page, 'locale': 'en-US'} for page in range(1, pages+1)]
            results = await request.get_json(self.__hosts['detail'], params)

            sum_ids = list()
            for result in results:
                APIUtility.error_handler(result, is_raise=True)
                try:
                    items = result['_embedded']['items']
                except Exception as e:
                    self.__logger.error(f"{APIUtility.func_name()} {type(e).__name__} {e}")
                    raise

                prod_ids = list()
                for item in items:
                    try:
                        prod_ids.append(item['_embedded']['product']['id'])
                    except Exception as e:
                        self.__logger.error(f"{APIUtility.func_name()} {type(e).__name__} {e}")
                        raise
                sum_ids.extend(prod_ids)

            return sum_ids

    async def get_product_data(self, product_id):
        params = {'locale': 'en-US'}

        if isinstance(product_id, int) or isinstance(product_id, str):
            prod_ids = [str(product_id)]
        elif isinstance(product_id, list) or isinstance(product_id, tuple):
            prod_ids = list(map(str, product_id))
        else:
            raise TypeError(f'{APIUtility.func_name()} Args Type Error')

        self.__logger.debug(
            f"Call {APIUtility.func_name()} ids=[{', '.join(str(prod_id) for prod_id in prod_ids)}]")

        urls = [f"{self.__hosts['detail']}/{prod_id}" for prod_id in prod_ids]

        async with APIRequester(self.__retries, self.__concurrency) as request:
            product_datas = await request.get_json(urls, params)
            for i in range(0, len(prod_ids)):
                product_datas[i] = APIUtility.error_handler(product_datas[i], prod_ids[i])

            return product_datas

    async def get_product_achievement(self, client_id, user_id, token_type, access_token):
        self.__logger.debug(f"Call {APIUtility.func_name()}")
        url = self.__hosts['achievement'].replace('{clientid}', client_id).replace('{userid}', user_id)
        headers = {'Authorization': f'{token_type.title()} {access_token}'}
        async with APIRequester(self.__retries, self.__concurrency, headers) as request:
            result = await request.get_json(url)
            APIUtility.error_handler(result, is_raise=True)
            return result

    async def get_countries(self):
        self.__logger.debug(f"Call {APIUtility.func_name()}")
        async with APIRequester(self.__retries, self.__concurrency) as request:
            result = await request.get_json(self.__hosts['region'])
            APIUtility.error_handler(result, is_raise=True)
            return result

    async def get_product_prices(self, product_id, countries):
        """
        get product's price in different countries
        :param product_id: product id, can be int, string or list
        :param countries: countries, can be string or list
        :return: result format like this
                    {
                        '<product id>': {
                            'basePrice': {
                                '<country code>': {
                                    'defaultCurrency': <currency>,
                                    '<currency>': <price>(decimal object)
                                }
                            }
                            'finalPrice': {
                                '<country code>': {
                                    'defaultCurrency': <currency>,
                                    '<currency>': <price>(decimal object)
                                }
                            }
                        }
                    }
        """
        id_list = list(map(str, product_id)) if isinstance(product_id, list) else [str(product_id)]
        prod_ids = ','.join(id_list)
        if not isinstance(countries, list):
            params = [{'ids': prod_ids, 'countryCode': str(countries)}]
        else:
            params = [{'ids': prod_ids, 'countryCode': str(countryCode)} for countryCode in countries]

        countries_str = ','.join(countries) if isinstance(countries, list) else countries
        self.__logger.debug(f"Call {APIUtility.func_name()} ids=[{prod_ids}] countries=[{countries_str}]")

        async with APIRequester(self.__retries, self.__concurrency) as request:
            rep = await request.get_json(self.__hosts['multiprice'], params)
            result_list = {prodid: {'basePrice': dict(), 'finalPrice': dict()} for prodid in id_list}
            for data in rep:
                try:
                    APIUtility.error_handler(data, is_raise=True)
                except Exception as e:
                    self.__logger.warning(f"{APIUtility.func_name()} error occurred: {str(e)}")
                    continue
                for item in data['_embedded']['items']:
                    prod_id = self.__utl.get_id_from_url(item['_links']['self']['href'])
                    country_code = self.__utl.get_country_code_from_url(item['_links']['self']['href'])
                    result_list[prod_id]['basePrice'][country_code] = dict()
                    result_list[prod_id]['finalPrice'][country_code] = dict()

                    result_list[prod_id]['basePrice'][country_code]['defaultCurrency'] = \
                        item['_embedded']['prices'][0]['currency']['code']
                    result_list[prod_id]['finalPrice'][country_code]['defaultCurrency'] = \
                        item['_embedded']['prices'][0]['currency']['code']

                    for price in item['_embedded']['prices']:
                        base_price = self.__utl.price_parse(price['basePrice'])
                        final_price = self.__utl.price_parse(price['finalPrice'])
                        result_list[prod_id]['basePrice'][country_code][price['currency']['code']] = base_price
                        result_list[prod_id]['finalPrice'][country_code][price['currency']['code']] = final_price

            return result_list

    async def get_rating(self, product_id):
        """
        get verified owner's rating
        :param product_id: products id
        :return: return format like this
                    {
                        'id':<product id>,
                        'count':<verified owner number>,
                        'value':<rating>(decimal object)
                    }
        """
        if isinstance(product_id, int) or isinstance(product_id, str):
            prod_ids = [str(product_id)]
        elif isinstance(product_id, list) or isinstance(product_id, tuple):
            prod_ids = list(map(str, product_id))
        else:
            raise TypeError(f'{APIUtility.func_name()} Args Type Error')

        self.__logger.info(
            f"Call {APIUtility.func_name()} ids=[{', '.join(str(prod_id) for prod_id in prod_ids)}]")
        urls = [f"{self.__hosts['rating'].replace('{productid}', prod_id)}" for prod_id in prod_ids]

        result = list()
        async with APIRequester(self.__retries, self.__concurrency) as request:
            rating_datas = await request.get_json(urls)
            for i in range(0, len(prod_ids)):
                try:
                    APIUtility.error_handler(rating_datas[i], prod_ids[i], is_raise=True)
                except Exception as e:
                    self.__logger.warning(f"{APIUtility.func_name()} error occurred: {str(e)}")
                    result.append(e)
                    continue
                rating = rating_datas[i]
                rating['id'] = prod_ids[i]
                rating['value'] = Decimal(rating['value']).quantize(Decimal('.00'))
                result.append(rating)

            return result

    async def get_extend_detail(self, product_id):
        id_list = list(map(str, product_id)) if isinstance(product_id, list) else [str(product_id)]
        urls = list(map(lambda x: f"{self.__hosts['extend_detail']}/{x}", id_list))
        params = {'expand': 'downloads'}

        self.__logger.info(f"Call {APIUtility.func_name()} ids=[{','.join(id_list)}]")

        async with APIRequester(self.__retries, self.__concurrency) as request:
            rep = await request.get_json(urls, params)

            result = list()
            for i in range(0, len(id_list)):
                detail = rep[i]
                try:
                    APIUtility.error_handler(detail, id_list[i], is_raise=True)
                except Exception as e:
                    self.__logger.warning(f"{APIUtility.func_name()} error occurred: {str(e)}")
                    result.append(e)
                    continue
                tmp_detail = dict()
                tmp_detail['id'] = detail['id']
                tmp_detail['slug'] = detail['slug']
                tmp_detail['content_system_compatibility'] = detail['content_system_compatibility']
                tmp_detail['downloads'] = detail['downloads']
                result.append(tmp_detail)

            return result

    async def login(self, username, passwd):
        """
        Login into GOG to get access token and refresh token
        Account need disable two step verification
        :param username: GOG username
        :param passwd: GOG password
        :return: dict object with access_token refresh_token expired_time and user_id
        """
        self.__logger.debug(f"Call {APIUtility.func_name()} username={username} password={passwd}")
        async with APIRequester(self.__retries, self.__concurrency) as request:
            authrep = await request.get(self.__hosts['auth'], self.__auth['auth'])
            APIUtility.error_handler(authrep, is_raise=True)
            etree = html5lib.parse(authrep['text'], treebuilder='lxml', namespaceHTMLElements=False)

            # check reCAPTCHA
            self.__logger.debug('Check reCAPTCHA')
            if len(etree.findall('.//div[@class="g-recaptcha form__recaptcha"]')) > 0:
                self.__logger.error("login error, GOG is asking for a reCAPTCHA :( try again in a few minutes.")
                raise GOGNeedVerification()

            # find login token
            self.__logger.debug('Find login token')
            for elm in etree.findall('.//input'):
                if elm.attrib['id'] == 'login__token':
                    self.__auth['login']['login[_token]'] = elm.attrib['value']

            # post data to login
            self.__logger.debug('POST data to login')
            self.__auth['login']['login[username]'] = username
            self.__auth['login']['login[password]'] = passwd
            loginrep = await request.post(self.__hosts['login'], self.__auth['login'], authrep['cookies'])
            APIUtility.error_handler(loginrep, is_raise=True)

            if 'on_login_success' not in str(loginrep['url']):
                self.__logger.error(f'login error, invalid username or password')
                raise GOGAccountError()
            else:
                self.__auth['token']['code'] = loginrep['url'].query['code']

            # get access token
            self.__logger.debug('Get access token')
            tokenrep = await request.get(self.__hosts['token'], self.__auth['token'], loginrep['cookies'])
            APIUtility.error_handler(tokenrep, is_raise=True)
            token = json.loads(tokenrep['text'])
            token['login_success'] = True
            token['last_update'] = datetime.utcnow()
            return token

    async def refresh_token(self, rtoken):
        self.__logger.debug(f"Call {APIUtility.func_name()}")
        self.__auth['refresh']['refresh_token'] = rtoken
        async with APIRequester(self.__retries, self.__concurrency) as request:
            tokenrep = await request.get_json(self.__hosts['token'], self.__auth['refresh'])
            APIUtility.error_handler(tokenrep, is_raise=True)
            token = tokenrep
            token['last_update'] = datetime.utcnow()
            return token
