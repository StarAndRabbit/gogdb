class GOGBaseException(Exception):
    pass


class GOGBadRequest(GOGBaseException):
    def __init__(self):
        super().__init__('Bad Request, please check url or payload')


class GOGNetworkError(GOGBaseException):
    def __init__(self):
        super().__init__('Network Error, try again later')


class GOGProductNotFound(GOGBaseException):

    def __init__(self, prod_id):
        self.product_id = prod_id
        super().__init__(f"product {self.product_id} not exists")


class GOGUnknowError(GOGBaseException):

    def __init__(self, exp_instance):
        super().__init__(f"error type: {type(exp_instance)}\nerror message: {str(exp_instance)}")
