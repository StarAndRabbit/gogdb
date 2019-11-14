from .gogapi import gogapi
from .gogbase import GOGBase, GOGNeedNetworkMetaClass
from .utilities import CoroutinePool, Requester
import zlib
import dateutil.parser
import json
from . import dbmodel as DB
from pony import orm


def get_lan_obj(name, gen):
    if name == 'Neutral' or name == '*':
        try:
            return DB.Language['*']
        except:
            return DB.Language(code='*', name='*')
    if gen == 1:
        if orm.exists(lan for lan in DB.Language if lan.name == name.strip()):
            return orm.get(lan for lan in DB.Language if lan.name == name.strip())
        else:
            return DB.Language(code=name, name=name)
    elif gen == 2:
        try:
            return DB.Language[name]
        except:
            return DB.Language(code=name)


def get_os_obj(pk):
    try:
        return DB.OS[pk]
    except:
        return DB.OS(name=pk)


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

    def save_or_update(self):
        deps = list()
        if self.dependencies is not None:
            for idx in range(len(self.dependencies)):
                dep = self.dependencies[idx]
                if orm.exists(d for d in DB.RepositoryProductDependency if d.name == dep.strip()):
                    deps.append(orm.get(d for d in DB.RepositoryProductDependency if d.name == dep.strip()))
                else:
                    deps.append(DB.RepositoryProductDependency(name=dep.strip()))
        dict_data = self.to_dict()
        dict_data['dependencies'] = deps
        return DB.RepositoryProductV1.save_into_db(**dict_data)


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

    def save_or_update(self, idx, repov1):
        dict_data = self.to_dict()
        dict_data['id'] = idx
        dict_data['product'] = DB.RepositoryProductV1[self.product]
        dict_data['repositoryV1'] = repov1
        dict_data['languages'] = list(map(lambda x: get_lan_obj(x, 1), dict_data['languages']))
        dict_data['systems'] = list(map(get_os_obj, dict_data['systems']))

        return DB.SupportCommand.save_into_db(**dict_data)


class Redistributable(GOGBase):

    def __init__(self, repo_redist_data):
        self.__redist = repo_redist_data.get('redist')
        self.__executable = repo_redist_data.get('executable', '')
        self.__argument = repo_redist_data.get('argument', '')

    @property
    def redist(self):
        return self.__redist.strip()

    @property
    def executable(self):
        return self.__executable.strip()

    @property
    def argument(self):
        return self.__argument.strip()

    def save_or_update(self):
        try:
            return DB.Redistributable[self.redist]
        except:
            return DB.Redistributable(redist=self.redist,
                                      executable=self.executable,
                                      argument=self.argument)


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

    def save_or_update(self, repov1):
        dict_data = self.to_dict()
        dict_data['repositoryV1'] = repov1
        dict_data['languages'] = list(map(lambda x: get_lan_obj(x, 1), dict_data['languages']))
        dict_data['systems'] = list(map(get_os_obj, dict_data['systems']))
        dict_data['products'] = list(map(lambda x: DB.RepositoryProductV1[x], self.products))
        return DB.DepotV1.save_into_db(**dict_data)


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
    def timestamp(self):
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

    def __before_save_or_update(self):
        repo_prods_v1 = list(map(lambda x: x.save_or_update(), self.products))
        redists = list(map(lambda x: x.save_or_update(), self.redistributables))
        return {
            "products": repo_prods_v1,
            "redistributables": redists
        }

    def __after_save_or_update(self, repov1_db_obj):
        def gen_supcmd(supcmd_data):
            idx, supcmd_obj = supcmd_data
            return supcmd_obj.save_or_update(idx, repov1_db_obj)
        list(map(gen_supcmd, enumerate(self.supportCommands)))
        list(map(lambda x: x.save_or_update(repov1_db_obj), self.depots))

    def save_or_update(self, build):
        ext_data = self.__before_save_or_update()
        dict_data = self.to_dict(with_collections=False)
        dict_data['rootGame'] = DB.GameDetail[self.rootGame]
        dict_data['build'] = build
        dict_data['products'] = ext_data['products']
        dict_data['redistributables'] = ext_data['redistributables']
        repov1 = DB.RepositoryV1.save_into_db(**dict_data)
        self.__after_save_or_update(repov1)
        return repov1


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

    def save_or_update(self):
        return DB.RepositoryProductV2.save_into_db(**self.to_dict())


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

    def save_or_update(self):
        return DB.CloudSave.save_into_db(**self.to_dict())


class DepotV2(GOGBase):

    def __init__(self, depot_data, isOffline=False):
        self.__manifest = depot_data.get('manifest')
        self.__comp_size = depot_data.get('compressedSize')
        self.__prod_id = depot_data.get('productId')
        self.__languages = depot_data.get('languages')
        self.__languages = list(map(lambda x: x.split('-')[0], self.__languages))
        self.__size = depot_data.get('size')
        self.__is_offline = isOffline

    @property
    def manifest(self):
        return self.__manifest

    @property
    def compressedSize(self):
        return self.__comp_size

    @property
    def productId(self):
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

    def save_or_update(self, repo_v2):
        dict_data = self.to_dict()
        dict_data['repositoryV2'] = repo_v2
        dict_data['languages'] = list(map(lambda x: get_lan_obj(x, 2), self.languages))
        return DB.DepotV2.save_into_db(**dict_data)


class RepoV2(GOGBase):

    def __init__(self, repo_data):
        self.__base_prod = repo_data.get('baseProductId')
        self.__client_id = repo_data.get('clientId')
        self.__client_secret = repo_data.get('clientSecret')
        self.__install_dir = repo_data.get('installDirectory')
        self.__platform = repo_data.get('platform')
        self.__tags = repo_data.get('tags', '')
        self.__dependencies = repo_data.get('dependencies', [])
        self.__products = list(map(lambda x: RepoProductV2(x), repo_data.get('products', [])))
        self.__depots_unmerged = list(map(lambda x: DepotV2(x), repo_data.get('depots', [])))
        # merge
        self.__depots = list()
        manifest_list = list()
        for depots in self.__depots_unmerged:
            if depots.manifest not in manifest_list:
                self.__depots.append(depots)
                manifest_list.append(depots.manifest)
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

    def __before_save_or_update(self):
        repo_prods_v2 = list(map(lambda x: x.save_or_update(), self.products))
        cloud_saves = list(map(lambda x: x.save_or_update(), self.cloudSaves))
        def get_dep(dep):
            try:
                return DB.Dependency[dep]
            except:
                return DB.Dependency(name=dep)
        deps = list(map(get_dep, self.dependencies))

        return {
            "products": repo_prods_v2,
            "cloudSaves": cloud_saves,
            "dependencies": deps
        }

    def __after_save_or_update(self, repo_db_obj):
        list(map(lambda x: x.save_or_update(repo_db_obj), self.depots))

    def save_or_update(self, build_db_obj):
        ext_data = self.__before_save_or_update()
        dict_data = self.to_dict(with_collections=False)
        dict_data['baseProduct'] = DB.GameDetail[self.baseProduct]
        dict_data['build'] = build_db_obj
        dict_data['products'] = ext_data['products']
        dict_data['dependencies'] = ext_data['dependencies']
        dict_data['cloudSaves'] = ext_data['cloudSaves']
        repo_db_obj = DB.RepositoryV2.save_into_db(**dict_data)
        self.__after_save_or_update(repo_db_obj)
        return repo_db_obj


class Build(GOGBase, GOGNeedNetworkMetaClass):

    def __init__(self, build_data, isDefault=False):
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
        self.__is_default = isDefault

    @classmethod
    async def create(cls, build_data, isDefault=False):
        self = Build(build_data, isDefault)
        repo_data = await self.__get_repo_data(build_data.get('link'), self.__gen)

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

    @classmethod
    async def create_multi(cls, builds_data: list):
        if len(builds_data) > 0:
            coro_list = [Build.create(builds_data[0], True)]
            if len(builds_data) > 1:
                coro_list.extend([Build.create(build_data) for build_data in builds_data[1:]])
        else:
            coro_list = []
        coro_pool = CoroutinePool(coro_list=coro_list)
        return await coro_pool.run_all()

    async def __get_repo_data(self, url, gen):
        async with Requester() as request:
            data = await request.get(url)
            if gen == 1:
                data = json.loads(data.text)
            elif gen == 2:
                data = json.loads(zlib.decompress(data.content).decode("utf-8"))
            else:
                data = ValueError('Generation not supported')

            return data

    @property
    def isDefault(self):
        return self.__is_default

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

    def save_or_update(self):
        dict_data = self.to_dict(with_collections=False)
        dict_data['product'] = DB.GameDetail[self.product]
        build_obj = DB.Build.save_into_db(**dict_data)
        if self.repositoryV1 is not None:
            self.repositoryV1.save_or_update(build_obj)
        elif self.repositoryV2 is not None:
            self.repositoryV2.save_or_update(build_obj)
        return build_obj


class BuildsTable(GOGBase, GOGNeedNetworkMetaClass):

    def __init__(self, prod_id):
        self.__builds = list()
        self.__prod_id = prod_id

    @classmethod
    async def create(cls, prod_id: str, os: str):
        builds_data = await gogapi.get_product_builds(prod_id, os)
        builds_data = builds_data.get('items', [])
        self = BuildsTable(prod_id)
        self.__builds = await Build.create_multi(builds_data)
        cls.try_exception(*self.__builds)

        return self

    @classmethod
    async def create_multi(cls, prod_ids: list, os_list: list):
        coro_list = list()
        for prod_id in prod_ids:
            for os in os_list:
                coro_list.append(BuildsTable.create(prod_id, os))
        coro_pool = CoroutinePool(coro_list=coro_list)
        return await coro_pool.run_all()

    @property
    def builds(self):
        return self.__builds

    @property
    def product(self):
        return self.__prod_id

    def save_or_update(self):
        return list(map(lambda x: x.save_or_update(), self.builds))
