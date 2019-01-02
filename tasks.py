from celeryapp import app
from gogapi import API

api = API()

@app.task
def get_game_data(game_id):
    main_data = list(api.get_game_data(game_id))
    rating_data = list(api.get_game_rating(game_id))
    point = 0
    for data in main_data:
        data['averageRating'] = rating_data[point]
        point += 1

    return main_data

@app.task
def get_game_global_price(game_id):
    country_table = api.get_region_table().keys()
    return list(api.get_multi_game_global_price(game_id, country_table))

@app.task
def get_all_game_id():
    return list(api.get_all_game_id())

@app.task
def get_game_discount(game_id):
    return list(api.get_game_discount(game_id))
