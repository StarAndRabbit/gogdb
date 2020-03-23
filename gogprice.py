from .gogapi import gogapi
from .gogbase import GOGBase, GOGNeedNetworkMetaClass
from . import dbmodel as DB
from datetime import datetime
from pony.orm import db_session


class Country(GOGBase):
    def __init__(self, country_data):
        self.__code = country_data['code']
        self.__name = country_data['name']
        self.__priority = 0

    @property
    def code(self):
        return self.__code

    @property
    def name(self):
        return self.__name

    @property
    def priority(self):
        return self.__priority

    def save_or_update(self):
        try:
            return DB.Country[self.code]
        except:
            return DB.Country(code=self.code, name=self.name, priority=self.priority)


class Countries(GOGBase, GOGNeedNetworkMetaClass):
    def __init__(self, countries_data):
        self.__countries = list()
        for country_data in countries_data:
            self.__countries.append(Country(country_data))

    @classmethod
    async def create(cls):
        countries_data = await gogapi.get_countries()
        return Countries(countries_data)

    @classmethod
    async def create_multi(cls, *args):
        pass

    @property
    def countries(self):
        return self.__countries

    def save_or_update(self):
        return list(map(lambda x: x.save_or_update(), self.countries))


class SignalPrice(GOGBase):

    @property
    def game(self):
        return self.__prod_id

    @property
    def country(self):
        return self.__country_code

    @property
    def currency(self):
        return self.__currency

    @property
    def basePrice(self):
        return self.__basePrice

    @property
    def finalPrice(self):
        return self.__finalPrice

    @property
    def priority(self):
        return self.__priority

    def __init__(self, prod_id, country, currency, basePrice, finalPrice, priority):
        self.__prod_id = prod_id
        self.__country_code = country
        self.__currency = currency
        self.__basePrice = basePrice
        self.__finalPrice = finalPrice
        self.__priority = priority

    def save_or_update(self):
        return DB.Price.save_into_db(**self.to_dict())


class GOGPrice(GOGBase, GOGNeedNetworkMetaClass):

    def __init__(self, price_data):
        self.__prod_id = price_data['product']
        self.__prices = []

        price_data = price_data['prices']

        for country in price_data:
            for data in price_data[country]:
                self.__prices.append(SignalPrice(str(self.__prod_id),
                                                 country,
                                                 data['currency'],
                                                 data['basePrice'],
                                                 data['finalPrice'],
                                                 0 if data['isDefault'] else 1))

    @classmethod
    async def create(cls, prod_id: str, countries: list):
        prod_id = [str(prod_id)]
        price_data = await gogapi.get_price_in_countries(prod_id, countries)
        GOGPrice.__deal_non_price_prod(prod_id, price_data)
        return GOGPrice(price_data[0])

    @classmethod
    async def create_multi(cls, prod_ids: list, countries: list):
        price_datas = await gogapi.get_price_in_countries(prod_ids, countries)
        objects = list()
        GOGPrice.__deal_non_price_prod(prod_ids, price_datas)
        for data in price_datas:
            objects.append(GOGPrice(data))
        return objects

    @staticmethod
    def __deal_non_price_prod(ids, price_datas):
        ids_in_result = list()
        for price_data in price_datas:
            ids_in_result.append(price_data['product'])
        ids_in_result = list(map(lambda x: str(x), ids_in_result))
        ids = list(map(lambda x: str(x), ids))
        non_price_prods = list(set(ids).difference(set(ids_in_result)))

        with db_session:
            for non_price in non_price_prods:
                now = datetime.utcnow()
                DB.Game[non_price].priceCheckout = now
                DB.Game[non_price].finalPriceCheckout = now

    @property
    def product_id(self):
        return self.__prod_id

    @property
    def prices(self):
        return self.__prices

    def save_or_update(self):
        return list(map(lambda x: x.save_or_update(), self.prices))
