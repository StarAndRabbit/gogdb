#!/usr/bin/env python
# encoding: utf-8

import aiohttp, asyncio
from fake_useragent import UserAgent
import logging
import html5lib
import json
import re
from datetime import datetime
from decimal import Decimal


class APIRequester:

    def __init__(self, retries=5, concurrency=10):
        self.__retries = retries
        self.__concurrency = concurrency
        self.__logger = logging.getLogger('GOGDB.REQUESTER')

    async def __aenter__(self):
        self.__ua = UserAgent().random
        self.__session = aiohttp.ClientSession(headers={'User-Agent':self.__ua})
        return self

    async def __aexit__(self, *err):
        await self.__session.close()
        self.__session = None

    async def post(self, url, params=None, cookies=None):
        retries = 0
        logstr = f'request {url} with params {params}'
        self.__logger.debug(f'Now {logstr}')
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
                            self.__logger.error(f'Fatal error occurred when {logstr}: {e}')
                            return {
                                'error': True,
                                'errorType': type(e).__name__,
                                'errorMessage': resp.reason,
                                'responseStatus': resp.status
                            }
                    try:
                        return {
                            'headers': resp.headers,
                            'cookies': resp.cookies,
                            'text': await resp.text(),
                            'history': resp.history,
                            'url': resp.url
                        }
                    except Exception as e:
                        self.__logger.error(f'Fatal error occurred when {logstr}: {e}')
                        return {
                            'error': True,
                            'errorType': type(e).__name__,
                            'errorMessage': str(e),
                            'responseStatus': resp.status
                        }
            except aiohttp.ClientConnectorError as e:
                retries += 1
                if retries <= self.__retries:
                    self.__logger.debug('Network error, retry...')
                    continue
                else:
                    self.__logger.error(f'Network error occurred when {logstr}: {e}')
                    return {
                        'error': True,
                        'errorType': type(e).__name__,
                        'errorMessage': str(e)
                    }

    async def get(self, url, params=None, cookies=None):
        retries = 0
        logstr = f'request {url} with params {params}'
        self.__logger.debug(f'Now {logstr}')
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
                            self.__logger.error(f'Fatal error occurred when {logstr}: {e}')
                            return {
                                'error': True,
                                'errorType': type(e).__name__,
                                'errorMessage': resp.reason,
                                'responseStatus': resp.status
                            }
                    try:
                        return {
                            'headers': resp.headers,
                            'cookies': resp.cookies,
                            'text': await resp.text(),
                            'history': resp.history,
                            'url': resp.url
                        }
                    except Exception as e:
                        self.__logger.error(f'Fatal error occurred when {logstr}: {e}')
                        return {
                            'error': True,
                            'errorType': type(e).__name__,
                            'errorMessage': str(e),
                            'responseStatus': resp.status
                        }
            except aiohttp.ClientConnectorError as e:
                retries += 1
                if retries <= self.__retries:
                    self.__logger.debug('Network error, retry...')
                    continue
                else:
                    self.__logger.error(f'Network error occurred when {logstr}: {e}')
                    return {
                        'error': True,
                        'errorType': type(e).__name__,
                        'errorMessage': str(e)
                    }

    async def getjson(self, url, params=None):
        if isinstance(url, str) and (isinstance(params, dict) or params == None):
            return await self.__getjson(url, params)
        elif isinstance(url, list) and (isinstance(params, dict) or params == None):
            return await self.__getjson_multi_urls(url, params)
        elif isinstance(url, str) and isinstance(params, list):
            return await self.__getjson_multi_params(url, params)

    async def __getjson(self, url, params):
        retries = 0
        logstr = f'request {url} with params {params}'
        self.__logger.debug(f'Now {logstr}')
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
                            self.__logger.error(f'Fatal error occurred when {logstr}: {e}')
                            return {
                                'error':True,
                                'errorType':type(e).__name__,
                                'errorMessage':resp.reason,
                                'responseStatus':resp.status
                            }
                    try:
                        return await resp.json()
                    except Exception as e:
                        self.__logger.error(f'Fatal error occurred when {logstr}: {e}')
                        return {
                            'error':True,
                            'errorType':type(e).__name__,
                            'errorMessage':str(e),
                            'responseStatus':resp.status
                        }
            except aiohttp.ClientConnectorError as e:
                retries += 1
                if retries <= self.__retries:
                    self.__logger.debug('Network error, retry...')
                    continue
                else:
                    self.__logger.error(f'Network error occurred when {logstr}: {e}')
                    return {
                        'error':True,
                        'errorType':type(e).__name__,
                        'errorMessage':str(e)
                    }

    async def __getjson_multi_urls(self, urls, params):
        if len(urls) <= self.__concurrency:
            return await asyncio.gather(*[self.__getjson(url, params) for url in urls], return_exceptions=True)
        else:
            result = list()
            start = 0
            end = self.__concurrency
            while True:
                result.extend(await asyncio.gather(*[self.__getjson(url, params) for url in urls[start:end]],
                                                   return_exceptions=True))
                if end > len(urls):
                    return result
                else:
                    start = end
                    end += self.__concurrency

    async def __getjson_multi_params(self, url, params):
        if len(params) <= self.__concurrency:
            return await asyncio.gather(*[self.__getjson(url, param) for param in params], return_exceptions=True)
        else:
            result = list()
            start = 0
            end = self.__concurrency
            while True:
                result.extend(await asyncio.gather(*[self.__getjson(url, param) for param in params[start:end]],
                                                   return_exceptions=True))
                if end > len(params):
                    return result
                else:
                    start = end
                    end += self.__concurrency


class APIUtility():

    def __init__(self):
        self.__logger = logging.getLogger('GOGDB.UTILITY')

    def errorchk(self, jsondata):
        if not isinstance(jsondata, dict):
            return False
        error = jsondata.get('error', False)
        if error:
            self.__logger.warning('Error occurred on request, may lost data')
        return error

    def product_notfoundchk(self, productid, productdata):
        if "message" in productdata:
            msg = productdata['message']
            if 'not found' in msg:
                self.__logger.error(f'Product {productid} not found')
                return True
            else:
                self.__logger.error(f'Product id may error, product data here {productdata}')
                return False
        else:
            return False

    def product_errorchk(self, productid, productdata):
        if self.errorchk(productdata):
            productdata['id'] = productid
            return productdata

        if self.product_notfoundchk(productid, productdata):
            err_msg = {
                'id':productid,
                'error':True,
                'responseStatus':404,
                'errorMessage':'Not Found',
                'errorType':'ClientResponseError'
            }
            return err_msg

        return productdata

    def price_parse(self, price_string):
        '''
        format price string into dict
        :param price_string: price string format like "999 USD"
        :return: Decimal object
        '''
        price_tmp = price_string.strip().split(' ')
        price_tmp[0] = price_tmp[0][:len(price_tmp[0])-2] + '.' + price_tmp[0][len(price_tmp[0])-2:]
        return Decimal(price_tmp[0]).quantize(Decimal('.00'))

    def get_id_from_url(self, url):
        t = re.findall('\d+', url)
        if t:
            return max(t, key=len)
        else:
            return None

    def get_country_code_from_url(self, url):
        t = re.findall('countryCode=.*', url)
        if t:
            return max(t, key=len).strip().split('=')[1].lower()
        else:
            return None


class API():

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
        self.__logger.debug(f"Call {self.get_total_num.__name__}")
        async with APIRequester(self.__retries, self.__concurrency) as request:
            fst_page = await request.getjson(self.__hosts['detail'])

            if self.__utl.errorchk(fst_page):
                return -1
            try:
                limit = fst_page['limit']
                pages = fst_page['pages']
                lst_page_url = fst_page['_links']['last']['href']
            except Exception as e:
                self.__logger.error(f"{self.get_total_num.__name__} {type(e).__name__} {e}")
                return -1

            lst_page = await request.getjson(lst_page_url)
            if self.__utl.errorchk(lst_page):
                return -1
            try:
                lst_num = len(lst_page['_embedded']['items'])
            except Exception as e:
                self.__logger.error(f"[{self.get_total_num.__name__}] {type(e).__name__} {e}")
                return -1

            return limit * (pages - 1) + lst_num

    async def get_product_id_in_page(self, page, limit=50):
        self.__logger.info(f"Call {self.get_product_id_in_page.__name__}")
        params = {'page':page, 'limit':limit, 'locale':'en-US'}
        async with APIRequester(self.__retries, self.__concurrency) as request:
            page_data = await request.getjson(self.hosts['detail'], params=params)
            if self.__utl.errorchk(page_data):
                return [-1]
            try:
                items = page_data['_embedded']['items']
            except Exception as e:
                self.__logger.error(f"[{self.get_product_id_in_page.__name__}] {type(e).__name__} {e}")
                return [-1]

            result = list()
            for item in items:
                try:
                    result.append(item['_embedded']['product']['id'])
                except Exception as e:
                    self.__logger.error(f"{self.get_product_id_in_page.__name__} {type(e).__name__} {e}")
                    result.append(-1)           # Error Flag
            return result

    async def get_all_product_id(self):
        self.__logger.info("Call %s" % self.get_all_product_id.__name__)
        async with APIRequester(self.__retries, self.__concurrency) as request:
            pages_data = await request.getjson(self.__hosts['detail'])
            if self.__utl.errorchk(pages_data):
                return [-1]
            try:
                pages = pages_data['pages']
            except Exception as e:
                self.__logger.error(f"{self.get_all_product_id.__name__} {type(e).__name__} {e}")
                return [-1]
            params = [{'page':page, 'locale':'en-US'} for page in range(1, pages+1)]
            results = await request.getjson(self.__hosts['detail'], params)

            sum_ids = list()
            for result in results:
                try:
                    items = result['_embedded']['items']
                except Exception as e:
                    self.__logger.error(f"{self.get_all_product_id.__name__} {type(e).__name__} {e}")
                    sum_ids.append(-1)          # Error Flag
                    continue

                ids = list()
                for item in items:
                    try:
                        ids.append(item['_embedded']['product']['id'])
                    except Exception as e:
                        self.__logger.error(f"{self.get_all_product_id.__name__} {type(e).__name__} {e}")
                        ids.append(-1)          # Error Flag
                        continue
                sum_ids.extend(ids)

            return sum_ids

    async def get_product_data(self, product_id):
        params = {'locale':'en-US'}

        if isinstance(product_id, int) or isinstance(product_id, str):
            ids = [str(product_id)]
        elif isinstance(product_id, list) or isinstance(product_id, tuple):
            ids = list(map(str, product_id))
        else:
            return {
                'error': True,
                'errorType': 'TypeError',
                'errorMessage': 'product_id just support int, string, list or tuple',
                'id': product_id
            }

        self.__logger.info(
            f"Call {self.get_product_data.__name__} ids=[{', '.join(str(proid) for proid in ids)}]")

        urls = [f"{self.__hosts['detail']}/{proid}" for proid in ids]

        async with APIRequester(self.__retries, self.__concurrency) as request:
            product_datas = await request.getjson(urls, params)
            for i in range(0, len(ids)):
                product_datas[i] = self.__utl.product_errorchk(ids[i], product_datas[i])

            return product_datas

    async def get_countries(self):
        async with APIRequester(self.__retries, self.__concurrency) as request:
            return await request.getjson(self.__hosts['region'])

    async def get_product_prices(self, product_id, countries):
        '''
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
        '''
        id_list = list(map(str, product_id)) if isinstance(product_id, list) else [str(product_id)]
        ids = ','.join(id_list)
        if not isinstance(countries, list):
            params = [{'ids':ids, 'countryCode':str(countries)}]
        else:
            params = [{'ids':ids, 'countryCode':str(countryCode)} for countryCode in countries]

        async with APIRequester(self.__retries, self.__concurrency) as request:
            rep = await request.getjson(self.__hosts['multiprice'], params)
            result_list = {prodid:{'basePrice':dict(), 'finalPrice':dict()} for prodid in id_list}
            for data in rep:
                if not self.__utl.errorchk(data):
                    for item in data['_embedded']['items']:
                        prod_id = self.__utl.get_id_from_url(item['_links']['self']['href'])
                        countryCode = self.__utl.get_country_code_from_url(item['_links']['self']['href'])
                        result_list[prod_id]['basePrice'][countryCode] = dict()
                        result_list[prod_id]['finalPrice'][countryCode] = dict()

                        result_list[prod_id]['basePrice'][countryCode]['defaultCurrency'] = \
                            item['_embedded']['prices'][0]['currency']['code']
                        result_list[prod_id]['finalPrice'][countryCode]['defaultCurrency'] = \
                            item['_embedded']['prices'][0]['currency']['code']

                        for price in item['_embedded']['prices']:
                            base_price = self.__utl.price_parse(price['basePrice'])
                            final_price = self.__utl.price_parse(price['finalPrice'])
                            result_list[prod_id]['basePrice'][countryCode][price['currency']['code']] = base_price
                            result_list[prod_id]['finalPrice'][countryCode][price['currency']['code']] = final_price

            return result_list

    async def get_rating(self, product_id):
        if isinstance(product_id, int) or isinstance(product_id, str):
            ids = [str(product_id)]
        elif isinstance(product_id, list) or isinstance(product_id, tuple):
            ids = list(map(str, product_id))
        else:
            return {
                'error': True,
                'errorType': 'TypeError',
                'errorMessage': 'product_id just support int, string, list or tuple',
                'id': product_id
            }

        result = {prodid:{} for prodid in ids}
        self.__logger.info(
            f"Call {self.get_rating.__name__} ids=[{', '.join(str(proid) for proid in ids)}]")
        urls = [f"{self.__hosts['rating'].replace('{productid}', proid)}" for proid in ids]

        async with APIRequester(self.__retries, self.__concurrency) as request:
            rating_datas = await request.getjson(urls)
            for i in range(0, len(ids)):
                if not self.__utl.errorchk(rating_datas[i]):
                    result[ids[i]] = rating_datas[i]
                    result[ids[i]]['value'] = Decimal(result[ids[i]]['value']).quantize(Decimal('.00'))

            return result

    async def get_extend_detail(self, product_id):
        id_list = list(map(str, product_id)) if isinstance(product_id, list) else [str(product_id)]
        ids = ','.join(id_list)
        params = {'ids':ids, 'expand':'downloads'}

        self.__logger.info(f"Call {self.get_extend_detail.__name__} ids=[{ids}]")

        async with APIRequester(self.__retries, self.__concurrency) as request:
            rep = await request.getjson(self.__hosts['extend_detail'], params)
            result = list()
            for detail in rep:
                if not self.__utl.errorchk(detail):
                    tmp_detail = dict()
                    tmp_detail['id'] = detail['id']
                    tmp_detail['slug'] = detail['slug']
                    tmp_detail['content_system_compatibility'] = detail['content_system_compatibility']
                    tmp_detail['downloads'] = detail['downloads']
                    result.append(tmp_detail)

            return result

    async def login(self, username, passwd):
        async with APIRequester(self.__retries, self.__concurrency) as request:
            authrep = await request.get(self.__hosts['auth'], self.__auth['auth'])
            if self.__utl.errorchk(authrep):
                self.__logger.error(f'login error')
                authrep['login_success'] = False
                return authrep

            etree = html5lib.parse(authrep['text'], treebuilder='lxml', namespaceHTMLElements=False)

            # check reCAPTCHA
            if len(etree.findall('.//div[@class="g-recaptcha form__recaptcha"]')) > 0:
                self.__logger.error("login error, GOG is asking for a reCAPTCHA :( try again in a few minutes.")
                return {
                    'login_success': False
                }
            # find login token
            for elm in etree.findall('.//input'):
                if elm.attrib['id'] == 'login__token':
                    self.__auth['login']['login[_token]'] = elm.attrib['value']

            # post data to login
            self.__auth['login']['login[username]'] = username
            self.__auth['login']['login[password]'] = passwd
            loginrep = await request.post(self.__hosts['login'], self.__auth['login'], authrep['cookies'])
            if self.__utl.errorchk(loginrep):
                self.__logger.error(f'login error')
                loginrep['login_success'] = False
                return loginrep
            if 'on_login_success' not in str(loginrep['url']):
                self.__logger.error(f'login error, invalid username or password')
                return {
                    'login_success': False
                }
            else:
                self.__auth['token']['code'] = loginrep['url'].query['code']

            # get access token
            tokenrep = await request.get(self.__hosts['token'], self.__auth['token'], loginrep['cookies'])
            if self.__utl.errorchk(tokenrep):
                self.__logger.error(f'login error')
                tokenrep['login_success'] = False
                return tokenrep
            else:
                token = json.loads(tokenrep['text'])
                token['login_success'] = True
                token['last_update'] = datetime.utcnow()
                return token

    async def refresh_token(self, rtoken):
        self.__auth['refresh']['refresh_token'] = rtoken
        async with APIRequester(self.__retries, self.__concurrency) as request:
            tokenrep = await request.getjson(self.__hosts['token'], self.__auth['refresh'])
            if self.__utl.errorchk(tokenrep):
                self.logger.error(f'refresh error, please check refresh_token')
                return tokenrep
            else:
                token = tokenrep
                token['last_update'] = datetime.utcnow()
                return token


if __name__ == "__main__":
    import time

    logger = logging.getLogger('GOGDB')
    logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s | %(name)s | %(levelname)s | %(message)s')
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)
    api = API(concurrency=16)
    logger.info(f'Total Products: {asyncio.run(api.get_total_num())}')
    start = time.time()
    ids = asyncio.run(api.get_all_product_id())
    logger.info(f'Total Products: {len(ids)}')
    logger.info(f'Get All Product ID time usage: {time.time() - start}')
    if -1 in ids:
        logger.error('Error occurred when get all product id')

    proid = 1943729714
    product_data = asyncio.run(api.get_product_data(proid))
    if product_data[0].get('error', False):
        logger.error(f'Error occurred when get product {proid}')
    else:
        logger.info(f'Get product {proid} success')
    asyncio.run(api.get_product_data([1,2,3,4,5,6,7,8,9,0]))
    asyncio.run(api.get_countries())
    asyncio.run(api.get_product_prices(['1', '2', '3', '4', '5'], ['CN', 'RU', 'US']))
    asyncio.run(api.get_rating([1,2,3,4,5]))
    asyncio.run(api.get_extend_detail([1,2,3,4,5]))
