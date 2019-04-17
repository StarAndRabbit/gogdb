#!/usr/bin/env python
# encoding: utf-8

import aiohttp, asyncio
from fake_useragent import UserAgent
import logging


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

    async def getjson(self, url, params=None):
        if isinstance(url, str) and (isinstance(params, dict) or params == None):
            return await self.__getjson(url, params)
        elif isinstance(url, list) and (isinstance(params, dict) or params == None):
            return await self.__getjson_multi_urls(url, params)
        elif isinstance(url, str) and isinstance(params, list):
            return await self.__getjson_multi_params(url, params)


    async def __getjson(self, url, params):
        retries = 0
        logstr = 'request %s with params %s' % (url, params)
        self.__logger.debug('Now %s' % logstr)
        while True:
            async with self.__session.get(url, params=params) as resp:
                try:
                    resp.raise_for_status()
                except Exception as e:
                    retries += 1
                    if retries <= self.__retries:
                        continue
                    else:
                        self.__logger.error('Fatal error occured when %s: %s' % (logstr, e))
                        return {'error':True, 'errorType':type(e).__name__, 'errorMessage':resp.reason, 'responseStatus':resp.status}
                try:
                    return await resp.json()
                except Exception as e:
                    self.__logger.error('Fatal error occured when %s: %s' % (logstr, e))
                    return {'error':True, 'errorType':type(e).__name__, 'errorMessage':str(e), 'responseStatus':resp.status}


    async def __getjson_multi_urls(self, urls, params):
        if len(urls) <= self.__concurrency:
            return await asyncio.gather(*[self.__getjson(url, params) for url in urls], return_exceptions=True)
        else:
            result = list()
            start = 0
            end = self.__concurrency
            while True:
                result.extend(await asyncio.gather(*[self.__getjson(url, params) for url in urls[start:end]], return_exceptions=True))
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
                result.extend(await asyncio.gather(*[self.__getjson(url, param) for param in params[start:end]], return_exceptions=True))
                if end > len(params):
                    return result
                else:
                    start = end
                    end += self.__concurrency


class APIUtility():

    def __init__(self):
        self.__logger = logging.getLogger('GOGDB.UTILITY')

    def errorchk(self, jsondata):
        error = jsondata.get('error', False)
        if error:
            self.__logger.warning('Error occured on request, may lost data')
        return error

    def product_notfoundchk(self, productid, productdata):
        if "message" in productdata:
            msg = productdata['message']
            if t:
                self.__logger.error('Product %s not found' % productid)
                return True
            else:
                self.__logger.error('Product id may error, product data here %s' % productdata)
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
                    'errorType':'ClientResponseError'}
            return err_msg

        return productdata


class API():

    def __init__(self, retries=5):
        self.__hosts = dict()
        self.__hosts['detail'] = 'https://api.gog.com/v2/games'
        self.__hosts['price'] = 'https://api.gog.com/products/{productid}/prices'
        self.__hosts['multiprice'] = 'https://api.gog.com/products/prices'
        self.__hosts['region'] = 'https://countrycode.org/api/countryCode/countryMenu'
        self.__hosts['rating'] = 'https://reviews.gog.com/v1/products/{productid}/averageRating?reviewer=verified_owner'

        self.__retries = retries
        self.__logger = logging.getLogger('GOGDB.GOGAPI')

        self.__utl = APIUtility()

    @property
    def retries(self):
        return self.__retries

    @retries.setter
    def retries(self, value):
        self.__retries = value

    @property
    def logger(self):
        return self.__logger

    @property
    def hosts(self):
        return self.__hosts


    async def get_total_num(self):
        self.__logger.debug("Call %s" % self.get_total_num.__name__)
        async with APIRequester(self.__retries) as request:
            fst_page = await request.getjson(self.__hosts['detail'])

            if self.__utl.errorchk(fst_page):
                return -1
            try:
                limit = fst_page['limit']
                pages = fst_page['pages']
                lst_page_url = fst_page['_links']['last']['href']
            except Exception as e:
                self.__logger.error("[%s] %s %s" % (self.get_total_num.__name__, type(e).__name__, e))
                return -1

            lst_page = await request.getjson(lst_page_url)
            if self.__utl.errorchk(lst_page):
                return -1
            try:
                lst_num = len(lst_page['_embedded']['items'])
            except Exception as e:
                self.__logger.error("[%s] %s %s" % (self.get_total_num.__name__, type(e).__name__, e))
                return -1

            return limit * (pages - 1) + lst_num


    async def get_product_id_in_page(self, page, limit=50):
        self.__logger.info("Call %s" % self.get_product_id_in_page.__name__)
        params = {'page':page, 'limit':limit, 'locale':'en-US'}
        async with APIRequester(self.__retries) as request:
            page_data = await request.getjson(self.hosts['detail'], params=params)
            if self.__utl.errorchk(page_data):
                return [-1]
            try:
                items = page_data['_embedded']['items']
            except Exception as e:
                self.__logger.error("[%s] %s %s" % (self.get_product_id_in_page.__name__, type(e).__name__, e))
                return [-1]

            result = list()
            for item in items:
                try:
                    result.append(item['_embedded']['product']['id'])
                except Exception as e:
                    self.__logger.error("[%s] %s %s" % (self.get_product_id_in_page.__name__, type(e).__name__, e))
                    result.append(-1)           # Error Flag
            return result


    async def get_all_product_id(self):
        self.__logger.info("Call %s" % self.get_all_product_id.__name__)
        async with APIRequester(self.__retries) as request:
            pages_data = await request.getjson(self.__hosts['detail'])
            if self.__utl.errorchk(pages_data):
                return [-1]
            try:
                pages = pages_data['pages']
            except Exception as e:
                self.__logger.error("[%s] %s %s" % (self.get_all_product_id.__name__, type(e).__name__, e))
                return [-1]
            params = [{'page':page, 'locale':'en-US'} for page in range(1, pages+1)]
            results = await request.getjson(self.__hosts['detail'], params)

            sum_ids = list()
            for result in results:
                try:
                    items = result['_embedded']['items']
                except Exception as e:
                    self.__logger.error("[%s] %s %s" % (self.get_all_product_id.__name__, type(e).__name__, e))
                    sum_ids.append(-1)          # Error Flag
                    continue

                ids = list()
                for item in items:
                    try:
                        ids.append(item['_embedded']['product']['id'])
                    except Exception as e:
                        self.__logger.error("[%s] %s %s" % (self.get_all_product_id.__name__, type(e).__name__, e))
                        ids.append(-1)          # Error Flag
                        continue
                sum_ids.extend(ids)

            return sum_ids

    async def get_product_data(self, product_id):
        params = {'locale':'en-US'}

        if isinstance(product_id, int) or isinstance(product_id, str):
            self.__logger.info('Call %s, ids=[%s]' % (self.get_product_data.__name__, str(product_id)))
            async with APIRequester(self.__retries) as request:
                return self.__utl.product_errorchk(product_id,
                        await request.getjson(f"{self.__hosts['detail']}/{product_id}", params))

        elif isinstance(product_id, list) or isinstance(product_id, tuple):
            self.__logger.info('Call %s, ids=[%s]' % (self.get_product_data.__name__, ', '.join(str(proid) for proid in product_id)))
            urls = [f"{self.__hosts['detail']}/{proid}" for proid in product_id]

            async with APIRequester(self.__retries) as request:
                product_datas = await request.getjson(urls, params)
                for i in range(0, len(product_id)):
                    product_datas[i] = self.__utl.product_errorchk(product_id[i], product_datas[i])

                return product_datas

        else:
            return {'error':True,
                    'errorType':'TypeError',
                    'errorMessage':'product_id just support int, string, list or tuple',
                    'id':product_id}


if __name__ == "__main__":
    import time

    logger = logging.getLogger('GOGDB')
    logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s | %(name)s | %(levelname)s | %(message)s')
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)
    api = API()
    logger.info('Total Products: %s' % asyncio.run(api.get_total_num()))
    start = time.time()
    ids = asyncio.run(api.get_all_product_id())
    logger.info('Total Products: %s' % len(ids))
    logger.info('Get All Product ID time usage: %s' % (time.time() - start))
    if -1 in ids:
        logger.error('Error occured when get all product id')

    proid = 1943729714
    product_data = asyncio.run(api.get_product_data(proid))
    if product_data.get('error', False):
        logger.error(f'Error occured when get product {proid}')
    else:
        logger.info(f'Get product {proid} success')

    asyncio.run(api.get_product_data([1,2,3,4,5,6,7,8,9,0]))
