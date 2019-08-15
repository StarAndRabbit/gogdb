from .gogbase import GOGBase, GOGNeedNetworkMetaClass
from .gogapi import gogapi
from .utilities import CoroutinePool
from decimal import Decimal


class AchievementRarityLevel(GOGBase):
    def __init__(self, slug, desc):
        self.__slug = slug
        self.__desc = desc

    @property
    def slug(self):
        return self.__slug

    @property
    def description(self):
        return self.__desc


class Achievement(GOGBase):

    def __init__(self, achi_data):
        self.__id = achi_data['achievement_id']
        self.__key = achi_data['achievement_key']
        self.__visiable = achi_data['visible']
        self.__name = achi_data['name']
        self.__desc = achi_data['description']
        self.__unlocked_image = achi_data['image_url_unlocked']
        self.__locked_image = achi_data['image_url_locked']
        self.__rarity = Decimal(achi_data['rarity']).quantize(Decimal('.00'))
        self.__rarity_level = AchievementRarityLevel(achi_data['rarity_level_slug'],
                                                     achi_data['rarity_level_description'])

    @property
    def id(self):
        return self.__id

    @property
    def key(self):
        return self.__key

    @property
    def visiable(self):
        return self.__visiable

    @property
    def name(self):
        return self.__name

    @property
    def description(self):
        return self.__desc

    @property
    def imageUrlUnlocked(self):
        return self.__unlocked_image

    @property
    def imageUrlLocked(self):
        return self.__locked_image

    @property
    def rarity(self):
        return self.__rarity

    @property
    def achievementRarityLevel(self):
        return self.__rarity_level


class AchievementsTable(GOGBase, GOGNeedNetworkMetaClass):
    def __init__(self, achis_data):
        self.__total_count = achis_data['total_count']
        self.__mode = achis_data['achievements_mode']
        self.__achievements = [Achievement(data) for data in achis_data.get('items', [])]

    @classmethod
    async def create(cls, client_id, user_id, token_type, access_token):
        achis_data = await gogapi.get_product_achievement(client_id, user_id, token_type, access_token)
        return AchievementsTable(achis_data)

    @classmethod
    async def create_multi(cls, client_ids: list, user_id, token_type, access_token):
        coro_pool = CoroutinePool(coro_list=[AchievementsTable.create(client_id,
                                                                      user_id,
                                                                      token_type,
                                                                      access_token)
                                             for client_id in client_ids])
        return await coro_pool.run_all()

    @property
    def total_count(self):
        return self.__total_count

    @property
    def mode(self):
        return self.__mode

    @property
    def achievements(self):
        return self.__achievements
