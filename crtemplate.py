from .gogexceptions import *
from .crtypes import CRTypes
from enum import Enum
from abc import ABCMeta, abstractmethod


class OperationType(Enum):
    NONE = 0
    ADDED = 1
    CHANGED = 2
    REMOVED = 3


class CRTemplate(metaclass=ABCMeta):

    def __init__(self, opt: OperationType, template_str: str, identifier: CRTypes):
        self._opt = opt
        self._template_string = template_str
        self._identifier = identifier
        self._args = list()

    @abstractmethod
    def load(self, cr_obj):
        self._args = cr_obj.args[1:]

    def template_check(self, cr_obj):
        if cr_obj.args[0] != self.identifier.name:
            raise WrongCRTemplate

    def format(self):
        return self.template_string.format(*[arg for arg in self._args])

    @property
    def operation(self):
        return self._opt

    @property
    def template_string(self):
        return self._template_string

    @property
    def identifier(self):
        return self._identifier


class ProductCR(CRTemplate):

    def __init__(self, opt: OperationType, template_str: str, identifier: CRTypes):
        super().__init__(opt, template_str, identifier)
        self.__product_id = ''

    def load(self, cr_obj):
        self.template_check(cr_obj)
        super().load(cr_obj)
        self.__product_id = self._args[0]

    @property
    def product_id(self):
        return self.__product_id


class ProductDetailCR(CRTemplate):

    def __init__(self, opt: OperationType, template_str: str, identifier: CRTypes):
        super().__init__(opt, template_str, identifier)
        self.__product_id = ''
        self.__attr = ''
        self.__old_value = ''
        self.__new_value = ''

    def load(self, cr_obj):
        self.template_check(cr_obj)
        super().load(cr_obj)
        self.__product_id, self.__attr, self.__old_value, self.__new_value = self._args

    @property
    def product_id(self):
        return self.__product_id

    @property
    def attribute_name(self):
        return self.__attr

    @property
    def old_value(self):
        return self.__old_value

    @property
    def new_value(self):
        return self.__new_value


class SetTypeAttrCR(CRTemplate):
    def __init__(self, opt: OperationType, template_str: str, identifier: CRTypes):
        super().__init__(opt, template_str, identifier)
        self.__product_id = ''
        self.__attr = ''
        self.__value = ''

    def load(self, cr_obj):
        self.template_check(cr_obj)
        super().load(cr_obj)
        self.__product_id, self.__attr, self.__value = self._args

    @property
    def product_id(self):
        return self.__product_id

    @property
    def attribute_name(self):
        return self.__attr

    @property
    def value(self):
        return self.__value


class PriceCR(CRTemplate):
    def __init__(self, opt: OperationType, template_str: str, identifier: CRTypes):
        super().__init__(opt, template_str, identifier)
        self.__product_id = ''
        self.__attr = ''
        self.__old_value = ''
        self.__new_value = ''
        self.__country = ''
        self.__currency = ''

    def load(self, cr_obj):
        self.template_check(cr_obj)
        super().load(cr_obj)
        self.__product_id, self.__attr, self.__country,\
        self.__old_value, self.__new_value, self.__currency  = self._args

    @property
    def product_id(self):
        return self.__product_id

    @property
    def attribute_name(self):
        return self.__attr

    @property
    def old_value(self):
        return self.__old_value

    @property
    def new_value(self):
        return self.__new_value

    @property
    def country(self):
        return self.__country

    @property
    def currency(self):
        return self.__currency


product_add = ProductCR(OperationType.ADDED, 'Added Product ID {0}', CRTypes.PRODUCT_ADD)
product_init = ProductCR(OperationType.CHANGED, 'Product {0} initialized', CRTypes.PRODUCT_INIT)
product_invisible = ProductCR(OperationType.REMOVED, 'Set Product {0} invisible', CRTypes.PRODUCT_INVISIBLE)

detail_change = ProductDetailCR(OperationType.CHANGED, 'Changed {1} – {2} › {3}', CRTypes.DETIAL_CHANGE)

set_add = SetTypeAttrCR(OperationType.CHANGED, 'Changed {1} – added {2}', CRTypes.SET_ADD)
set_remove = SetTypeAttrCR(OperationType.CHANGED, 'Changed {1} – removed {2}', CRTypes.SET_RM)

baseprice_change = PriceCR(OperationType.CHANGED, 'Changed {1} in {2} – {3} › {4} {5}', CRTypes.BASEPRICE_CHANGE)


cr_templates = {
    CRTypes.PRODUCT_ADD.name: product_add,
    CRTypes.PRODUCT_INIT.name: product_init,
    CRTypes.PRODUCT_INVISIBLE.name: product_invisible,
    CRTypes.DETIAL_CHANGE.name: detail_change,
    CRTypes.SET_ADD.name: set_add,
    CRTypes.SET_RM.name: set_remove,
    CRTypes.BASEPRICE_CHANGE.name: baseprice_change
}