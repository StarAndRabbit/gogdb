from enum import Enum

class CRTypes(Enum):
    PRODUCT_ADD = 0
    PRODUCT_INIT = 1
    PRODUCT_INVISIBLE = 2
    DETIAL_CHANGE = 3
    SET_ADD = 4
    SET_RM = 5
    BASEPRICE_CHANGE = 6


class CRArgs:

    @staticmethod
    def wrap_args(crtype: CRTypes, *args):
        return {
            CRTypes.PRODUCT_ADD: CRArgs.wrap_args_product_cr,
            CRTypes.PRODUCT_INIT: CRArgs.wrap_args_product_cr,
            CRTypes.PRODUCT_INVISIBLE: CRArgs.wrap_args_product_cr,
            CRTypes.DETIAL_CHANGE: CRArgs.wrap_args_detail_cr,
            CRTypes.SET_ADD: CRArgs.wrap_args_set_type_cr,
            CRTypes.SET_RM: CRArgs.wrap_args_set_type_cr,
            CRTypes.BASEPRICE_CHANGE: CRArgs.wrap_args_price_cr,
        }[crtype](crtype, *args)

    @staticmethod
    def wrap_args_product_cr(crtype: CRTypes, product_id):
        return [
            crtype.name,
            product_id
        ]

    @staticmethod
    def wrap_args_detail_cr(crtype: CRTypes, product_id, attr_name, old_value, new_value):
        return [
            crtype.name,
            product_id,
            attr_name,
            old_value,
            new_value
        ]

    @staticmethod
    def wrap_args_set_type_cr(crtype: CRTypes, product_id, attr_name, value):
        return [
            crtype.name,
            product_id,
            attr_name,
            value
        ]

    @staticmethod
    def wrap_args_price_cr(crtype: CRTypes, product_id, attr_name, country, old_value, new_value, currency):
        return [
            crtype.name,
            product_id,
            attr_name,
            country,
            old_value,
            new_value,
            currency
        ]