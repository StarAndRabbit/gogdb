from .gogapi import API
import asyncio
import dateutil


class GOGProduct:

    @property
    def id(self):
        return self.__id

    @property
    def title(self):
        return self.__title

    @property
    def slug(self):
        return self.__slug

    @property
    def inDevelopment(self):
        return self.__inDevelopment

    @property
    def isUsingDosBox(self):
        return self.__isUsingDosBox

    @property
    def isAvailableForSale(self):
        return self.__isAvailableForSale

    @property
    def isVisibleInCatalog(self):
        return self.__isVisibleInCatalog

    @property
    def isPreorder(self):
        return self.__isPreorder

    @property
    def isVisibleInAccount(self):
        return self.__isVisibleInAccount

    @property
    def isInstallable(self):
        return self.__isInstallable

    @property
    def hasProductCard(self):
        return self.__hasProductCard

    @property
    def isSecret(self):
        return self.__isSecret

    @property
    def productType(self):
        return self.__productType

    @property
    def globalReleaseDate(self):
        return dateutil.parser.parse(self.__globalReleaseDate).replace(tzinfo=None)

    @property
    def gogReleaseDate(self):
        return dateutil.parser.parse(self.__gogReleaseDate).replace(tzinfo=None)

    @property
    def additionalRequirements(self):
        return self.__additionalRequirements

    def __init__(self, *args):
        if len(args) == 1 and (isinstance(args[0], int) or isinstance(args[0], str)):
            api = API()
            prod_id = args[0]
            prod_data, prod_ext_data = asyncio.run(
                asyncio.gather(api.get_product_data(prod_id), api.get_extend_detail(prod_id)))
            self.__parse_data(prod_data)
            self.__parse_ext_data(prod_ext_data)
        elif len(args) == 2 and isinstance(args[0], dict) and isinstance(args[1], dict):
            prod_data = args[0]
            prod_ext_data = args[1]
            self.__parse_data(prod_data)
            self.__parse_data(prod_ext_data)
        else:
            raise TypeError()

    def __parse_data(self, data):
        if 'error' in data:
            raise ValueError()
        else:
            if '_embedded' not in data:
                raise ValueError()
            else:
                embed = data['_embedded']
                product = embed['product']

                self.__id = product['id']
                self.__title = product['title']
                self.__isAvailableForSale = product.get('isAvailableForSale', False)
                self.__isVisibleInCatalog = product.get('isVisibleInCatalog', False)
                self.__isPreorder = product.get('isPreorder', False)
                self.__isVisibleInAccount = product.get('isVisibleInAccount', False)
                self.__isInstallable = product.get('isInstallable', False)
                self.__globalReleaseDate = product.get('globalReleaseDate', None)
                self.__hasProductCard = product.get('hasProductCard', False)
                self.__gogReleaseDate = product.get('gogReleaseDate', None)
                self.__isSecret = product.get('isSecret', False)

                self.__productType = embed.get('productType', 'GAME')

                self.__isUsingDosBox = data.get('isUsingDosBox', False)
                self.__inDevelopment = False if isinstance(data.get('inDevelopment', False), bool) \
                    else data['inDevelopment'].get('active', False)
                self.__additionalRequirements = data.get('additionalRequirements', '')

    def __parse_ext_data(self, data):
        if 'error' in data:
            raise ValueError()
        else:
            self.__slug = data.get('slug', '')
