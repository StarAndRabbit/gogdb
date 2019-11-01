from datetime import datetime, timedelta
from decimal import Decimal
from pony.orm import *
from .gogexceptions import NeedPrimaryKey
import logging
from .utilities import func_name
from hashlib import sha256
from .changetemplate import change_templates
import time
import collections


db = Database()


class BaseModel(object):
    oldValueDict = dict()
    hookOperator = ['insert', 'update', 'checkout']

    @classmethod
    def equals(cls, a, b):
        if isinstance(a, core.Entity) and isinstance(b, core.Entity):
            return type(a) == type(b) and a.get_pk() == b.get_pk()
        elif isinstance(a, core.Entity) and not isinstance(b, core.Entity):
            return a.get_pk() == b
        elif not isinstance(a, core.Entity) and isinstance(b, core.Entity):
            return a == b.get_pk()
        elif isinstance(a, list) or isinstance(a, tuple):
            if type(a) != type(b):
                return False
            elif len(a) != len(b):
                return False
            else:
                tmp_a = list(map(lambda x: x.get_pk() if isinstance(x, core.Entity) else x, a))
                tmp_b = list(map(lambda x: x.get_pk() if isinstance(x, core.Entity) else x, b))
                return collections.Counter(tmp_a) == collections.Counter(tmp_b)
        else:
            if a == b:
                return True
            else:
                return False

    @classmethod
    def save_into_db(cls, **kwargs):
        logger = logging.getLogger('GOGDB.DataBase')
        logger.debug(f'Call {cls.__dict__["_table_"]}.{func_name()}')
        start_time = time.time()

        # black magic to get primary key
        pk_objs = cls.__dict__['_pk_attrs_']
        adict = cls.__dict__['_adict_']
        pk_columns = list()
        for pk_obj in pk_objs:
            for key in adict:
                if adict[key] == pk_obj:
                    pk_columns.append(key)
                    break

        if all(item in kwargs.keys() for item in pk_columns) is False:
            logger.error('The primary key is not included in the params')
            raise NeedPrimaryKey('The primary key is not included in the params')

        pk_value = tuple(kwargs[val] for val in pk_columns)
        try:
            obj = cls.__getitem__(pk_value)
        except:
            logger.debug(f'Insert into [{cls.__dict__["_table_"]}]')
            obj = cls(**kwargs)
            obj.after_save('insert')        # hook method
            return obj

        obj_dict = obj.to_dict(exclude=pk_columns, with_collections=True, related_objects=True)
        obj.oldValueDict = dict()

        need_update = dict()
        for col in kwargs.keys():
            if col in pk_columns:
                continue
            else:
                if cls.equals(obj_dict[col], kwargs[col]):
                    continue
                else:
                    obj.oldValueDict[col] = obj_dict[col]
                    need_update[col] = kwargs[col]
        if len(need_update) == 0:
            logger.debug(f'Nothing needs to be done in [{cls.__dict__["_table_"]}]')
            logger.debug(f'call save_into_db time usage: {time.time() - start_time}')
            obj.after_save('checkout')          # hook method
            return obj
        else:
            obj.set(**need_update)
            logger.info(f'Update columns {[key for key in need_update.keys()]} in [{cls.__dict__["_table_"]}]')
            logger.debug(f'call save_into_db time usage: {time.time() - start_time}')
            obj.after_save('update')            # hook method
            return obj

    def update(self, **kwargs):
        logger = logging.getLogger('GOGDB.DataBase')
        logger.debug(f'Call {self.__class__.__dict__["_table_"]}.{func_name()}')

        # black magic to get primary key
        pk_objs = self.__class__.__dict__['_pk_attrs_']
        adict = self.__class__.__dict__['_adict_']
        pk_columns = list()
        for pk_obj in pk_objs:
            for key in adict:
                if adict[key] == pk_obj:
                    pk_columns.append(key)
                    break

        obj_dict = self.to_dict(exclude=pk_columns, with_collections=True, related_objects=True)
        self.oldValueDict = dict()

        need_update = dict()
        for col in kwargs.keys():
            if col in pk_columns:
                continue
            else:
                if self.__class__.equals(obj_dict[col], kwargs[col]):
                    continue
                else:
                    self.oldValueDict[col] = obj_dict[col]
                    need_update[col] = kwargs[col]
        if len(need_update) == 0:
            logger.debug(f'Nothing needs to be done in [{self.__class__.__dict__["_table_"]}]')
            self.after_save('checkout')         # hook method
        else:
            self.set(**need_update)
            logger.debug(
                f'Update columns {[key for key in need_update.keys()]} in [{self.__class__.__dict__["_table_"]}]')
            self.after_save('update')           # hook method

    def after_save(self, op):
        pass


class GameDetail(db.Entity, BaseModel):
    id = PrimaryKey('Game', reverse='detail')
    title = Required(str)
    slug = Required('Slug')
    clientId = Optional(str)
    clientSecret = Optional(str)
    inDevelopment = Required(bool)
    isUsingDosBox = Required(bool)
    isAvailableForSale = Required(bool)
    isVisibleInCatalog = Required(bool)
    isPreorder = Required(bool)
    isVisibleInAccount = Required(bool)
    isInstallable = Required(bool)
    hasProductCard = Required(bool)
    isSecret = Required(bool)
    productType = Required(str)
    globalReleaseDate = Optional(datetime)
    gogReleaseDate = Optional(datetime)
    averageRating = Optional('AverageRating')
    additionalRequirements = Optional(str)
    links = Optional('GameLink')
    publishers = Set('Publisher')
    developers = Set('Developer')
    supportedOS = Set('OS', reverse='games')
    contentSystemCompatibility = Set('OS', reverse='contentSystemCompatibility')
    features = Set('Feature')
    tags = Set('Tag')
    finalpricerecords = Set('FinalPriceRecord')
    price = Set('Price')
    localizations = Set('Localization')
    image = Optional('Image')
    requiresGames = Set('Game', reverse='requiredByGames')
    requiredByGames = Set('Game', reverse='requiresGames')
    includesGames = Set('Game', reverse='includedInGames')
    includedInGames = Set('Game', reverse='includesGames')
    editions = Set('Game', reverse='editions')
    screenshots = Set('Screenshot')
    videos = Set('Video')
    series = Optional('Series')
    downloads = Optional('Download')
    bonuses = Set('Bonus')
    achivevmentsTable = Optional('AchivevmentsTable')
    builds = Set('Build')
    repositorysV1 = Set('RepositoryV1')
    repositoryV2 = Optional('RepositoryV2')

    def after_save(self, op):
        if op not in self.hookOperator:
            return
        else:
            if (op == 'update' or op == 'checkout') and self.id.initialized is True:
                self.id.detailCheckout = datetime.utcnow()


class GameLink(db.Entity, BaseModel):
    game = PrimaryKey(GameDetail)
    store = Optional(str, nullable=True)
    support = Optional(str, nullable=True)
    forum = Optional(str, nullable=True)
    iconSquare = Optional(str, nullable=True)
    boxArtImage = Optional(str, nullable=True)
    backgroundImage = Optional(str, nullable=True)
    icon = Optional(str, nullable=True)
    logo = Optional(str, nullable=True)
    galaxyBackgroundImage = Optional(str, nullable=True)


class OS(db.Entity, BaseModel):
    name = PrimaryKey(str)
    games = Set(GameDetail, reverse='supportedOS')
    contentSystemCompatibility = Set(GameDetail, reverse='contentSystemCompatibility')
    installers = Set('Installer')
    patches = Set('Patche')
    languagePacks = Set('LanguagePack')
    builds = Set('Build')
    supportCommands = Set('SupportCommand')
    depotsV1 = Set('DepotV1')
    repositorysV2 = Set('RepositoryV2')


class Publisher(db.Entity, BaseModel):
    name = PrimaryKey(str)
    games = Set(GameDetail)


class Developer(db.Entity, BaseModel):
    name = PrimaryKey(str)
    games = Set(GameDetail)


class Feature(db.Entity, BaseModel):
    id = PrimaryKey(str, auto=True)
    name = Required(str)
    games = Set(GameDetail)


class FinalPriceRecord(db.Entity, BaseModel):
    """without currency attribute, use USD by default"""
    game = Required(GameDetail)
    country = Required('Country')
    dateTime = Required(datetime)
    finalPrice = Optional(Decimal)
    PrimaryKey(game, country, dateTime)


class Price(db.Entity, BaseModel):
    game = Required(GameDetail)
    country = Required('Country')
    currency = Required(str)
    basePrice = Optional(Decimal)
    finalPrice = Optional(Decimal)
    priority = Required(int, default=0)
    PrimaryKey(game, country, currency)

    def after_save(self, op):
        if op not in self.hookOperator:
            return
        else:
            now = datetime.utcnow()
            if op == 'checkout':
                self.game.id.priceCheckout = now
            elif op == 'insert':
                self.game.id.priceCheckout = now
                self.game.id.priceUpdate = now
                if self.currency == 'USD':
                    FinalPriceRecord(game=self.game, country=self.country, dateTime=now, finalPrice=self.finalPrice)
            elif op == 'update':
                self.game.id.priceCheckout = now
                self.game.id.priceUpdate = now


class Localization(db.Entity, BaseModel):
    language = Required('Language')
    type = Required(str)
    game = Set(GameDetail)
    PrimaryKey(language, type)


class Image(db.Entity, BaseModel):
    game = PrimaryKey(GameDetail)
    href = Required(str)
    formatters = Set('Formatter')


class Formatter(db.Entity, BaseModel):
    formatter = PrimaryKey(str)
    images = Set(Image)
    screenshots = Set('Screenshot')


class Screenshot(db.Entity, BaseModel):
    id = Required(int)
    game = Required(GameDetail)
    href = Required(str)
    formatters = Set(Formatter)
    PrimaryKey(id, game)


class Video(db.Entity, BaseModel):
    id = Required(int)
    game = Required(GameDetail)
    videoId = Required(str)
    thumbnailId = Required(str)
    provider = Required('VideoProvider')
    PrimaryKey(id, game)


class VideoProvider(db.Entity, BaseModel):
    provider = PrimaryKey(str, auto=True)
    videoHref = Required(str)
    thumbnailHref = Required(str)
    videos = Set(Video)


class ChangeRecord(db.Entity, BaseModel):
    changeId = PrimaryKey(str)
    game = Required('Game')
    dateTime = Required(datetime)
    changes = Set('BaseChange')

    @classmethod
    def dispatch_changeid(cls, product):
        now = datetime.utcnow()
        crs = cls.select(
            lambda cr: now.replace(tzinfo=None) < cr.dateTime + timedelta(minutes=30) and cr.game == product).order_by(
            cls.dateTime)
        if len(crs) > 0:
            return list(crs)[0]
        else:
            unix_now = datetime.timestamp(now)
            change_id = sha256(bytes(f'{product.id}{unix_now}', encoding='utf8')).hexdigest()
            return ChangeRecord(changeId=change_id, game=product, dateTime=now)

    def record(self, args, template):
        saved_changes = len(self.changes)
        args = list(map(lambda x: str(x), args))
        flush()
        if exists(fmttmp for fmttmp in FormatTemplate if fmttmp.name == template['name']):
            temp = FormatTemplate[template['name']]
        else:
            temp = FormatTemplate(**template)
        BaseChange(id=saved_changes, changeRecord=self, args=args, template=temp)


class Tag(db.Entity, BaseModel):
    id = PrimaryKey(int)
    name = Required(str)
    games = Set(GameDetail)


class Series(db.Entity, BaseModel):
    id = PrimaryKey(int)
    name = Optional(str)
    games = Set(GameDetail)


class Download(db.Entity, BaseModel):
    game = PrimaryKey(GameDetail)
    installers = Set('Installer')
    bonusContent = Set('BonusContent')
    patches = Set('Patche')
    languagePacks = Set('LanguagePack')


class Installer(db.Entity, BaseModel):
    id = Required(str)
    download = Required(Download)
    name = Required(str)
    language = Required('Language')
    os = Required(OS)
    version = Optional(str)
    totalSize = Optional(int)
    installerFiles = Set('InstallerFile')
    PrimaryKey(id, download)


class Patche(db.Entity, BaseModel):
    id = Required(int)
    download = Required(Download)
    name = Required(str)
    language = Required('Language')
    os = Required(OS)
    version = Optional(str)
    totalSize = Required(int)
    patcheFiles = Set('PatcheFile')
    PrimaryKey(id, download)


class LanguagePack(db.Entity, BaseModel):
    id = Required(str)
    download = Required(Download)
    name = Required(str)
    language = Required('Language')
    os = Required(OS)
    version = Optional(str)
    totalSize = Required(int)
    languagePackFiles = Set('LanguagePackFile')
    PrimaryKey(id, download)


class BonusContent(db.Entity, BaseModel):
    id = Required(int)
    download = Required(Download)
    bonus = Required('Bonus')
    count = Required(int)
    totalSize = Required(int)
    bonusFiles = Set('BonusFile')
    PrimaryKey(id, download)


class Language(db.Entity, BaseModel):
    code = PrimaryKey(str, auto=True)
    name = Optional(str)
    localization = Set(Localization)
    patches = Set(Patche)
    installers = Set(Installer)
    languagePacks = Set(LanguagePack)
    supportCommands = Set('SupportCommand')
    depotsV1 = Set('DepotV1')
    depotsV2 = Set('DepotV2')


class BonusFile(db.Entity, BaseModel):
    id = Required(int)
    bonusContent = Required(BonusContent)
    size = Required(int)
    downlink = Required(str)
    PrimaryKey(id, bonusContent)


class InstallerFile(db.Entity, BaseModel):
    id = Required(str)
    installer = Required(Installer)
    size = Required(int)
    downlink = Required(str)
    PrimaryKey(id, installer)


class BonusType(db.Entity, BaseModel):
    slug = PrimaryKey(str, auto=True)
    type = Required(str)
    bonuses = Set('Bonus')


class Bonus(db.Entity, BaseModel):
    game = Required(GameDetail)
    name = Required(str)
    bonusType = Required(BonusType)
    bonusContent = Optional(BonusContent)
    PrimaryKey(game, name)


class PatcheFile(db.Entity, BaseModel):
    id = Required(str)
    patche = Required(Patche)
    size = Required(int)
    downlink = Required(str)
    PrimaryKey(id, patche)


class LanguagePackFile(db.Entity, BaseModel):
    id = Required(str)
    languagePack = Required(LanguagePack)
    size = Required(int)
    downlink = Required(str)
    PrimaryKey(id, languagePack)


class Slug(db.Entity, BaseModel):
    slug = PrimaryKey(str, auto=True)
    games = Set(GameDetail)


class AchivevmentsTable(db.Entity, BaseModel):
    game = PrimaryKey(GameDetail)
    totalCount = Required(int, default=0)
    mode = Optional(str)
    achievements = Set('Achievement')


class Achievement(db.Entity, BaseModel):
    id = PrimaryKey(str)
    key = Required(str)
    visible = Required(bool)
    name = Required(str)
    description = Optional(str)
    imageUrlUnlocked = Required(str)
    imageUrlLocked = Required(str)
    rarity = Required(Decimal)
    achievementRarityLevel = Required('AchievementRarityLevel')
    achivevmentsTable = Required(AchivevmentsTable)


class AchievementRarityLevel(db.Entity, BaseModel):
    slug = PrimaryKey(str)
    description = Required(str)
    achievements = Set(Achievement)


class BaseChange(db.Entity, BaseModel):
    id = Required(int)
    changeRecord = Required(ChangeRecord)
    args = Required(StrArray)
    template = Required('FormatTemplate')
    PrimaryKey(id, changeRecord)

    def format(self):
        return self.template.formatString.format(*[arg for arg in self.args])


class Build(db.Entity, BaseModel):
    buildId = PrimaryKey(str, auto=True)
    product = Required(GameDetail)
    os = Required(OS)
    branch = Optional(str)
    version = Optional(str)
    tags = Set('BuildTag')
    datePublished = Optional(datetime)
    generation = Required(int)
    legacyBuildId = Optional(int)
    isDefault = Required(bool)  # Is the lastest version in this game
    repositoryV1 = Optional('RepositoryV1')
    repositoryV2 = Optional('RepositoryV2')


class BuildTag(db.Entity, BaseModel):
    id = PrimaryKey(str, auto=True)
    build = Required(Build)
    repositorysV2 = Set('RepositoryV2')


class RepositoryV1(db.Entity, BaseModel):
    """if build generation=1, use this repository"""
    build = PrimaryKey(Build)
    rootGame = Required(GameDetail)
    products = Set('RepositoryProductV1')
    timestamp = Optional(int)
    installDirectory = Optional(str)
    projectName = Optional(str)
    supportCommands = Set('SupportCommand')
    redistributables = Set('Redistributable')
    depots = Set('DepotV1')


class RepositoryV2(db.Entity, BaseModel):
    """if build generation=2, use this repository"""
    build = PrimaryKey(Build)
    baseProduct = Required(GameDetail)
    clientId = Optional(str)
    clientSecret = Optional(str)
    installDirectory = Optional(str)
    platform = Required(OS)
    tags = Set(BuildTag)
    products = Set('RepositoryProductV2')
    depots = Set('DepotV2')
    dependencies = Set('Dependency')
    cloudSaves = Set('CloudSave')


class RepositoryProductV1(db.Entity, BaseModel):
    game = PrimaryKey('Game')
    standalone = Optional(bool)
    dependencies = Set('RepositoryProductDependency')
    repositoryV1 = Set(RepositoryV1)
    supportCommand = Optional('SupportCommand')
    depotsV1 = Set('DepotV1')


class RepositoryProductDependency(db.Entity, BaseModel):
    id = PrimaryKey(int, auto=True)
    name = Required(str)
    repositoryProduct = Required(RepositoryProductV1)


class SupportCommand(db.Entity, BaseModel):
    id = PrimaryKey(int, auto=True)
    product = Required(RepositoryProductV1)
    languages = Set(Language)
    argument = Optional(str)
    systems = Set(OS)
    executable = Optional(str)
    repositoryV1 = Required(RepositoryV1)


class Redistributable(db.Entity, BaseModel):
    redist = PrimaryKey(str, auto=True)
    executable = Optional(str)
    argument = Optional(str)
    repositorysV1 = Set(RepositoryV1)


class DepotV1(db.Entity, BaseModel):
    manifest = PrimaryKey(str)
    languages = Set(Language)
    systems = Set(OS)
    products = Set(RepositoryProductV1)
    size = Required(str)
    repositoryV1 = Required(RepositoryV1)


class RepositoryProductV2(db.Entity, BaseModel):
    id = PrimaryKey(int, auto=True)
    product = Required('Game')
    script = Optional(str)
    tempArguments = Optional(str)
    tempExecutable = Optional(str)
    repositorysV2 = Set(RepositoryV2)


class DepotV2(db.Entity, BaseModel):
    manifest = PrimaryKey(str)
    compressedSize = Required(int)
    languages = Set(Language)
    productId = Required(str)
    size = Required(int)
    isOffline = Required(bool)
    repositoryV2 = Required(RepositoryV2)


class Dependency(db.Entity, BaseModel):
    name = PrimaryKey(str, auto=True)
    repositorysV2 = Set(RepositoryV2)


class CloudSave(db.Entity, BaseModel):
    location = Required(str)
    name = Required(str)
    repositorysV2 = Set(RepositoryV2)
    PrimaryKey(location, name)


class Game(db.Entity, BaseModel):
    id = PrimaryKey(int)
    detail = Optional(GameDetail, reverse='id')
    initialized = Required(bool, default=False)
    invisible = Required(bool, default=False)
    detailCheckout = Optional(datetime)
    detailUpdate = Optional(datetime)
    priceCheckout = Optional(datetime)
    priceUpdate = Optional(datetime)
    finalPriceCheckout = Optional(datetime)
    finalPriceUpdate = Optional(datetime)
    buildsCheckout = Optional(datetime)
    buildsUpdate = Optional(datetime)
    changeRecords = Set(ChangeRecord)
    requiredByGames = Set(GameDetail, reverse='requiresGames')
    requiresGames = Set(GameDetail, reverse='requiredByGames')
    includedInGames = Set(GameDetail, reverse='includesGames')
    includesGames = Set(GameDetail, reverse='includedInGames')
    editions = Set(GameDetail, reverse='editions')
    repositoryProductV1 = Optional(RepositoryProductV1)
    repositoryProductV2 = Optional(RepositoryProductV2)

    def after_save(self, op):
        if op not in self.hookOperator:
            return
        else:
            change_id = ChangeRecord.dispatch_changeid(self)
            if op == 'insert':
                args = [str(self.id)]
                change_id.record(args, change_templates.prod_add)
            elif op == 'update':
                for key in self.oldValueDict.keys():
                    args = [str(self.id)]
                    if key == 'initialized' and self.oldValueDict[key] is False:
                        change_id.record(args, change_templates.prod_init)
                    elif key == 'invisible' and self.oldValueDict[key] is False:
                        change_id.record(args, change_templates.prod_invs)


class Country(db.Entity, BaseModel):
    code = PrimaryKey(str, auto=True)
    name = Required(str)
    priority = Required(int, default=0, unsigned=True)
    finalPriceRecord = Set(FinalPriceRecord)
    price = Set(Price)


class FormatTemplate(db.Entity, BaseModel):
    name = PrimaryKey(str)
    type = Required(str)
    argsName = Required(StrArray)  # editor not support StrArray now, use str instead
    formatString = Required(str)
    baseChanges = Set(BaseChange)


class AverageRating(db.Entity, BaseModel):
    game = PrimaryKey(GameDetail)
    rating = Required(Decimal)
    count = Required(int)
