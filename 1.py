import json

from data import db_session
from data import question

import requests
from bs4 import BeautifulSoup

with open(f'game_logs/5115468386261226788.json', 'r') as cat_file:
    data = json.load(cat_file)

print(data)