from datetime import datetime
from decimal import Decimal
from pony.converting import str2datetime
from pony.orm import *


db = Database()


class GameDetail(db.Entity):
    id = PrimaryKey(int)
    title = Required(str)
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
    averageRating = Optional(Decimal)
    links = Optional('GameLink')
    publishers = Set('Publisher')
    developers = Set('Developer')
    supportedOS = Set('OS')
    features = Set('Feature')
    discount = Set('Discount')
    countries = Set('Country')
    basePrice = Set('BasePrice')
    localizations = Set('Localization')
    image = Optional('Image')
    additionalRequirements = Optional(str)
    requiresGames = Set('GameDetail', reverse='requiredByGames')
    requiredByGames = Set('GameDetail', reverse='requiresGames')
    includesGames = Set('GameDetail', reverse='includedInGames')
    includedInGames = Set('GameDetail', reverse='includesGames')
    screenshots = Set('Screenshot')
    videos = Set('Video')
    editions = Set('GameDetail', reverse='editions')
    changeRecord = Set('ChangeRecord')


class GameLink(db.Entity):
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


class OS(db.Entity):
    name = PrimaryKey(str)
    games = Set(GameDetail)


class Publisher(db.Entity):
    name = PrimaryKey(str)
    games = Set(GameDetail)


class Developer(db.Entity):
    name = PrimaryKey(str)
    games = Set(GameDetail)


class Feature(db.Entity):
    id = PrimaryKey(str, auto=True)
    name = Required(str)
    games = Set(GameDetail)


class Discount(db.Entity):
    game = Required(GameDetail)
    dateTime = Required(datetime)
    discount = Required(Decimal)
    PrimaryKey(game, dateTime)


class Country(db.Entity):
    code = PrimaryKey(str, auto=True)
    name = Required(str)
    games = Set(GameDetail)
    basePrice = Set('BasePrice')


class BasePrice(db.Entity):
    game = Required(GameDetail)
    country = Required(Country)
    price = Required(Decimal)
    currency = Required(str)
    PrimaryKey(game, country)


class Localization(db.Entity):
    code = Required(str)
    type = Required(str)
    name = Required(str)
    game = Set(GameDetail)
    PrimaryKey(code, type)


class Image(db.Entity):
    game = PrimaryKey(GameDetail)
    href = Required(str)
    formatters = Set('Formatter')


class Formatter(db.Entity):
    formatter = PrimaryKey(str)
    images = Set(Image)
    screenshots = Set('Screenshot')


class Screenshot(db.Entity):
    id = Required(int)
    game = Required(GameDetail)
    href = Required(str)
    formatters = Set(Formatter)
    PrimaryKey(id, game)


class Video(db.Entity):
    id = Required(int)
    game = Required(GameDetail)
    videoId = Required(str)
    thumbnailId = Required(str)
    provider = Required('VideoProvider')
    PrimaryKey(id, game)


class VideoProvider(db.Entity):
    provider = PrimaryKey(str, auto=True)
    videoHref = Required(str)
    thumbnailHref = Required(str)
    videos = Set(Video)


class ChangeRecord(db.Entity):
    game = Required(GameDetail)
    dateTime = Required(datetime)
    change = Required(str)
    PrimaryKey(game, dateTime)

