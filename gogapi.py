import requests, json
from requests.adapters import HTTPAdapter
from multiprocessing.dummy import Pool as ThreadPool
import grequests, re, logging
from fake_useragent import UserAgent


class utility():
    @staticmethod
    def get_game_id_from_url(url):
        t = re.findall('\d+', url)
        if t:
            return max(t, key=len)
        else:
            return None

    @staticmethod
    def price_data_parse(gameid, price_data, country):
        if price_data == None:
            return {'gameId':gameid,
                    'currency':'',
                    'basePrice':None,
                    'finalPrice':None,
                    'country':country}
        else:
            if '_embedded' in price_data:
                price_data = price_data['_embedded']['prices'][0]
                price = dict()
                price['gameId'] = gameid
                price['currency'] = price_data['currency']['code']
                price['basePrice'] = round(int(price_data['basePrice'].split(' ')[0]) * 0.01, 2)
                price['finalPrice'] = round(int(price_data['finalPrice'].split(' ')[0]) * 0.01, 2)
                price['country'] = country
                return price
            else:
                return {'gameId':gameid,
                        'currency':'',
                        'basePrice':None,
                        'finalPrice':None,
                        'country':country}


class API(object):

    def __init__(self):
        self._hosts = dict()
        self._hosts['detail'] = 'https://api.gog.com/v2/games'
        self._hosts['price'] = 'https://api.gog.com/products/{gameid}/prices'
        self._hosts['multiprice'] = 'https://api.gog.com/products/prices'
        self._hosts['region'] = 'https://countrycode.org/api/countryCode/countryMenu'
        self._hosts['rating'] = 'https://reviews.gog.com/v1/products/{gameid}/averageRating?reviewer=verified_owner'
        self._timeout = 5
        self._retries = 5
        self._sess = requests.Session()
        self._sess.mount('https://', HTTPAdapter(max_retries=self._retries))
        self._sess.mount('http://', HTTPAdapter(max_retries=self._retries))
        self._ua = UserAgent()
        self._logger = logging.getLogger('GOGDB.GOGAPI')


    @property
    def logger(self):
        return self._logger

    @property
    def _req_sess(self):
        self._sess.headers.update({'User-Agent':self._ua.random})
        return self._sess

    @property
    def hosts(self):
        return self._hosts

    @property
    def timeout(self):
        return self._timeout

    @timeout.setter
    def timeout(self, value):
        if type(value) != type(int()):
            raise TypeError('Invalid Type')
        self._timeout = value

    @property
    def retries(self):
        return self._retries

    @retries.setter
    def retries(self, value):
        if type(value) != type(int()):
            raise TypeError('Invalid Type')
        self._retries = value


    def update_proxies(self, proxies):
        if type(proxies) != type(dict()):
            raise TypeError('Invalid Type')
        else:
            self._req_sess.proxies.update(proxies)


    def get_total_num(self):
        fst_page_data = self._req_sess.get(self.hosts['detail'], timeout=self.timeout).json()
        limit = fst_page_data['limit']
        pages = fst_page_data['pages']

        lst_page_data = self._req_sess.get(fst_page_data['_links']['last']['href'], timeout=self.timeout).json()
        return limit * (pages - 1) + len(lst_page_data['_embedded']['items'])


    def get_game_id_in_page(self, page, limit):
        payload = {'page':page, 'limit':limit, 'locale':'en-US'}
        page_data = self._req_sess.get(self.hosts['detail'], params=payload, timeout=self.timeout).json()
        items = page_data['_embedded']['items']

        for item in items:
            yield item['_embedded']['product']['id']


    def get_all_game_id(self):
        pages = self._req_sess.get(self.hosts['detail'], timeout=self.timeout).json()['pages']
        pages = range(1, pages+1)
        urls = [self.hosts['detail'] + '?limit=50&page=' + str(p) for p in pages]
        rs = (grequests.get(u, timeout=self.timeout, session=self._req_sess) for u in urls)
        results = grequests.imap(rs, size=10)

        for rep in results:
            items = rep.json()['_embedded']['items']
            for item in items:
                yield item['_embedded']['product']['id']


    def get_game_data(self, game_id):
        payload = {'locale':'en-US'}

        if type(game_id) == type(int()) or type(game_id) == type(str()):
            self._logger.info('read game data, ids=[%s]' % str(game_id))
            yield self._req_sess.get(self.hosts['detail'] + '/' + str(game_id), params=payload, timeout=self.timeout).json()

        elif type(game_id) == type(list()) or type(game_id) == type(tuple()):
            self._logger.info('read game data, ids=[%s]' % ', '.join(str(gid) for gid in game_id))
            urls = [self.hosts['detail'] + '/' + str(gid) for gid in game_id]
            rs = (grequests.get(u, timeout=self.timeout, session=self._req_sess, params=payload) for u in urls)
            results = grequests.map(rs, size=10)
            for rep in results:
                yield rep.json()
        else:
            raise TypeError('Invalid Type')


    def get_game_price(self, game_id, country_code='US'):
        if type(game_id) == type(int()) or type(game_id) == type(str()):
            self._logger.info('read game price, ids=[%s]' % str(game_id))
            price_url = self.hosts['price'].replace('{gameid}', str(game_id))
            payload = {'countryCode':country_code}

            price_data = self._req_sess.get(price_url, timeout=self.timeout, params=payload).json()
            yield utility.price_data_parse(game_id, price_data, country_code)

        elif type(game_id) == type(list()) or type(game_id) == type(tuple()):
            price_url = self.hosts['multiprice']
            ids = ','.join(str(gid) for gid in game_id)
            self._logger.info('read game price, ids=[%s]' % ids.replace(',', ', '))
            payload = {'ids':ids, 'countryCode':country_code}
            price_data = self._req_sess.get(price_url, timeout=self.timeout, params=payload).json()['_embedded']['items']

            if len(price_data) == 0:
                for gid in game_id:
                    yield utility.price_data_parse(None, country_code)
            else:
                gid_point = 0
                for gid in game_id:
                    pdata_now = price_data[gid_point]
                    if str(gid) == utility.get_game_id_from_url(pdata_now['_links']['self']['href']):
                        price = utility.price_data_parse(gid, pdata_now, country_code)
                        gid_point += 1
                        yield price
                    else:
                        yield utility.price_data_parse(gid, None, country_code)
        else:
            raise TypeError('Invalid Type')


    def get_game_base_price(self, game_id, country_code='US'):
        self._logger.info('read game base price')
        price_data = self.get_game_price(game_id, country_code)
        for pd in price_data:
            yield pd['basePrice']


    def get_game_final_price(self, game_id, country_code='US'):
        self._logger.info('read game final price')
        price_data = self.get_game_price(game_id, country_code)
        for pd in price_data:
            yield pd['finalPrice']


    def get_game_price_currency(self, game_id, country_code='US'):
        self._logger.info('read game price currency')
        price_data = self.get_game_price(game_id, country_code)
        for pd in price_data:
            yield pd['currency']


    def get_game_discount(self, game_id, country_code='US'):
        self._logger.info('read game discount')
        price_data = self.get_game_price(game_id, country_code)
        for pd in price_data:
            if pd['basePrice'] != None:
                if pd['finalPrice'] == 0:
                    yield {'gameId':pd['gameId'], 'discount':100}
                else:
                    yield {'gameId':pd['gameId'],
                            'discount':int(round(1.0 - pd['finalPrice'] / pd['basePrice'], 2) * 100)}
            else:
                yield {'gameId':pd['gameId'], 'discount':None}


    def get_region_table(self):
        region_host = self.hosts['region']
        region_data = self._req_sess.get(region_host, timeout=self.timeout).json()

        region_table = {}
        for region in region_data:
            region_table[region['code']] = region['name']

        return region_table


    def get_game_global_price(self, game_id, countries):
        price_url = self.hosts['price'].replace('{gameid}', str(game_id))

        self._logger.info('read game global price, ids=[%s]' % str(game_id))

        rs = (grequests.get(price_url, timeout=self.timeout, session=self._req_sess, params={'countryCode':ct}) for ct in countries)
        results = grequests.map(rs, size=10)
        point = 0
        for r in results:
            price_data = r.json()
            price = utility.price_data_parse(utility.get_game_id_from_url(r.url), price_data, countries[point])
            point += 1
            yield price


    def get_multi_game_global_price(self, game_id, countries):
        if type(game_id) != type(list()) and type(game_id) != type(tuple()):
            raise TypeError('Invalid Type')

        ids = ','.join(str(gid) for gid in game_id)
        self._logger.info('read game global price, ids=[%s]' % ids.replace(',', ', '))

        rs = (grequests.get(self.hosts['multiprice'], timeout=self.timeout, session=self._req_sess,
            params={'ids':ids, 'countryCode':country}) for country in countries)
        results = grequests.map(rs, size=10)

        country_point = 0
        for r in results:
            gid_point = 0
            price_data = r.json()['_embedded']['items']
            if len(price_data) == 0:
                for gid in game_id:
                    yield utility.price_data_parse(gid, None, countries[country_point])
            else:
                for gid in game_id:
                    pdata_now = price_data[gid_point]
                    if str(gid) == utility.get_game_id_from_url(pdata_now['_links']['self']['href']):
                        price = utility.price_data_parse(gid, pdata_now, countries[country_point])
                        gid_point += 1
                        yield price
                    else:
                        yield utility.price_data_parse(gid, None, countries[country_point])
            country_point += 1


    def get_game_rating(self, game_id):
        if type(game_id) == type(int()) or type(game_id) == type(str()):
            yield self._req_sess.get(self.hosts['rating'].replace('{gameid}', str(game_id)), timeout=self.timeout).json()['value']
        elif type(game_id) == type(list()) or type(game_id) == type(tuple()):
            urls = [self.hosts['rating'].replace('{gameid}', str(gid)) for gid in game_id]
            rs = (grequests.get(u, timeout=self.timeout, session=self._req_sess) for u in urls)
            results = grequests.map(rs, size=10)
            for r in results:
                yield r.json()['value']


if __name__ == '__main__':
    import time

    logger = logging.getLogger('GOGDB')
    logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s | %(name)s | %(levelname)s | %(message)s')
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    api = API()

    logger.debug('Games on GOG in total: %s' %(api.get_total_num()))

    start = time.time()
    list(api.get_game_price([1,2,3,4,5,6,7,8,9,10]))
    logger.debug('get 10 games price time usage: %f' %(time.time() - start))

    start = time.time()
    list(api.get_game_data([1,2,3,4,5,6,7,8,9,10]))
    logger.debug('get 10 games data time usage: %f' %(time.time() - start))

    start = time.time()
    list(api.get_multi_game_global_price([1,2,3,4,5,6,7,8,9,10], api.get_region_table().keys()))
    logger.debug('get 10 games price in 240 countries time usage: %f' %(time.time() - start))
