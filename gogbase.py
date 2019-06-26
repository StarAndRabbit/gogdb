import re
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
            if isinstance(value, GOGBase):
                if with_collections == False:
                    continue
                elif related_objects == True:
                    pass
                else:
                    value = value.to_dict(with_collections=with_collections, related_objects=related_objects)
            elif isinstance(value, list):
                for i in range(0, len(value)):
                    if isinstance(value[i], GOGBase):
                        value[i] = value[i].to_dict(with_collections=with_collections, related_objects=related_objects)
            else:
                pass
            properties_dict[prop] = value

        return properties_dict


class GOGSimpleClass(GOGBase):

    @property
    def name(self):
        return self.__name

    def __init__(self, data):
        self.__name = data['name'].strip()
