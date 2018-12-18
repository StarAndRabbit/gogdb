from gogapi import API
from dbmodel import *
import dateutil.parser, re
from datetime import datetime

@db_session
def region_parse():
    region_table = API.get_region_table()
    for code in region_table:
        if not select(region for region in Country if region.code == code).exists():
            Country(code=code, name=region_table[code])


@db_session
def link_parse(game_detail, link_data):
    if game_detail.links:
        link = game_detail.links

        if link.store != link_data['store']['href']:
            link.store = link_data['store']['href']

        if link.support != link_data['support']['href']:
            link.support = link_data['support']['href']

        if link.forum != link_data['forum']['href']:
            link.support = link_data['forum']['href']

        if link.iconSquare != link_data['iconSquare']['href']:
            link.iconSquare = link_data['iconSquare']['href']

        if link.boxArtImage != link_data['boxArtImage']['href']:
            link.boxArtImage = link_data['boxArtImage']['href']

        if link.backgroundImage != link_data['backgroundImage']['href']:
            link.backgroundImage = link_data['backgroundImage']['href']

        if 'icon' in link_data:
            if link.icon != link_data['icon']['href']:
                link.icon = link_data['icon']['href']

        if 'logo' in link_data:
            if link.logo != link_data['logo']['href']:
                link.logo = link_data['logo']['href']

        if 'galaxyBackgroundImage' in link_data:
            if link.galaxyBackgroundImage != link_data['galaxyBackgroundImage']['href']:
                link.galaxyBackgroundImage = link_data['galaxyBackgroundImage']['href']

    else:
        link = GameLink(
                game = game_detail,
                store = link_data['store']['href'],
                support = link_data['support']['href'],
                forum = link_data['forum']['href'],
                iconSquare = link_data['iconSquare']['href'],
                boxArtImage = link_data['boxArtImage']['href'],
                backgroundImage = link_data['backgroundImage']['href'])

        if 'icon' in link_data:
            link.icon = link_data['icon']['href']

        if 'logo' in link_data:
            link.logo = link_data['logo']['href']

        if 'galaxyBackgroundImage' in link_data:
            link.galaxyBackgroundImage = link_data['galaxyBackgroundImage']['href']

    return link


@db_session
def publisher_parse(puber_data):
    if select(puber for puber in Publisher if puber.name == puber_data['name'].strip()).exists():
        return select(puber for puber in Publisher if puber.name == puber_data['name'].strip())[:][0]
    else:
        return Publisher(name = puber_data['name'].strip())


@db_session
def developer_parse(dever_data):
    devers = list()
    for dever in dever_data:
        if select(dev for dev in Developer if dev.name == dever['name'].strip()).exists():
            devers.append(select(dev for dev in Developer if dev.name == dever['name'].strip())[:][0])
        else:
            devers.append(Developer(name = dever['name'].strip()))

    return devers


@db_session
def os_parse(os_data):
    oss = list()
    for os in os_data:
        if select(sys for sys in OS if sys.name == os['operatingSystem']['name']).exists():
            oss.append(select(sys for sys in OS if sys.name == os['operatingSystem']['name'])[:][0])
        else:
            oss.append(OS(name = os['operatingSystem']['name']))

    return oss


@db_session
def feature_parse(feature_data):
    features = list()
    for feature in feature_data:
        if select(fe for fe in Feature if fe.id == feature['id']).exists():
            features.append(select(fe for fe in Feature if fe.id == feature['id'])[:][0])
        else:
            features.append(Feature(id = feature['id'], name = feature['name']))

    return features


@db_session
def tag_parse(tag_data):
    tags = list()
    for tag in tag_data:
        if select(tg for tg in Tag if tg.id == tag['id']).exists():
            tags.append(select(tg for tg in Tag if tg.id == tag['id'])[:][0])
        else:
            tags.append(Tag(id = tag['id'], name = tag['name']))

    return tags


@db_session
def localization_parse(loc_data):
    locs = list()
    for loc in loc_data:
        if select(lc for lc in Localization if lc.code == loc['_embedded']['language']['code']
                and lc.type == loc['_embedded']['localizationScope']['type']).exists():
            locs.append(select(lc for lc in Localization if lc.code == loc['_embedded']['language']['code']
                and lc.type == loc['_embedded']['localizationScope']['type'])[:][0])
        else:
            locs.append(Localization(
                code = loc['_embedded']['language']['code'],
                type = loc['_embedded']['localizationScope']['type'],
                name = loc['_embedded']['language']['name']))

    return locs


@db_session
def formatter_parse(fmter_data):
    fmters = list()
    for fmter in fmter_data:
        if select(fmt for fmt in Formatter if fmt.formatter == fmter).exists():
            fmters.append(select(fmt for fmt in Formatter if fmt.formatter == fmter)[:][0])
        else:
            fmters.append(Formatter(formatter=fmter))

    return fmters


@db_session
def image_parse(game_detail, image_data):
    if game_detail.image:
        img = game_detail.image
        if img.href != image_data['href']:
            img.href = image_data['href']
    else:
        img = Image(game = game_detail, href = image_data['href'])

    img.formatters = formatter_parse(image_data['formatters'])
    return img


@db_session
def screenshot_parse(game_detail, scshot_data):
    scshots = list()
    scid = 0
    for scshot in scshot_data:
        if select(sc for sc in Screenshot if sc.id == scid and sc.game == game_detail).exists():
            sc = select(sc for sc in Screenshot if sc.id == scid and sc.game == game_detail)[:][0]
            if sc.href != scshot['_links']['self']['href']:
                sc.href = scshot['_links']['self']['href']
        else:
            sc = Screenshot(id = scid, game = game_detail, href = scshot['_links']['self']['href'])

        sc.formatters = formatter_parse(scshot['_links']['self']['formatters'])
        scshots.append(sc)
        scid += 1

    return scshots


@db_session
def videoprovider_parse(video_data):
    if select(pvder for pvder in VideoProvider if pvder.provider == video_data['provider']).exists():
        return select(pvder for pvder in VideoProvider if pvder.provider == video_data['provider'])[:][0]
    else:
        videohref = video_data['_links']['self']['href'].replace(video_data['videoId'], '{videoId}')
        tmbhref = video_data['_links']['thumbnail']['href'].replace(video_data['thumbnailId'], '{thumbnailId}')
        return VideoProvider(
                provider = video_data['provider'],
                videoHref = videohref,
                thumbnailHref = tmbhref)


@db_session
def video_parse(game_detail, videos_data):
    vids = list()
    videoid = 0
    for video_data in videos_data:
        if select(vid for vid in Video if vid.id == videoid and vid.game == game_detail).exists():
            vid = select(vid for vid in Video if vid.id == videoid and vid.game == game_detail)[:][0]
            if vid.videoId != video_data['videoId']:
                vid.videoId = video_data['videoId']
            if vid.thumbnailId != video_data['thumbnailId']:
                vid.thumbnailId = video_data['thumbnailId']
            if vid.provider != videoprovider_parse(video_data):
                vid.provider = videoprovider_parse(video_data)

        else:
            vid = Video(
                    id = videoid,
                    game = game_detail,
                    videoId = video_data['videoId'],
                    thumbnailId = video_data['thumbnailId'],
                    provider = videoprovider_parse(video_data))

        vids.append(vid)
        videoid += 1

    return vids


@db_session
def gamedetail_parse(gameid, json_data):
    print('now read game %s' % gameid)

    embedded_data = json_data['_embedded']
    product_data = embedded_data['product']

    if select(game for game in GameDetail if game.id == gameid).exists():
        game = select(game for game in GameDetail if game.id == gameid)[:][0]

        game.lastUpdate = datetime.utcnow()

        if game.inDevelopment != json_data['inDevelopment']['active']:
            game.inDevelopment = json_data['inDevelopment']['active']

        if game.isUsingDosBox != json_data['isUsingDosBox']:
            game.isUsingDosBox = json_data['isUsingDosBox']

        if game.isAvailableForSale != product_data['isAvailableForSale']:
            game.isAvailableForSale = product_data['isAvailableForSale']

        if game.isVisibleInCatalog != product_data['isVisibleInCatalog']:
            game.isVisibleInCatalog = product_data['isVisibleInCatalog']

        if game.isPreorder != product_data['isPreorder']:
            game.isPreorder = product_data['isPreorder']

        if game.isVisibleInAccount != product_data['isVisibleInAccount']:
            game.isVisibleInAccount = product_data['isVisibleInAccount']

        if game.isInstallable != product_data['isInstallable']:
            game.isInstallable = product_data['isInstallable']

        if game.hasProductCard != product_data['hasProductCard']:
            game.hasProductCard = product_data['hasProductCard']

        if game.isSecret != product_data['isSecret']:
            game.isSecret = product_data['isSecret']

        if 'globalReleaseDate' in product_data:
            if game.globalReleaseDate != dateutil.parser.parse(re.sub('\+.*', '', product_data['globalReleaseDate'])):
                game.globalReleaseDate = dateutil.parser.parse(re.sub('\+.*', '', product_data['globalReleaseDate']))

        if game.title != product_data['title']:
            game.title = product_data['title']

        if game.productType != embedded_data['productType']:
            game.productType = embedded_data['productType']

        if game.averageRating != API.get_game_rating(gameid):
            game.averageRating = API.get_game_rating(gameid)

    else:
        game = GameDetail(
                id = product_data['id'],
                title = product_data['title'],
                inDevelopment = json_data['inDevelopment']['active'],
                isUsingDosBox = json_data['isUsingDosBox'],
                isAvailableForSale = product_data['isAvailableForSale'],
                isVisibleInCatalog = product_data['isVisibleInCatalog'],
                isPreorder = product_data['isPreorder'],
                isVisibleInAccount = product_data['isVisibleInAccount'],
                isInstallable = product_data['isInstallable'],
                hasProductCard = product_data['hasProductCard'],
                isSecret = product_data['isSecret'],
                productType = embedded_data['productType'],
                averageRating = API.get_game_rating(gameid),
                lastUpdate = datetime.utcnow())
        if 'globalReleaseDate' in product_data:
            game.globalReleaseDate = dateutil.parser.parse(re.sub('\+.*', '', product_data['globalReleaseDate'])),

    game.links = link_parse(game, json_data['_links'])
    game.publishers = publisher_parse(embedded_data['publisher'])
    game.developers = developer_parse(embedded_data['developers'])
    game.supportedOS = os_parse(embedded_data['supportedOperatingSystems'])
    game.features = feature_parse(embedded_data['features'])
    game.tags = tag_parse(embedded_data['tags'])
    game.localizations = localization_parse(embedded_data['localizations'])
    if product_data['_links']['image']['href']:
        game.image = image_parse(game, product_data['_links']['image'])
    game.screenshots = screenshot_parse(game, embedded_data['screenshots'])
    game.videos = video_parse(game, embedded_data['videos'])

    if 'requiresGames' in json_data['_links']:
        req_games = list()
        for gid in json_data['_links']['requiresGames']:
            gid = API.get_game_id_from_url(gid['href'])
            if gid:
                if not select(game for game in GameDetail if game.id == gid).exists():
                    req_games.append(gamedetail_parse(gid, API.get_game_data(gid)))
                else:
                    req_games.append(GameDetail[gid])
        game.requiresGames = req_games

    if 'includesGames' in json_data['_links']:
        inc_games = list()
        for gid in json_data['_links']['includesGames']:
            gid = API.get_game_id_from_url(gid['href'])
            if gid:
                if not select(game for game in GameDetail if game.id == gid).exists():
                    inc_games.append(gamedetail_parse(gid, API.get_game_data(gid)))
                else:
                    inc_games.append(GameDetail[gid])
        game.includesGames = inc_games

    if len(embedded_data['editions']) > 0:
        editions = list()
        for edition in embedded_data['editions']:
            if select(game for game in GameDetail if game.id == edition['id']).exists():
                editions.append(GameDetail[edition['id']])
            else:
                json_data = API.get_game_data(edition['id'])
                if '_embedded' in json_data:
                    editions.append(gamedetail_parse(edition['id'], json_data))
        game.editions = editions

    return game

'''
@db_session
def editions_parse(gameid, json_data):
    print('now fill %s editions' % gameid)
    edition_data = json_data['_embedded']['editions']
    if len(edition_data) > 0:
        editions = list()
        for edition in edition_data:
            if select(game for game in GameDetail if game.id == edition['id']).exists():
                editions.append(GameDetail[edition['id']])
        GameDetail[gameid].editions = editions
        return editions
    else:
        return list()
'''

def safe_game_parse(gameid, json_data):
    try:
        gamedetail_parse(gameid, json_data)
    except Exception,exp:
        print(exp)
