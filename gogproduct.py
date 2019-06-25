from .gogapi import API
from .gogbase import GOGBase
import asyncio
import dateutil.parser


class NetworkError(Exception):
    pass


class Series(GOGBase):

    @property
    def id(self):
        return self.__id

    @property
    def name(self):
        return self.__name

    def __init__(self, series_data):
        self.__id = series_data['id']
        self.__name = series_data['name']


class Links(GOGBase):

    @property
    def store(self):
        return '' if self.__store is None else self.__store

    @property
    def support(self):
        return '' if self.__support is None else self.__support

    @property
    def forum(self):
        return '' if self.__forum is None else self.__forum

    @property
    def iconSquare(self):
        return '' if self.__iconSquare is None else self.__iconSquare

    @property
    def boxArtImage(self):
        return '' if self.__boxArtImage is None else self.__boxArtImage

    @property
    def backgroundImage(self):
        return '' if self.__backgroundImage is None else self.__backgroundImage

    @property
    def icon(self):
        return '' if self.__icon is None else self.__icon

    @property
    def logo(self):
        return '' if self.__logo is None else self.__logo

    @property
    def galaxyBackgroundImage(self):
        return '' if self.__galaxyBackgroundImage is None else self.__galaxyBackgroundImage

    def __init__(self, links_data):
        self.__store = links_data.get('store', {}).get('href', '')
        self.__support = links_data.get('support', {}).get('href', '')
        self.__forum = links_data.get('forum', {}).get('href', '')
        self.__iconSquare = links_data.get('iconSquare', {}).get('href', '')
        self.__boxArtImage = links_data.get('boxArtImage', {}).get('href', '')
        self.__backgroundImage = links_data.get('backgroundImage', {}).get('href', '')
        self.__icon = links_data.get('icon', {}).get('href', '')
        self.__logo = links_data.get('logo', {}).get('href', '')
        self.__galaxyBackgroundImage = links_data.get('galaxyBackgroundImage', {}).get('href', '')


class Images(GOGBase):

    @property
    def href(self):
        return self.__href

    @property
    def formatters(self):
        return self.__formatters

    def __init__(self, image_data):
        self.__href = image_data.get('href', '')
        self.__formatters = image_data.get('formatters', [])

    def template(self):
        return list(map(lambda x: self.__href.replace('{formatter}', x), self.__formatters))


class GOGProduct(GOGBase):

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

    @property
    def image(self):
        return self.__image

    @property
    def links(self):
        return self.__links

    @property
    def series(self):
        return self.__series

    def __init__(self, *args):
        if len(args) == 1 and (isinstance(args[0], int) or isinstance(args[0], str)):
            api = API()
            prod_id = args[0]

            tasks = asyncio.gather(api.get_product_data(prod_id), api.get_extend_detail(prod_id))
            loop = asyncio.get_event_loop()
            try:
                prod_data, prod_ext_data = loop.run_until_complete(tasks)
            except:
                raise NetworkError()

            prod_data = prod_data[0]
            prod_ext_data = prod_ext_data[0]
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
                self.__image = Images(product['_links']['image'])

                self.__productType = embed.get('productType', 'GAME')
                self.__series = None if 'series' not in embed else Series(embed['series'])

                self.__isUsingDosBox = data.get('isUsingDosBox', False)
                self.__inDevelopment = False if isinstance(data.get('inDevelopment', False), bool) \
                    else data['inDevelopment'].get('active', False)
                self.__additionalRequirements = data.get('additionalRequirements', '')
                self.__links = Links(data['_links'])


    def __parse_ext_data(self, data):
        if 'error' in data:
            raise ValueError()
        else:
            self.__slug = data.get('slug', '')
