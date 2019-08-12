from .gogapi import *
from .gogbase import GOGBase
import asyncio
import zlib
import dateutil.parser

class RepoProductV1(GOGBase):

    def __init__(self, repo_prod_data):
        self.__standalone = repo_prod_data.get('standalone', False)
        self.__game = repo_prod_data.get('gameID')
        self.__dependencies = repo_prod_data.get('dependencies')

    @property
    def standalone(self):
        return self.__standalone

    @property
    def game(self):
        return self.__game

    @property
    def dependencies(self):
        return self.__dependencies


class SupportCommands(GOGBase):

    def __init__(self, repo_supcmd_data):
        self.__product = repo_supcmd_data.get('gameID')
        self.__languages = repo_supcmd_data.get('languages')
        self.__argument = repo_supcmd_data.get('argument', '')
        self.__systems = list(map(lambda x: x.lower(), repo_supcmd_data.get('systems')))
        self.__executable = repo_supcmd_data.get('executable')

    @property
    def product(self):
        return self.__product

    @property
    def languages(self):
        return self.__languages

    @property
    def argument(self):
        return self.__argument

    @property
    def systems(self):
        return self.__systems

    @property
    def executable(self):
        return self.__executable


class Redistributable(GOGBase):

    def __init__(self, repo_redist_data):
        self.__redist = repo_redist_data.get('redist')
        self.__executable = repo_redist_data.get('executable')
        self.__argument = repo_redist_data.get('argument')

    @property
    def redist(self):
        return self.__redist

    @property
    def executable(self):
        return self.__executable

    @property
    def argument(self):
        return self.__argument


class DepotV1(GOGBase):

    def __init__(self, repo_depot_data):
        self.__products = repo_depot_data.get('gameIDs')
        self.__languages = repo_depot_data.get('languages')
        self.__manifest = repo_depot_data.get('manifest')
        self.__systems = list(map(lambda x: x.lower(), repo_depot_data.get('systems')))
        self.__size = repo_depot_data.get('size')

    @property
    def products(self):
        return self.__products

    @property
    def languages(self):
        return self.__languages

    @property
    def manifest(self):
        return self.__manifest

    @property
    def systems(self):
        return self.__systems

    @property
    def size(self):
        return self.__size


class RepoV1(GOGBase):

    def __init__(self, repo_data):
        repo_data = repo_data['product']
        self.__rootGame = repo_data.get('rootGameID')
        self.__timestamp = repo_data.get('timestamp')
        self.__products = list(map(lambda x: RepoProductV1(x), repo_data.get('gameIDs')))
        self.__support_commands = list(map(lambda x: SupportCommands(x), repo_data.get('support_commands', [])))

        self.__redists = list()
        self.__depots = list()
        for data in repo_data.get('depots'):
            if 'redist' in data:
                self.__redists.append(Redistributable(data))
            else:
                self.__depots.append(DepotV1(data))

        self.__installDirectory = repo_data.get('installDirectory')
        self.__projectName = repo_data.get('projectName')

    @property
    def rootGame(self):
        return self.__rootGame

    @property
    def timeStamp(self):
        return self.__timestamp

    @property
    def products(self):
        return self.__products

    @property
    def installDirectory(self):
        return self.__installDirectory

    @property
    def projectName(self):
        return self.__projectName

    @property
    def supportCommands(self):
        return self.__support_commands

    @property
    def redistributables(self):
        return self.__redists

    @property
    def depots(self):
        return self.__depots


class RepoProductV2(GOGBase):

    def __init__(self, repo_prod_data):
        self.__product = repo_prod_data.get('productId')
        self.__script = repo_prod_data.get('script', '')
        self.__temp_args = repo_prod_data.get('temp_arguments', '')
        self.__temp_exec = repo_prod_data.get('temp_executable', '')

    @property
    def product(self):
        return self.__product

    @property
    def script(self):
        return self.__script

    @property
    def tempArguments(self):
        return self.__temp_args

    @property
    def tempExecutable(self):
        return self.__temp_exec


class CloudSave(GOGBase):

    def __init__(self, cloudsave_data):
        self.__location = cloudsave_data.get('location')
        self.__name = cloudsave_data.get('name')

    @property
    def location(self):
        return self.__location

    @property
    def name(self):
        return self.__name


class DepotV2(GOGBase):

    def __init__(self, depot_data, isOffline=False):
        self.__manifest = depot_data.get('manifest')
        self.__comp_size = depot_data.get('compressedSize')
        self.__prod_id = depot_data.get('productId')
        self.__languages = depot_data.get('languages')
        self.__size = depot_data.get('size')
        self.__is_offline = isOffline

    @property
    def manifest(self):
        return self.__manifest

    @property
    def compressedSize(self):
        return self.__comp_size

    @property
    def product(self):
        return self.__prod_id

    @property
    def languages(self):
        return self.__languages

    @property
    def size(self):
        return self.__size

    @property
    def isOffline(self):
        return self.__is_offline


class RepoV2(GOGBase):

    def __init__(self, repo_data):
        self.__base_prod = repo_data.get('baseProductId')
        self.__client_id = repo_data.get('clientId')
        self.__client_secret = repo_data.get('clientSecret')
        self.__install_dir = repo_data.get('installDirectory')
        self.__platform = repo_data.get('platform')
        self.__tags = repo_data.get('tags')
        self.__dependencies = repo_data.get('dependencies')
        self.__products = list(map(lambda x: RepoProductV2(x), repo_data.get('products', [])))
        self.__depots = list(map(lambda x: DepotV2(x), repo_data.get('depots', [])))
        if 'manifest' in repo_data.get('offlineDepot', dict()):
            self.__depots.append(DepotV2(repo_data.get('offlineDepot'), True))
        self.__cloud_saves = list(map(lambda x: CloudSave(x), repo_data.get('cloudSaves', [])))

    @property
    def baseProduct(self):
        return self.__base_prod

    @property
    def clientId(self):
        return self.__client_id

    @property
    def clientSecret(self):
        return self.__client_secret

    @property
    def installDirectory(self):
        return self.__install_dir

    @property
    def platform(self):
        return self.__platform

    @property
    def tags(self):
        return self.__tags

    @property
    def products(self):
        return self.__products

    @property
    def depots(self):
        return self.__depots

    @property
    def dependencies(self):
        return self.__dependencies

    @property
    def cloudSaves(self):
        return self.__cloud_saves


class Build(GOGBase):

    def __init__(self, build_data):
        self.__build_id = build_data.get('build_id')
        self.__product_id = build_data.get('product_id')
        self.__os = build_data.get('os')
        self.__branch = build_data.get('branch')
        self.__version = build_data.get('version_name')
        self.__tags = build_data.get('tags')
        self.__public = build_data.get('public', True)
        self.__date_published = dateutil.parser.parse(build_data.get('date_published')).replace(tzinfo=None)
        self.__gen = build_data.get('generation')
        self.__legacy_build_id = build_data.get('legacy_build_id', None)

    @classmethod
    async def follow_link(cls, build_data):
        self = Build(build_data)
        repo_data = build_data.get('link')
        if isinstance(repo_data, str):
            repo_data = await self.__get_repo_data(repo_data, self.__gen)
        if isinstance(repo_data, Exception):
            raise repo_data
        if self.__gen == 1:
            self.__repo_v1 = RepoV1(repo_data)
            self.__repo_v2 = None
        elif self.__gen == 2:
            self.__repo_v1 = None
            self.__repo_v2 = RepoV2(repo_data)
        else:
            raise ValueError('Generation not supported')
        return self

    async def __get_repo_data(self, url, gen):
        async with APIRequester() as request:
            if gen == 1:
                data = await request.get(url)
                if not isinstance(data, Exception):
                    data = json.loads(data['text'])
            elif gen == 2:
                data = await request.get(url)
                if not isinstance(data, Exception):
                    data = zlib.decompress(data.get('text')).decode("utf-8")
                    data = json.loads(data)
            else:
                data = ValueError('Generation not supported')

            return data

    @property
    def buildId(self):
        return self.__build_id

    @property
    def product(self):
        return self.__product_id

    @property
    def os(self):
        return self.__os

    @property
    def branch(self):
        return self.__branch

    @property
    def version(self):
        return self.__version

    @property
    def tags(self):
        return self.__tags

    @property
    def datePublished(self):
        return self.__date_published

    @property
    def generation(self):
        return self.__gen

    @property
    def legacyBuildId(self):
        return self.__legacy_build_id

    @property
    def repositoryV1(self):
        return self.__repo_v1

    @property
    def repositoryV2(self):
        return self.__repo_v2


class BuildsTable(GOGBase):

    def __init__(self, builds_data):
        self.__builds = list(map(lambda x: Build(x), builds_data.get('items', [])))

    @classmethod
    async def create_repo(cls, builds_data):
        self = BuildsTable(builds_data)
        self.__builds = await self.__gen_all_build_obj(builds_data)
        return self

    async def __gen_all_build_obj(self, builds_data):
        return await asyncio.gather(*[Build.follow_link(data) for data in builds_data.get('items', [])])

    @property
    def builds(self):
        return self.__builds


def error_chk(builds_data):
    if isinstance(builds_data, GOGBaseException):
        return True
    else:
        return False


async def gen_builds_table_wrap(builds_data):
    if error_chk(builds_data):
        return await builds_data
    else:
        return await BuildsTable.create_repo(builds_data)


async def create_builds_tasks(prod_id, platform):
    api = API()
    data = await api.get_product_builds(prod_id, platform)
    return await asyncio.gather(*[gen_builds_table_wrap(builds_data) for builds_data in data])


def create_multi_builds(prod_id, platform):
    return asyncio.run(create_builds_tasks(prod_id, platform))
