from data import db_session
from data import question

import requests
from bs4 import BeautifulSoup


req = requests.get('https://db.chgk.info/search/questions/%D1%83%D1%82%D0%BA%D0%B0/any_word/QAC/limit10000').content
soup = BeautifulSoup (req, 'html.parser')
db_session.global_init("db/3W.sqlite")
db_sess = db_session.create_session()
for i in range(len(soup.find_all(class_='question')[0])):
    nquestion = question.Question()
    nquestion.autor = 1
    nquestion.question = ''.join(soup.find_all(class_='question')[i].find_all('p')[0].text.split(":")[1::]).strip()
    nquestion.answer = ''.join(soup.find_all(class_='question')[i].find_all('p')[1].text.split(":")[1::]).strip()

    db_sess.add(nquestion)

db_sess.commit()