from .gogapi import gogapi
from .gogbase import GOGBase, GOGNeedNetworkMetaClass


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
        return GOGPrice(price_data[0])

    @classmethod
    async def create_multi(cls, prod_ids: list, countries: list):
        price_datas = await gogapi.get_price_in_countries(prod_ids, countries)
        objects = list()
        for data in price_datas:
            objects.append(GOGPrice(data))
        return objects

    @property
    def product_id(self):
        return self.__prod_id

    @property
    def prices(self):
        return self.__prices
