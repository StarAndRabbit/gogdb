import re
from .gogexceptions import *

class OptType:
    ADD = "add"
    DEL = "delete"
    CHG = "change"


class ArgsName:
    PROD_ID = "product_id"      # product id
    OLD_STR = "old_str"         # old string
    NEW_STR = "new_str"         # new string
    OLD_NUM = "old_num"         # old number
    NEW_NUM = "new_num"         # new number
    ATTR_NAME = "attr_name"     # attribute name


class Template:
    def __init__(self, name, type, args_name: list, fmt_str):
        self.name = name
        self.type = type
        self.args_name = args_name
        self.fmt_str = fmt_str
        self.check_valid()

    def check_valid(self):
        args = len(self.args_name)
        reg = re.compile(r'{\d+}')
        if args < len(reg.findall(self.fmt_str)):
            raise CRTemplateFormatError

    def to_dict(self):
        return {
            'name': self.name,
            'type': self.type,
            'argsName': self.args_name,
            'formatString': self.fmt_str
        }


class ChangeTemplates:
    def __init__(self):
        self.__prod_add = Template('prod_add', OptType.ADD,
                                   [ArgsName.PROD_ID], 'Added Product ID {0}')
        self.__prod_init = Template('prod_init', OptType.CHG,
                                    [ArgsName.PROD_ID], 'Product {0} initialized')
        self.__prod_invs = Template('prod_invs', OptType.DEL,
                                    [ArgsName.PROD_ID], 'Set Product {0} invisible')
        self.__common_chg_str = Template('common_chg_str', OptType.CHG,
                                         [ArgsName.ATTR_NAME, ArgsName.OLD_STR, ArgsName.NEW_STR, ArgsName.PROD_ID],
                                         'Changed {0} – {1} › {2}')

    @property
    def prod_add(self):
        return self.__prod_add.to_dict()

    @property
    def prod_init(self):
        return self.__prod_init.to_dict()

    @property
    def prod_invs(self):
        return self.__prod_invs.to_dict()

    @property
    def common_chg_str(self):
        return self.__common_chg_str.to_dict()


change_templates = ChangeTemplates()