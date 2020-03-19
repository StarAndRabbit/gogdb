from .gogapi import gogapi
from .gogbase import *
import asyncio
import dateutil.parser
from .utilities import get_id_from_url, CoroutinePool
from . import dbmodel as DB
from pony import orm
from datetime import datetime


class Rating(GOGBase):

    @property
    def rating(self):
        return self.__rating

    @property
    def count(self):
        return self.__count

    def __init__(self, rating_data):
        self.__rating = rating_data['value']
        self.__count = rating_data['count']

    def save_or_update(self, game):
        dict_data = self.to_dict()
        dict_data['game'] = game
        return DB.AverageRating.save_into_db(**dict_data)


class Publisher(GOGSimpleClass):
    def save_or_update(self):
        return DB.Publisher.save_into_db(**self.to_dict())


class Developer(GOGSimpleClass):
    def save_or_update(self):
        return DB.Developer.save_into_db(**self.to_dict())


class OS(GOGSimpleClass):
    def save_or_update(self):
        try:
            return DB.OS[self.name]
        except:
            return DB.OS(name=self.name)


class Feature(GOGSimpleClass):

    @property
    def id(self):
        return self.__id

    def __init__(self, feature_data):
        self.__id = feature_data['id'].strip()
        super().__init__(feature_data)

    def save_or_update(self):
        return DB.Feature.save_into_db(**self.to_dict())


class Tag(GOGSimpleClass):

    @property
    def id(self):
        return self.__id

    def __init__(self, tag_data):
        self.__id = tag_data['id']
        super().__init__(tag_data)

    def save_or_update(self):
        return DB.Tag.save_into_db(**self.to_dict())


class Language(GOGSimpleClass):

    @property
    def code(self):
        return self.__code

    def __init__(self, language_data):
        self.__code = language_data['code'].strip()
        super().__init__(language_data)

    def save_or_update(self):
        return DB.Language.save_into_db(**self.to_dict())


class Localization(GOGBase):

    @property
    def language(self):
        return self.__language

    @property
    def type(self):
        return self.__type

    def __init__(self, local_data):
        self.__language = Language(local_data['language'])
        self.__type = local_data['localizationScope']['type']

    def save_or_update(self):
        self.language.save_or_update()
        dict_data = self.to_dict()
        dict_data['language'] = self.language.to_dict()['code']
        return DB.Localization.save_into_db(**dict_data)


class Series(GOGSimpleClass):

    @property
    def id(self):
        return self.__id

    def __init__(self, series_data):
        self.__id = series_data['id']
        super().__init__(series_data)

    def save_or_update(self):
        return DB.Series.save_into_db(**self.to_dict())


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

    def save_or_update(self, game):
        dict_data = self.to_dict()
        dict_data['game'] = game
        return DB.GameLink.save_into_db(**dict_data)


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

    def save_or_update(self, game):
        def fmter_obj(fmter):
            try:
                return DB.Formatter[fmter]
            except:
                return DB.Formatter(formatter=fmter)
        fmts = list(map(fmter_obj, self.formatters))
        dict_data = self.to_dict()
        dict_data['formatters'] = fmts
        dict_data['game'] = game
        return DB.Image.save_into_db(**dict_data)


class Screenshot(Images):

    @property
    def id(self):
        return self.__id

    def __init__(self, index, screenshot_data):
        sc_data = screenshot_data['_links']['self']
        self.__id = index
        super().__init__(sc_data)

    def save_or_update(self, game):
        def fmter_obj(fmter):
            try:
                return DB.Formatter[fmter]
            except:
                return DB.Formatter(formatter=fmter)
        fmts = list(map(fmter_obj, self.formatters))
        dict_data = self.to_dict()
        dict_data['formatters'] = fmts
        dict_data['game'] = game
        obj = DB.Screenshot.save_into_db(**dict_data)
        return obj


class VideoProvider(GOGBase):

    @property
    def provider(self):
        return self.__provider

    @property
    def videoHref(self):
        return self.__videoHref

    @property
    def thumbnailHref(self):
        return self.__thumbnailHref

    def __init__(self, video_data):
        self.__provider = video_data['provider']
        links = video_data['_links']
        self.__videoHref = links['self']['href'].replace(video_data['videoId'], '{videoId}')
        self.__thumbnailHref = links['thumbnail']['href'].replace(video_data['thumbnailId'], '{thumbnailId}')

    def save_or_update(self):
        try:
            return DB.VideoProvider[self.provider]
        except:
            return DB.VideoProvider(**self.to_dict())


class Video(GOGBase):
    @property
    def id(self):
        return self.__id

    @property
    def provider(self):
        return self.__provider

    @property
    def videoId(self):
        return self.__videoId

    @property
    def thumbnailId(self):
        return self.__thumbnailId

    def __init__(self, index, video_data):
        self.__id = index
        self.__provider = VideoProvider(video_data)
        self.__videoId = video_data['videoId']
        self.__thumbnailId = video_data['thumbnailId']

    def save_or_update(self, game):
        provider = self.provider.save_or_update()
        dict_data = self.to_dict()
        dict_data['game'] = game
        dict_data['provider'] = provider
        return DB.Video.save_into_db(**dict_data)


class BonusType(GOGBase):

    @property
    def slug(self):
        return self.__slug

    @property
    def type(self):
        return self.__type

    def __init__(self, bonustype_data):
        self.__slug = bonustype_data['slug'].strip()
        self.__type = bonustype_data['name'].strip()

    def save_or_update(self):
        try:
            return DB.BonusType[self.slug]
        except:
            return DB.BonusType(slug=self.slug, type=self.type)


class Bonus(GOGSimpleClass):

    @property
    def type(self):
        return self.__type

    def __init__(self, bonus_data):
        self.__type = BonusType(bonus_data['type'])
        super().__init__(bonus_data)

    def save_or_update(self, game):
        bonus_type = self.type.save_or_update()
        dict_data = self.to_dict()
        dict_data['game'] = game
        del dict_data['type']
        dict_data['bonusType'] = bonus_type
        return DB.Bonus.save_into_db(**dict_data)


class Installer(GOGDownloadable):

    @property
    def name(self):
        return self.__name

    @property
    def language(self):
        """
        index of language table
        :return: language table index code
        """
        return self.__language

    @property
    def os(self):
        """
        index of OS table
        :return: OS table index
        """
        if self.__os == 'mac':
            return 'osx'
        else:
            return self.__os

    @property
    def version(self):
        return self.__version

    def __init__(self, product_slug, installer_data):
        self.__name = installer_data['name'].strip()
        self.__language = installer_data['language']
        self.__os = installer_data['os']
        self.__version = '' if installer_data['version'] is None else installer_data['version'].strip()
        super().__init__(product_slug, installer_data)

    def get_os_obj(self):
        try:
            return DB.OS[self.os]
        except:
            return DB.OS(name=self.os)

    def get_lan_obj(self):
        try:
            return DB.Language[self.language]
        except:
            return DB.Language(code=self.language)

    def save_or_update(self, game):
        dict_data = self.to_dict(with_collections=False)
        dict_data['download'] = GOGDownloadable.get_downloadable_table(game)
        dict_data['os'] = self.get_os_obj()
        dict_data['language'] = self.get_lan_obj()
        installer_obj = DB.Installer.save_into_db(**dict_data)
        orm.flush()
        for file in self.files:
            file_dict_data = file.to_dict()
            file_dict_data['installer'] = installer_obj
            DB.InstallerFile.save_into_db(**file_dict_data)
        return installer_obj


class BonusContent(GOGDownloadable):

    @property
    def count(self):
        return self.__count

    def __init__(self, product_slug, bonus_data):
        self.__bonus = bonus_data['name'].strip()
        self.__count = bonus_data['count']
        super().__init__(product_slug, bonus_data)

    def save_or_update(self, game):
        dict_data = self.to_dict(with_collections=False)
        dict_data['download'] = GOGDownloadable.get_downloadable_table(game)
        bonuscont_obj = DB.BonusContent.save_into_db(**dict_data)
        orm.flush()
        for file in self.files:
            file_dict_data = file.to_dict()
            file_dict_data['bonusContent'] = bonuscont_obj
            DB.BonusFile.save_into_db(**file_dict_data)
        return bonuscont_obj


class LanguagePack(Installer):
    def save_or_update(self, game):
        dict_data = self.to_dict(with_collections=False)
        dict_data['download'] = GOGDownloadable.get_downloadable_table(game)
        dict_data['os'] = self.get_os_obj()
        dict_data['language'] = self.get_lan_obj()
        lanpack_obj = DB.LanguagePack.save_into_db(**dict_data)
        orm.flush()
        for file in self.files:
            file_dict_data = file.to_dict()
            file_dict_data['languagePack'] = lanpack_obj
            DB.LanguagePackFile.save_into_db(**file_dict_data)
        return lanpack_obj


class Patche(Installer):
    def save_or_update(self, game):
        dict_data = self.to_dict(with_collections=False)
        dict_data['download'] = GOGDownloadable.get_downloadable_table(game)
        dict_data['os'] = self.get_os_obj()
        dict_data['language'] = self.get_lan_obj()
        patch_obj = DB.Patche.save_into_db(**dict_data)
        orm.flush()
        for file in self.files:
            file_dict_data = file.to_dict()
            file_dict_data['patche'] = patch_obj
            DB.PatcheFile.save_into_db(**file_dict_data)
        return patch_obj


class GOGProduct(GOGBase, GOGNeedNetworkMetaClass):

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
        return dateutil.parser.parse(self.__globalReleaseDate).replace(tzinfo=None) \
            if self.__globalReleaseDate is not None else None

    @property
    def gogReleaseDate(self):
        return dateutil.parser.parse(self.__gogReleaseDate).replace(tzinfo=None) \
            if self.__gogReleaseDate is not None else None

    @property
    def averageRating(self):
        return self.__averageRating

    @property
    def additionalRequirements(self):
        return self.__additionalRequirements

    @property
    def publishers(self):
        return self.__publishers

    @property
    def developers(self):
        return self.__developers

    @property
    def supportedOS(self):
        return self.__supportedOS

    @property
    def contentSystemCompatibility(self):
        return self.__content_system_compatibility

    @property
    def features(self):
        return self.__features

    @property
    def tags(self):
        return self.__tags

    @property
    def localizations(self):
        return self.__localizations

    @property
    def image(self):
        return self.__image

    @property
    def requiresGames(self):
        return self.__requiresGames

    @property
    def requiredByGames(self):
        return self.__requiredByGames

    @property
    def includesGames(self):
        return self.__includesGames

    @property
    def includedInGames(self):
        return self.__includedInGames

    @property
    def screenshots(self):
        return self.__screenshots

    @property
    def videos(self):
        return self.__videos

    @property
    def editions(self):
        return self.__editions

    @property
    def links(self):
        return self.__links

    @property
    def series(self):
        return self.__series

    @property
    def bonuses(self):
        return self.__bonuses

    @property
    def downloads(self):
        return {
            "installers": self.__installers,
            "bonusContent": self.__bonusContent,
            "patches": self.__patches,
            "languagePacks": self.__languagePacks
        }

    def __init__(self, *args):
        if len(args) == 3 and isinstance(args[0], dict) and isinstance(args[1], dict) and isinstance(args[2], dict):
            prod_data = args[0]
            prod_ext_data = args[1]
            prod_rating_data = args[2]
            self.__parse_data(prod_data)
            self.__parse_ext_data(prod_ext_data)
            self.__parse_rating_data(prod_rating_data)
        else:
            raise TypeError()

    @classmethod
    async def create(cls, prod_id):
        prod_data, prod_ext_data, prod_rating_data = await asyncio.gather(gogapi.get_product_data(prod_id),
                                                                          gogapi.get_extend_detail(prod_id),
                                                                          gogapi.get_rating(prod_id),
                                                                          return_exceptions=True)

        try:
            cls.try_exception(prod_data, prod_ext_data, prod_rating_data)
        except Exception:
            raise

        return GOGProduct(prod_data, prod_ext_data, prod_rating_data)

    @classmethod
    async def create_multi(cls, prod_ids: list):
        coro_pool = CoroutinePool(coro_list=[GOGProduct.create(prod_id) for prod_id in prod_ids])
        return await coro_pool.run_all(return_exceptions=True)

    def __parse_data(self, data):
        if '_embedded' not in data:
            raise ValueError()
        else:
            embed = data['_embedded']
            product = embed['product']

            # product segment
            self.__id = product['id']
            self.__title = product['title'].strip()
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

            # embedded segment
            self.__productType = embed.get('productType', 'GAME')
            self.__series = None if 'series' not in embed or embed['series'] is None else Series(embed['series'])
            self.__publishers = [Publisher(embed.get('publisher'))]
            self.__developers = list(map(lambda x: Developer(x), embed.get('developers', [])))
            self.__supportedOS = list(
                map(lambda x: OS(x['operatingSystem']), embed.get('supportedOperatingSystems', [])))
            self.__features = list(map(lambda x: Feature(x), embed.get('features', [])))
            self.__tags = list(map(lambda x: Tag(x), embed.get('tags', [])))
            self.__localizations = list(map(lambda x: Localization(x['_embedded']), embed.get('localizations', [])))

            def gen_sc(tup_data):
                i, x = tup_data
                return Screenshot(i, x)
            self.__screenshots = list(map(gen_sc, enumerate(embed.get('screenshots', []))))

            def gen_vid(tup_data):
                i, x = tup_data
                return Video(i, x)
            self.__videos = list(map(gen_vid, enumerate(embed.get('videos', []))))
            self.__editions = list(map(lambda x: str(x['id']), embed.get('editions', [])))
            self.__bonuses = list(map(lambda x: Bonus(x), embed.get('bonuses', [])))

            # data segment
            self.__isUsingDosBox = data.get('isUsingDosBox', False)
            self.__inDevelopment = False if isinstance(data.get('inDevelopment', False), bool) \
                else data['inDevelopment'].get('active', False)
            self.__additionalRequirements = data.get('additionalRequirements', '').strip()
            self.__links = Links(data['_links'])
            self.__requiresGames = list(
                map(lambda x: get_id_from_url(x['href']), data['_links'].get('requiresGames', [])))
            self.__requiredByGames = list(
                map(lambda x: get_id_from_url(x['href']), data['_links'].get('isRequiredByGames', [])))
            self.__includesGames = list(
                map(lambda x: get_id_from_url(x['href']), data['_links'].get('includesGames', [])))
            self.__includedInGames = list(
                map(lambda x: get_id_from_url(x['href']), data['_links'].get('isIncludedInGames', [])))

    def __parse_ext_data(self, data):
        self.__slug = data.get('slug', '').strip()

        content_system_compatibility = list()
        for os in data['content_system_compatibility'].keys():
            if data['content_system_compatibility'][os]:
                content_system_compatibility.append({'name': os})
        self.__content_system_compatibility = list(map(lambda x: OS(x), content_system_compatibility))

        downloads = data.get('downloads', {})
        self.__installers = list(map(lambda x: Installer(self.slug, x), downloads.get('installers', [])))
        self.__bonusContent = list(map(lambda x: BonusContent(self.slug, x), downloads.get('bonus_content', [])))
        self.__patches = list(map(lambda x: Patche(self.slug, x), downloads.get('patches', [])))
        self.__languagePacks = list(map(lambda x: LanguagePack(self.slug, x), downloads.get('language_packs', [])))

    def __parse_rating_data(self, data):
        self.__averageRating = Rating(data)

    def __before_save_or_update(self):
        dict_data = dict()
        dict_data['publishers'] = list(map(lambda x: x.save_or_update(), self.publishers))
        dict_data['developers'] = list(map(lambda x: x.save_or_update(), self.developers))
        dict_data['features'] = list(map(lambda x: x.save_or_update(), self.features))
        dict_data['tags'] = list(map(lambda x: x.save_or_update(), self.tags))
        dict_data['supportedOS'] = list(map(lambda x: x.save_or_update(), self.supportedOS))
        dict_data['contentSystemCompatibility'] = list(map(lambda x: x.save_or_update(),
                                                           self.contentSystemCompatibility))
        dict_data['localizations'] = list(map(lambda x: x.save_or_update(), self.localizations))
        dict_data['series'] = None if self.series is None else self.series.save_or_update()

        return dict_data

    def __after_save_or_update(self):
        self.averageRating.save_or_update(self.id)
        self.links.save_or_update(self.id)
        if self.image is not None and self.image.href is not None:
            self.image.save_or_update(self.id)

        list(map(lambda y: list(map(lambda x: x.save_or_update(self.id), y)), [
            self.screenshots,
            self.videos,
            self.bonuses,
            self.downloads['installers'],
            self.downloads['bonusContent'],
            self.downloads['languagePacks'],
            self.downloads['patches']
        ]))

    def save_or_update(self):
        extra_data = self.__before_save_or_update()
        extra_data['id'] = self.id
        dict_data = self.to_dict(with_collections=False)
        try:
            dict_data['slug'] = DB.Slug[self.slug]
        except:
            dict_data['slug'] = DB.Slug(slug=self.slug)

        DB.GameDetail.save_into_db(**dict_data)
        DB.GameDetail.save_into_db(**extra_data)

        self.__after_save_or_update()

        editions = list(map(lambda x: DB.Game.save_into_db(**{'id':x}), self.editions))
        req_games = list(map(lambda x: DB.Game.save_into_db(**{'id':x}), self.requiresGames))
        req_by_games = list(map(lambda x: DB.Game.save_into_db(**{'id':x}), self.requiredByGames))
        inc_games = list(map(lambda x: DB.Game.save_into_db(**{'id':x}), self.includesGames))
        inc_in_games = list(map(lambda x: DB.Game.save_into_db(**{'id':x}), self.includedInGames))
        DB.GameDetail.save_into_db(**{
            'id': self.id,
            'editions': editions,
            'requiresGames': req_games,
            'requiredByGames': req_by_games,
            'includesGames': inc_games,
            'includedInGames': inc_in_games
        })

        # setup Game table
        if DB.Game[self.id].initialized is False:
            now = datetime.utcnow()
            DB.Game.save_into_db(**{
                'id': self.id,
                'initialized': True,
                'detailCheckout': now,
                'detailUpdate': now})
