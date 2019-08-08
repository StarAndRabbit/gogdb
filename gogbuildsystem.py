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
        self.__systems = repo_supcmd_data.get('systems')
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
        self.__systems = repo_depot_data.get('systems')
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
        self.__support_commands = list(map(lambda x: SupportCommands(x), repo_data.get('support_commands')))

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

        repo_data = build_data.get('link')
        if isinstance(repo_data, str):
            repo_data = asyncio.run(self.__get_repo_data(repo_data, self.__gen))
        if isinstance(repo_data, Exception):
            raise repo_data
        if self.__gen == 1:
            self.__repo_v1 = RepoV1(repo_data)
        elif self.__gen == 2:
            raise NotImplementedError
        else:
            raise ValueError('Generation not supported')

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
