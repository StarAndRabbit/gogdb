#!/usr/bin/env python
# encoding: utf-8

from dataparse import *
from dbmodel import *
from multiprocessing.dummy import Pool as ThreadPool
import time

if __name__ == '__main__':

    db.bind('postgres', host='127.0.0.1', user='gogdb', password='gogdb', database='gogdb')
    db.generate_mapping(create_tables=True)

    dblite.bind('sqlite', 'gamelist.db', create_db=True)
    dblite.generate_mapping(create_tables=True)

    region_parse()

    start = time.time()

    all_game_id = gamelist_parse()
    pool = ThreadPool(8)
    pool.map(lambda gameid: safe_game_parse(gameid), all_game_id)

    usage = time.time() - start
    print('time usage: %f ' % usage)
