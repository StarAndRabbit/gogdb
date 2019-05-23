# encoding: utf-8

from datetime import datetime
from .gogapi import API
import asyncio
import os
import simplejson as json

class GOGToken:

    def __init__(self, username, passwd):
        self.__api = API()
        self.__valid = False

        self.__token = dict()

        self.__token_file = 'token.json'
        if os.path.exists(self.__token_file):
            with open(self.__token_file, 'r') as tkfile:
                try:
                    self.__token = json.load(tkfile)
                except json.JSONDecodeError as e:
                    self.__token = self.__login(username, passwd)
        else:
            self.__token = self.__login(username, passwd)

        if self.__is_fmt_valid():
            self.__save_token()
            self.__valid = True
        else:
            self.__valid = False

    @property
    def access_token(self):
        if self.__valid:
            if not self.__is_expired():
                return self.__token['access_token']
            else:
                self.__refresh()
                return self.__token['access_token']
        else:
            return ''

    @property
    def refresh_token(self):
        if self.__valid:
            return self.__token['refresh_token']
        else:
            return ''

    @property
    def token_type(self):
        if self.__valid:
            return self.__token['token_type']
        else:
            return ''

    @property
    def user_id(self):
        if self.__valid:
            return self.__token['user_id']
        else:
            return ''

    def __login(self, user, passwd):
        data = asyncio.run(self.__api.login(user, passwd))
        if data['login_success']:
            return data
        else:
            return dict()

    def __is_expired(self):
        tdelta = datetime.utcnow() - self.__token['last_update']
        if tdelta.total_seconds() - 10 >= self.__token['expires_in']:
            return True
        else:
            return False

    def __is_fmt_valid(self):
        key_tab = [
            'expires_in',
            'scope',
            'token_type',
            'access_token',
            'user_id',
            'refresh_token',
            'session_id',
            'last_update'
        ]

        for key in key_tab:
            if key not in self.__token:
                return False
        return True

    def __save_token(self):
        with open(self.__token_file, 'w') as tkfile:
            json.dump(self.__token, tkfile)

    def __refresh(self):
        self.__token = asyncio.run(self.__api.refresh_token(self.__token['refresh_token']))
        self.__save_token()
