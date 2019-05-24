# encoding: utf-8

from datetime import datetime
from .gogapi import API
import asyncio
import simplejson as json

def datetime_encoder(obj):
    if isinstance(obj, datetime):
        return obj.strftime('%Y-%m-%d %H:%M:%S')

def datetime_decoder(dct):
    if 'last_update' in dct:
        dct['last_update'] = datetime.strptime(dct['last_update'], '%Y-%m-%d %H:%M:%S')
    return dct


class GOGToken:

    def __init__(self, autosave=True):
        self.__expires_in = 3600
        self.__scope = ''
        self.__token_type = ''
        self.__access_token = ''
        self.__user_id = ''
        self.__refresh_token = ''
        self.__session_id = ''
        self.__last_update = datetime.utcnow()

        self.__token_file = 'token.json'
        self.__is_autosave = autosave

        self.__api = API()

    @property
    def access_token(self):
        if self.is_expired():
            self.refresh()
        return self.__access_token

    @property
    def token_type(self):
        return self.__token_type

    @property
    def user_id(self):
        return self.__user_id

    @property
    def refresh_token(self):
        return self.__refresh_token

    @property
    def token_file(self):
        return self.__token_file

    @property
    def auto_save(self):
        return self.__is_autosave

    def to_dict(self):
        return {
            'expires_in': self.__expires_in,
            'scope': self.__scope,
            'token_type': self.__token_type,
            'access_token': self.__access_token,
            'user_id': self.__user_id,
            'refresh_token': self.__refresh_token,
            'session_id': self.__session_id,
            'last_update': self.__last_update
        }

    def load(self, **kwargs):
        self.__expires_in = kwargs['expires_in']
        self.__scope = kwargs['scope']
        self.__token_type = kwargs['token_type']
        self.__access_token = kwargs['access_token']
        self.__user_id = kwargs['user_id']
        self.__refresh_token = kwargs['refresh_token']
        self.__session_id = kwargs['session_id']
        self.__last_update = kwargs['last_update']

        if self.__is_autosave:
            self.save_to_file()

    def load_from_file(self, filename=None):
        if filename == None:
            filename = self.__token_file
        else:
            self.__token_file = filename
        with open(filename, 'r') as tkfile:
            data = json.load(tkfile, object_hook=datetime_decoder)
            self.load(**data)

    def save_to_file(self, filename=None):
        if filename == None:
            filename = self.__token_file
        else:
            self.__token_file = filename
        with open(filename, 'w') as tkfile:
            json.dump(self.to_dict(), tkfile, default=datetime_encoder)

    def is_expired(self):
        tdelta = datetime.utcnow() - self.__last_update
        if tdelta.total_seconds() + 10 >= self.__expires_in:
            return True
        else:
            return False

    def refresh(self):
        data = asyncio.run(self.__api.refresh_token(self.__refresh_token))
        if 'error' not in data:
            self.load(**data)
            if self.__is_autosave:
                self.save_to_file()