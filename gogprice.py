from .gogapi import API
from .gogbase import GOGBase
import asyncio

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

class GOGPrice(GOGBase):

    def __init__(self, *args):
        if len(args) != 2:
            raise RuntimeError("Args number Error!!!")
        elif isinstance(args[1], dict):
            price_data = args[1][str(args[0])]
        else:
            api = API()
            price_data = asyncio.run(api.get_product_prices(args[0], args[1]))
            price_data = price_data[str(args[0])]

        self.__prod_id = args[0]
        self.__prices = []

        bprice_data = price_data['basePrice']
        fprice_data = price_data['finalPrice']

        for country in bprice_data:
            for currency in bprice_data[country]:
                if currency is not 'defaultCurrency':
                    bprice = bprice_data[country][currency]
                    fprice = fprice_data[country][currency]
                    priority = 0 if bprice_data[country]['defaultCurrency'] == currency else 1
                    self.__prices.append(SignalPrice(str(self.__prod_id), country, currency, bprice, fprice, priority))

    @property
    def product_id(self):
        return self.__prod_id

    @property
    def prices(self):
        return self.__prices

def create_multi_product_prices(ids, countries):
    if not isinstance(ids, list) and not isinstance(ids, tuple):
        raise TypeError()
    else:
        api = API()
        prod_prices_data = asyncio.run(api.get_product_prices(ids, countries))
        return list(map(lambda x: GOGPrice(x, prod_prices_data), ids))
