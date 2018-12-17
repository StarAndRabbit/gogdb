#!/usr/bin/env python
# encoding: utf-8

from dataparse import *
from dbmodel import *
from multiprocessing.dummy import Pool as ThreadPool
import time

if __name__ == '__main__':
    db.bind('mysql', host='127.0.0.1', user='gogdb', passwd='gogdb', db='gogdb')
    db.generate_mapping(create_tables=True)

    region_parse()

    start = time.time()

    gamedetail_parse(1, API.get_game_data(1))
    all_game_id = API.get_all_game_id()
    pool = ThreadPool(8)
    pool.map(lambda gameid: safe_game_parse(gameid, API.get_game_data(gameid)), all_game_id)

    usage = time.time() - start
    print('time usage: %f ' % usage)
