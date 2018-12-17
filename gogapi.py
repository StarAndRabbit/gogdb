import requests, json
from requests.adapters import HTTPAdapter
from multiprocessing.dummy import Pool as ThreadPool
import grequests, re

RETRIES = 5
TIMEOUT = 5

class API(object):
    host = 'https://api.gog.com/v2/games'

    @staticmethod
    def get_total_num():
        req_sess = requests.Session()
        req_sess.mount('https://', HTTPAdapter(max_retries=RETRIES))
        fst_page_data = json.loads(req_sess.get(API.host, timeout=TIMEOUT).text)
        limit = fst_page_data['limit']
        pages = fst_page_data['pages']

        lst_page_data = json.loads(req_sess.get(fst_page_data['_links']['last']['href'], timeout=TIMEOUT).text)
        return limit * (pages - 1) + len(lst_page_data['_embedded']['items'])

    @staticmethod
    def get_game_id_in_page(page, limit):
        req_sess = requests.Session()
        req_sess.mount('https://', HTTPAdapter(max_retries=RETRIES))
        games_id = []

        payload = {'page':page, 'limit':limit, 'locale':'en-US'}
        page_data = json.loads(req_sess.get(API.host, params=payload, timeout=TIMEOUT).text)
        items = page_data['_embedded']['items']

        for item in items:
            games_id.append(item['_embedded']['product']['id'])

        return games_id

    '''
    @staticmethod
    def get_all_game_id(threads):
        req_sess = requests.Session()
        req_sess.mount('https://', HTTPAdapter(max_retries=RETRIES))
        pages = json.loads(req_sess.get(API.host, timeout=TIMEOUT).text)['pages']
        pages = range(1, pages)
        games_id = []

        if threads <= 1:
            for page in pages:
                games_id += API.get_game_id_in_page(page, 50)
            return games_id
        else:
            pool = ThreadPool(threads)
            results = pool.map(lambda page: API.get_game_id_in_page(page, 50), pages)
            for result in results:
                games_id += result
            return games_id
    '''

    @staticmethod
    def get_all_game_id():
        req_sess = requests.Session()
        req_sess.mount('https://', HTTPAdapter(max_retries=RETRIES))
        pages = json.loads(req_sess.get(API.host, timeout=TIMEOUT).text)['pages']
        pages = range(1, pages)
        urls = [API.host + '?limit=50&page=' + str(p) for p in pages]
        rs = (grequests.get(u, timeout=TIMEOUT, session=req_sess) for u in urls)
        results = grequests.map(rs)
        games_id = list()
        for rep in results:
            items = rep.json()['_embedded']['items']
            for item in items:
                games_id.append(item['_embedded']['product']['id'])
        return games_id

    @staticmethod
    def get_game_data(game_id):
        req_sess = requests.Session()
        req_sess.mount('https://', HTTPAdapter(max_retries=RETRIES))
        payload = {'locale':'en-US'}
        return json.loads(req_sess.get(API.host + '/' + str(game_id), params=payload, timeout=TIMEOUT).text)

    @staticmethod
    def get_game_price(game_id, country_code='US'):
        game_data = API.get_game_data(game_id)
        price_url = game_data['_embedded']['product']['_links']['prices']['href']
        price_url = price_url.replace('{country}', country_code)
        req_sess = requests.Session()
        req_sess.mount('https://', HTTPAdapter(max_retries=RETRIES))

        price = {}
        price_data = json.loads(req_sess.get(price_url, timeout=TIMEOUT).text)
        if '_embedded' in price_data:
            price_data = price_data['_embedded']['prices'][0]
            price['currency'] = price_data['currency']['code']
            price['basePrice'] = round(int(price_data['basePrice'].split(' ')[0]) * 0.01, 2)
            price['finalPrice'] = round(int(price_data['finalPrice'].split(' ')[0]) * 0.01, 2)
        else:
            price['currency'] = ''
            price['basePrice'] = None
            price['finalPrice'] = None
        price['country'] = country_code
        return price

    @staticmethod
    def get_game_base_price(game_id, country_code='US'):
        price_data = API.get_game_price(game_id, country_code)
        return price_data['basePrice']

    @staticmethod
    def get_game_final_price(game_id, country_code='US'):
        price_data = API.get_game_price(game_id, country_code)
        return price_data['finalPrice']

    @staticmethod
    def get_game_price_currency(game_id, country_code='US'):
        price_data = API.get_game_price(game_id, country_code)
        return price_data['currency']

    @staticmethod
    def get_game_discount(game_id, country_code='US'):
        price_data = API.get_game_price(game_id, country_code)
        return int(round(1.0 - price_data['finalPrice'] / price_data['basePrice'], 2) * 100)

    @staticmethod
    def get_region_table():
        region_host = 'https://countrycode.org/api/countryCode/countryMenu'
        req_sess = requests.Session()
        req_sess.mount('https://', HTTPAdapter(max_retries=RETRIES))
        region_data = json.loads(req_sess.get(region_host, timeout=TIMEOUT).text)

        region_table = {}
        for region in region_data:
            region_table[region['code']] = region['name']

        return region_table

    '''
    @staticmethod
    def get_game_global_price(game_id, threads):
        countries = API.get_region_table().keys()
        if threads <= 1:
            game_prices = []
            for country in countries:
                game_prices.append(API.get_game_price(game_id, country))
            return game_prices
        else:
            pool = ThreadPool(threads)
            game_prices = pool.map(lambda country: API.get_game_price(game_id, country), countries)
            return game_prices
    '''

    @staticmethod
    def get_game_global_price(game_id):
        countries = API.get_region_table().keys()
        host = 'https://api.gog.com/products/' + str(game_id) + '/prices?countryCode={country}'
        urls = [host.replace('{country}', cty) for cty in countries]

        req_sess = requests.Session()
        req_sess.mount('https://', HTTPAdapter(max_retries=RETRIES))
        rs = (grequests.get(u, timeout=TIMEOUT, session=req_sess) for u in urls)
        results = grequests.map(rs)
        prices = list()
        point = 0
        for r in results:
            price = dict()
            price_data = r.json()
            if '_embedded' in price_data:
                price_data = price_data['_embedded']['prices'][0]
                price['currency'] = price_data['currency']['code']
                price['basePrice'] = round(int(price_data['basePrice'].split(' ')[0]) * 0.01, 2)
                price['finalPrice'] = round(int(price_data['finalPrice'].split(' ')[0]) * 0.01, 2)
            else:
                price['currency'] = ''
                price['basePrice'] = None
                price['finalPrice'] = None
            price['country'] = countries[point]
            point += 1
            prices.append(price)
        return prices


    @staticmethod
    def get_game_rating(game_id):
        host = 'https://reviews.gog.com/v1/products/{gameid}/averageRating?reviewer=verified_owner'
        req_sess = requests.Session()
        req_sess.mount('https://', HTTPAdapter(max_retries=RETRIES))
        return req_sess.get(host.replace('{gameid}', str(game_id)), timeout=TIMEOUT).json()['value']

    @staticmethod
    def get_game_id_from_url(url):
        t = re.findall('\d+', url)
        if t:
            return max(t, key=len)
        else:
            return None

if __name__ == '__main__':
    import time
    print("Games on GOG in total: %s" %(API.get_total_num()))

    start = time.time()
    API.get_game_global_price(1)
    print(time.time() - start)
    print(API.get_game_rating(1207665493))
    print(API.get_game_base_price(1207665493))
