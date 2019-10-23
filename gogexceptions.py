from aiohttp.client_exceptions import ClientResponseError


class GOGBaseException(Exception):
    pass


class GOGAPIException(GOGBaseException):
    pass


class GOGDatabaseException(GOGBaseException):
    pass


class GOGBadRequest(GOGAPIException):
    def __init__(self):
        super().__init__('Bad Request, please check url or payload')


class GOGNetworkError(GOGAPIException):
    def __init__(self):
        super().__init__('Network Error, try again later')


class GOGNotFound(GOGAPIException):

    def __init__(self):
        super().__init__("Page Not Fund")


class GOGResponseError(GOGAPIException):

    @classmethod
    def judge_status(cls, exp: ClientResponseError):
        if exp.status == 404:
            return GOGNotFound()
        else:
            return GOGNetworkError()


class GOGProductNotFound(GOGAPIException):
    def __init__(self, prod_id):
        self.product_id = prod_id
        super().__init__(f'Product {prod_id} not exists')


class GOGUnknowError(GOGAPIException):

    def __init__(self, exp_instance: Exception):
        super().__init__(f"error type: {type(exp_instance)}\nerror message: {str(exp_instance)}")


class GOGLoginError(GOGAPIException):
    pass


class GOGNeedVerification(GOGLoginError):
    def __init__(self):
        super().__init__('GOG is asking for a reCAPTCHA :( try again in a few minutes.')


class GOGAccountError(GOGLoginError):
    def __init__(self):
        super().__init__('GOG Username or Password Error')


class NeedPrimaryKey(GOGDatabaseException):
    pass

class CRTemplateFormatError(GOGDatabaseException):
    pass