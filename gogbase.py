import inspect


class GOGBase:

    def to_dict(self, only=None, exclude=None, with_collections=True, related_objects=False):
        members = dict(inspect.getmembers(self))
        classes = inspect.getmembers(self, inspect.isclass)
        properties = inspect.getmembers(classes[0][1], lambda x: isinstance(x, property))
        properties = list(map(lambda x: x[0], properties))

        properties_dict = dict()
        for prop in properties:
            if only is not None:
                if prop not in only:
                    continue
            else:
                if exclude is not None:
                    if prop in exclude:
                        continue

            value = members[prop]
            value = self.__deal_data(value, with_collections, related_objects)
            if value is None:
                continue
            properties_dict[prop] = value

        return properties_dict

    def __deal_data(self, data, with_collections, related_objects):
        value = data
        if isinstance(value, GOGBase):
            if not with_collections:
                return None
            elif related_objects:
                return value
            else:
                return value.to_dict(with_collections=with_collections, related_objects=related_objects)
        elif isinstance(value, list):
            for i in range(0, len(value)):
                tmp = self.__deal_data(value[i], with_collections, related_objects)
                if tmp is not None:
                    value[i] = tmp
            return value
        elif isinstance(value, dict):
            for key in value:
                tmp = self.__deal_data(value[key], with_collections, related_objects)
                if tmp is not None:
                    value[key] = tmp
            return value
        elif isinstance(value, str):
            return value.strip()
        else:
            return value


class GOGSimpleClass(GOGBase):

    @property
    def name(self):
        return self.__name

    def __init__(self, data):
        self.__name = data['name'].strip()


class GOGFile(GOGBase):

    @property
    def id(self):
        return self.__id

    @property
    def size(self):
        return self.__filesize

    @property
    def downlink(self):
        return self.__downlink

    def __init__(self, product_slug, file_data):
        self.__id = file_data['id'] if isinstance(file_data['id'], int) else file_data['id'].strip()
        self.__filesize = file_data['size']
        self.__downlink = f'https://www.gog.com/downlink/{product_slug}/{self.__id}'


class GOGDownloadable(GOGBase):

    @property
    def id(self):
        return self.__id

    @property
    def totalSize(self):
        return self.__totalSize

    @property
    def files(self):
        return self.__files

    def __init__(self, product_slug, down_data):
        self.__id = down_data['id'] if isinstance(down_data['id'], int) else down_data['id'].strip()
        self.__totalSize = down_data['total_size']
        self.__files = list(map(lambda x: GOGFile(product_slug, x), down_data['files']))
