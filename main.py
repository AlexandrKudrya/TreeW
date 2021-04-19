import random

import flask.views
from flask import Flask, render_template, redirect, make_response, request, sessions, url_for
from flask_login import login_user, current_user, LoginManager
from flask_wtf import FlaskForm
from wtforms import PasswordField, BooleanField, SubmitField, StringField, IntegerField, FieldList, FormField
from wtforms.fields.html5 import EmailField
from wtforms.validators import DataRequired
import datetime
from data import db_session
from data import users, question, game
import json
from collections import namedtuple

app = Flask(__name__)
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'
db_session.global_init("db/3W.sqlite")
login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    return db_sess.query(users.User).get(user_id)


@app.route("/", methods=['GET', 'POST'])
def index():
    return render_template("base.html", title="Главная Страница")


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        user = db_sess.query(users.User).filter(users.User.email == form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            return redirect("/")
        return render_template('login.html',
                               message="Неправильный логин или пароль",
                               form=form)
    return render_template('login.html', title='Авторизация', form=form)


@app.route('/reg', methods=['GET', 'POST'])
def reg():
    form = RegForm()
    print(form.validate_on_submit())
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        nuser = users.User()
        nuser.name = form.login.data
        nuser.email = form.email.data
        nuser.hashed_password = form.password.data
        nuser.modifed_date = datetime.datetime.now()
        print(nuser)
        if form.password.data == form.password_submit.data:
            db_sess.add(nuser)

            db_sess.commit()
            return redirect("/")
        return render_template('reg.html',
                               message="Пароли не совпадают",
                               form=form)
    return render_template('reg.html', title='Регистрация', form=form)


@app.route('/create_question', methods=['GET', 'POST'])
def create_question():
    form = QuestionForm()
    print(form.validate_on_submit())
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        nquestion = question.Question()
        nquestion.autor = current_user.id
        nquestion.question = form.question.data
        nquestion.answer = form.answer.data

        db_sess.add(nquestion)

        db_sess.commit()
        return redirect("/")
    return render_template('create_question.html', title='Регистрация', form=form)


@app.route('/create_game', methods=['GET', 'POST'])
def create_game():
    form = GameForm()
    print(form.validate_on_submit())
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        ngame = game.Game()
        ngame.admin = current_user.id
        ngame.title = form.title.data
        arr = [str(i) for i in range(1, len(db_sess.query(question.Question).all()) + 1)]
        random.shuffle(arr)
        ngame.questions_id = ";".join(arr[:int(form.num_questions.data)])
        ngame.key = ''.join(str(random.randint(1, 150)) for i in range(10))
        db_sess.add(ngame)
        game_data = {'data': {}, 'points': {}}
        with open(f'game_logs/{ngame.key}.json', 'w') as cat_file:
            json.dump(game_data, cat_file)
        db_sess.commit()
        res = make_response(render_template("start_game.html", title="Главная Страница", key=ngame.key))
        res.set_cookie("game_key", ngame.key,
                       max_age=60 * 60 * 24)
        res.set_cookie("pos", '0',
                       max_age=60 * 60 * 24)
        res.set_cookie("score", '0',
                       max_age=60 * 60 * 24)
        return res
    return render_template('create_game.html', title='Создание комнаты', form=form)



@app.route('/choice_game', methods=['GET', 'POST'])
def choice_game():
    form = ChoiceForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        current_game = db_sess.query(game.Game).filter(game.Game.key == form.key.data).first()
        if current_game:
            res = make_response(redirect('/newgame'))
            res.set_cookie("pos", str(1),
                           max_age=60 * 60 * 24)
            res.set_cookie('game_key', form.key.data, max_age=60*60*24)
            return res
    return render_template('choice_game.html', title='Создание комнаты', form=form)


@app.route('/newgame', methods=['GET', 'POST'])
def newgame():
    form = AnswerForm()
    key = str(request.cookies.get("game_key", ''))
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        current_game = db_sess.query(game.Game).filter(game.Game.key == key).first()
        print(current_game.questions_id)
        pos = int(request.cookies.get("pos", 0))
        try:
            qust_id = current_game.questions_id.split(';')[pos]
            qust = db_sess.query(question.Question).filter(question.Question.id == qust_id).first()
            res = make_response(render_template('game.html', title='Создание комнаты', qust=qust, form=form))
            res.set_cookie("pos", str(pos + 1),
                           max_age=60 * 60 * 24)
            if form.answer.data.lower() == qust.answer.lower():
                res.set_cookie('score', str(int(request.cookies.get("score", 0)) + 1), max_age=60 * 60 * 24)
            with open(f'game_logs/{current_game.key}.json', 'r') as cat_file:
                data = json.load(cat_file)
            data['data'][str(current_user.id)] = data['data'].get(str(current_user.id), []) + [[qust.answer, form.answer.data, qust.question]]
            try:
                k = data['points'][str(current_user.id)]
            except KeyError:
                data['points'][str(current_user.id)] = 0
            print(data)
            with open(f'game_logs/{current_game.key}.json', 'w') as cat_file:
                json.dump(data, cat_file, ensure_ascii=False)
            return res
        except IndexError:
            return redirect('/')
    elif len(key) > 0:
        db_sess = db_session.create_session()
        current_game = db_sess.query(game.Game).filter(game.Game.key == key).first()
        pos = int(request.cookies.get("pos", 0))
        try:
            qust_id = int(current_game.questions_id.split(';')[pos])
            qust = db_sess.query(question.Question).filter(question.Question.id == qust_id).first()
            print(qust)
            res = make_response(render_template('game.html', title='Создание комнаты', qust=qust, form=form))
            return res
        except IndexError:
            res = make_response(redirect('/'))
            res.set_cookie('score', '', max_age=0)
            res.set_cookie('pos', '', max_age=0)
            res.set_cookie('game_key', '', max_age=0)
            return res
    else:
        return redirect("/create_game")


@app.route('/check_my_games', methods=['GET', 'POST'])
def check_my_games():
    current_games = list(db_sess.query(game.Game).filter(game.Game.admin == current_user.id))
    return render_template('check_my_games.html', arr=current_games)


@app.route('/check_my_game/<gameid>', methods=['GET', 'POST'])
def check_my_game(gameid):
    db_sess = db_session.create_session()
    cgame = db_sess.query(game.Game).filter(game.Game.id == int(gameid)).first()
    with open(f'game_logs/{cgame.key}.json', 'r') as cat_file:
        data = json.load(cat_file)
    arr_of_answ = data['data']
    arr_of_normal_answers = [
        db_sess.query(question.Question).filter(question.Question.id == id).first().answer
        for id in cgame.questions_id.split(';')
    ]
    product = namedtuple('Product', ['yes'])

    fdata = {
        'save': 'Widgets',
        'products': [
            product(data['points'][str(i)])
            for i in list(arr_of_answ.keys())
        ]
    }
    form = SaveForm(data=fdata)
    if str(request).split()[-1][:-1] == '[POST]':
        for i in range(len(list(arr_of_answ.keys()))):
            user = db_sess.query(users.User).filter(users.User.id == int(list(arr_of_answ.keys())[i])).first()
            print(user)
            user.points += int(form.products[i].yes.data) - data['points'][str(list(arr_of_answ.keys())[i])]
            print(data)
            data['points'][str(user.id)] = int(form.products[i].yes.data)
        db_sess.commit()
        with open(f'game_logs/{cgame.key}.json', 'w') as cat_file:
            json.dump(data, cat_file, ensure_ascii=False)
        return render_template('check_my_game.html', arr_of_answ=arr_of_answ,
                                   arr_of_normal_answers=arr_of_normal_answers,
                                   users_id=arr_of_answ.keys(),
                                   form=form)
    return render_template('check_my_game.html', arr_of_answ=arr_of_answ,
                                                 arr_of_normal_answers=arr_of_normal_answers,
                                                 users_id=arr_of_answ.keys(),
                                                 form=form)


@app.route('/admin', methods=['GET', 'POST'])
def admin():
    return 'я сделаль, потом доделаю'


class LoginForm(FlaskForm):
    email = EmailField('Почта', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    remember_me = BooleanField('Запомнить меня')
    submit = SubmitField('Войти')


class RegForm(FlaskForm):
    email = EmailField('Почта', validators=[DataRequired()])
    login = StringField('Логин', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    password_submit = PasswordField('Подтрердите Пароль')
    submit = SubmitField('Зарегистрироваться')


class QuestionForm(FlaskForm):
    question = StringField('Вопрос', validators=[DataRequired()])
    answer = StringField('Ответ', validators=[DataRequired()])
    is_private = BooleanField('Приватный?')
    create = SubmitField('Создать')


class GameForm(FlaskForm):
    title = StringField('Тема', validators=[DataRequired()])
    num_questions = IntegerField('Количество Вопросов', validators=[DataRequired()])
    is_private = BooleanField('Приватный?')
    create = SubmitField('Создать')


class AnswerForm(FlaskForm):
    answer = StringField('Ответ', validators=[DataRequired()])
    create = SubmitField('Подтвердить')


class ChoiceForm(FlaskForm):
    key = StringField('Ключ Игры', validators=[DataRequired()])
    create = SubmitField('Подтвердить')


class Cheking_Form(FlaskForm):
    yes = IntegerField('Счёт')


class SaveForm(FlaskForm):
    products = FieldList(FormField(Cheking_Form), min_entries=1, max_entries=9999)
    save = SubmitField('Сохранить')


if __name__ == '__main__':
    db_sess = db_session.create_session()
    app.run(port=8080, host='127.0.0.1')