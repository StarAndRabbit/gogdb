#!/usr/bin/env python
# encoding: utf-8

import logging
import html5lib
from datetime import datetime
from decimal import Decimal
from .utilities import Requester, func_name, CoroutinePool
from .gogexceptions import *


class APIUtility:

    def __init__(self):
        self.__logger = logging.getLogger('GOGDB.Utility')

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

    def merge_multi_prices_data(self, prices_data):
        self.__logger.debug(f'Call {func_name()}')
        ids = list()
        ret_prices = list()
        for price in prices_data:
            prod_id = price['product']
            merged_price = price
            if prod_id not in ids:
                ids.append(prod_id)
                temp_list = filter(lambda x: x["product"] == price["product"], prices_data)
                for i in temp_list:
                    merged_price['prices'] = {**merged_price['prices'], **i['prices']}
                ret_prices.append(merged_price)
            else:
                continue
        return ret_prices


class API:

    def __init__(self):
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
        self.__hosts['builds'] = 'https://content-system.gog.com/products/{productid}/os/{os}/builds?generation=2'

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

        self.__logger = logging.getLogger('GOGDB.GOGAPI')

        self.__utl = APIUtility()

    @property
    def logger(self):
        return self.__logger

    @property
    def hosts(self):
        return self.__hosts

    async def get_total_num(self):
        self.__logger.debug(f"Call {func_name()}")
        async with Requester() as req:
            fst_page = await req.get_json(self.__hosts['detail'])

            try:
                limit = fst_page['limit']
                pages = fst_page['pages']
                lst_page_url = fst_page['_links']['last']['href']
            except Exception as e:
                self.__logger.error(f"{func_name()} {type(e).__name__} {e}")
                raise

            lst_page = await req.get_json(lst_page_url)
            try:
                lst_num = len(lst_page['_embedded']['items'])
            except Exception as e:
                self.__logger.error(f"[{func_name()}] {type(e).__name__} {e}")
                raise

            return limit * (pages - 1) + lst_num

    async def get_product_id_in_page(self, page, limit=50):
        self.__logger.debug(f"Call {func_name()}")
        params = {'page': page, 'limit': limit, 'locale': 'en-US'}
        async with Requester() as req:
            page_data = await req.get_json(self.hosts['detail'], params=params)

            try:
                items = page_data['_embedded']['items']
            except Exception as e:
                self.__logger.error(f"[{func_name()}] {type(e).__name__} {e}")
                raise

            result = list()
            for item in items:
                try:
                    result.append(item['_embedded']['product']['id'])
                except Exception as e:
                    self.__logger.error(f"{func_name()} {type(e).__name__} {e}")
                    raise
            return result

    async def get_product_id_in_pages(self, pages: list, limit=50):
        self.__logger.debug(f"Call {func_name()}")
        coro_pool = CoroutinePool(coro_list=[self.get_product_id_in_page(page, limit) for page in pages])
        return await coro_pool.run_all()

    async def get_all_product_id(self):
        self.__logger.debug(f"Call {func_name()}")
        async with Requester() as request:
            pages_data = await request.get_json(self.__hosts['detail'])
            try:
                pages = pages_data['pages']
            except Exception as e:
                self.__logger.error(f"{func_name()} {type(e).__name__} {e}")
                raise

        pages = range(1, pages+1)
        return await self.get_product_id_in_pages(pages, limit=50)

    async def get_product_data(self, product_id: str):
        self.__logger.debug(f"Call {func_name()} id={product_id}")

        params = {'locale': 'en-US'}
        url = f"{self.__hosts['detail']}/{product_id}"

        async with Requester() as request:
            try:
                return await request.get_json(url, params)
            except GOGNotFound:
                raise GOGProductNotFound(product_id)
            except Exception:
                raise

    async def get_product_achievement(self, client_id, user_id, token_type, access_token):
        self.__logger.debug(f"Call {func_name()}")
        url = self.__hosts['achievement'].replace('{clientid}', client_id).replace('{userid}', user_id)
        headers = {'Authorization': f'{token_type.title()} {access_token}'}
        async with Requester() as request:
            return await request.get_json(url, headers=headers)

    async def get_countries(self):
        self.__logger.debug(f"Call {func_name()}")
        async with Requester() as request:
            return await request.get_json(self.__hosts['region'])

    async def get_price_in_country(self, product_ids: list, country: str):
        id_list = list(map(str, product_ids))
        prod_ids = ','.join(id_list)
        params = {'ids': prod_ids, 'countryCode': country}

        self.__logger.debug(f"Call {func_name()} ids=[{prod_ids}] countries={country}")

        async with Requester() as request:
            prices_in_country = await request.get_json(self.__hosts['multiprice'], params)

            results = list()
            for prod_price in prices_in_country['_embedded']['items']:
                ret_data = dict()
                prod_price = prod_price['_embedded']
                ret_data['product'] = prod_price['product']['id']
                ret_data['prices'] = dict()
                price_data = list()
                for i in range(0, len(prod_price['prices'])):
                    ret_price = dict()
                    ret_price['currency'] = prod_price['prices'][i]['currency']['code']
                    ret_price['isDefault'] = True if i == 0 else False
                    ret_price['basePrice'] = self.__utl.price_parse(prod_price['prices'][i]['basePrice'])
                    ret_price['finalPrice'] = self.__utl.price_parse(prod_price['prices'][i]['finalPrice'])
                    price_data.append(ret_price)

                ret_data['prices'][country] = price_data
                results.append(ret_data)
            return results

    async def get_price_in_countries(self, product_ids: list, countries: list):
        self.__logger.debug(f"Call {func_name()} ids={product_ids} countries={countries}")
        coro_pool = CoroutinePool(coro_list=[self.get_price_in_country(product_ids, country) for country in countries])
        results = sum(await coro_pool.run_all(), [])
        return self.__utl.merge_multi_prices_data(results)

    async def get_rating(self, product_id):
        """
        get verified owner's rating
        :param product_id: product id
        :return: return format like this
                    {
                        'id':<product id>,
                        'count':<verified owner number>,
                        'value':<rating>(decimal object)
                    }
        """
        self.__logger.info(f"Call {func_name()} id={product_id}")
        url = f"{self.__hosts['rating'].replace('{productid}', str(product_id))}"

        async with Requester() as request:
            rating_data = await request.get_json(url)
            rating_data['id'] = product_id
            rating_data['value'] = Decimal(rating_data['value']).quantize(Decimal('.00'))
            return rating_data

    async def get_extend_detail(self, product_id):
        url = f"{self.__hosts['extend_detail']}/{product_id}"
        params = {'expand': 'downloads'}

        self.__logger.info(f"Call {func_name()} id={product_id}")

        async with Requester() as request:
            try:
                detail = await request.get_json(url, params)
                ret = dict()
                ret['id'] = detail['id']
                ret['slug'] = detail['slug']
                ret['content_system_compatibility'] = detail['content_system_compatibility']
                ret['downloads'] = detail['downloads']
                return ret
            except GOGNotFound:
                raise GOGProductNotFound(product_id)
            except Exception:
                raise

    async def get_product_builds(self, product_id, os: str):
        self.__logger.info(f"Call {func_name()} id={product_id} os={os}")

        url = f"{self.__hosts['builds'].replace('{productid}', str(product_id)).replace('{os}', os)}"
        async with Requester() as request:
            return await request.get_json(url)

    async def login(self, username, passwd):
        """
        Login into GOG to get access token and refresh token
        Account need disable two step verification
        :param username: GOG username
        :param passwd: GOG password
        :return: dict object with access_token refresh_token expired_time and user_id
        """
        self.__logger.debug(f"Call {func_name()} username={username} password={passwd}")
        async with Requester() as request:
            authrep = await request.get(self.__hosts['auth'], params=self.__auth['auth'])
            etree = html5lib.parse(authrep.text, treebuilder='lxml', namespaceHTMLElements=False)

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
            loginrep = await request.post(self.__hosts['login'], data=self.__auth['login'], cookies=authrep.cookies)

            if 'on_login_success' not in str(loginrep.url):
                self.__logger.error(f'login error, invalid username or password')
                raise GOGAccountError()
            else:
                self.__auth['token']['code'] = loginrep.url.query['code']

            # get access token
            self.__logger.debug('Get access token')
            tokenrep = await request.get(self.__hosts['token'], params=self.__auth['token'], cookies=loginrep.cookies)
            token = tokenrep.json
            token['login_success'] = True
            token['last_update'] = datetime.utcnow()
            return token

    async def refresh_token(self, rtoken):
        self.__logger.debug(f"Call {func_name()}")
        self.__auth['refresh']['refresh_token'] = rtoken
        async with Requester() as request:
            token = await request.get_json(self.__hosts['token'], self.__auth['refresh'])
            token['last_update'] = datetime.utcnow()
            return token


gogapi = API()
