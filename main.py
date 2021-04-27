import datetime
import json
import random
from collections import namedtuple

from flask import Flask, render_template, redirect, make_response, request
from flask_login import login_user, current_user, LoginManager, login_required, logout_user
from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed
from wtforms import PasswordField, BooleanField, SubmitField, StringField, IntegerField, FieldList, FormField, FileField
from wtforms.fields.html5 import EmailField
from wtforms.validators import DataRequired
from PIL import Image
from tinytag import TinyTag

from data import db_session
from data import users, question, game


app = Flask(__name__)
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'
db_session.global_init("db/3W.sqlite")
login_manager = LoginManager()
login_manager.init_app(app)


def get_content_len(filename):
    tag = TinyTag.get(filename)
    return int(tag.duration)


@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    return db_sess.query(users.User).get(user_id)


@app.route("/", methods=['GET', 'POST'])
def index():
    arr_of_opened_games = list(db_sess.query(game.Game).all())
    random.shuffle(arr_of_opened_games)

    raiting = list(db_sess.query(users.User).order_by(users.User.points))[::-1]
    raiting = raiting[:max(10, len(raiting) - 1)]

    return render_template("base.html", title="Главная Страница",
                           arr_of_opened_games=arr_of_opened_games[:max(10, len(arr_of_opened_games) - 1)],
                           raiting=raiting)


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

        photo = form.image.data
        if photo.filename.split('.')[-1] in ['jpg', 'png']:
            print(photo)
            filename = 'static/img/questions/' + str(len(db_sess.query(question.Question).all())) \
                       + '.' + photo.filename.split('.')[-1]
            photo.save(filename)
            image = Image.open(filename)
            new_image = image.resize((600, 600))
            new_image.save(filename)

            nquestion.path_to_file = filename
            nquestion.content_type = 'image'
            nquestion.content_len = 0
            db_sess.add(nquestion)

            db_sess.commit()
            return redirect("/")
        elif photo.filename.split('.')[-1] in ['mp4']:
            print(photo)
            filename = 'static/img/questions/' + str(len(db_sess.query(question.Question).all())) \
                       + '.' + photo.filename.split('.')[-1]
            photo.save(filename)

            nquestion.path_to_file = filename
            nquestion.content_type = 'mp4'
            nquestion.content_len = get_content_len(filename)
            db_sess.add(nquestion)

            db_sess.commit()
            return redirect("/")
        elif photo.filename.split('.')[-1] in ['mp3']:
            print(photo)
            filename = 'static/img/questions/' + str(len(db_sess.query(question.Question).all())) \
                       + '.' + photo.filename.split('.')[-1]
            photo.save(filename)

            nquestion.path_to_file = filename
            nquestion.content_type = 'mp3'
            nquestion.content_len = get_content_len(filename)
            db_sess.add(nquestion)

            db_sess.commit()
            return redirect("/")
        elif not(photo):
            db_sess.commit()
            return redirect("/")
        return render_template('create_question.html', title='Регистрация', form=form, erore='Поддерживаются только '
                                                                                             'файлы .jpg, .png, .mp3, '
                                                                                             '.mp4')
    return render_template('create_question.html', title='Регистрация', form=form, erore='')


@app.route('/create_game', methods=['GET', 'POST'])
def create_game():
    form = GameForm()
    print(form.validate_on_submit())
    db_sess = db_session.create_session()
    max_arr = len(db_sess.query(question.Question).all())
    if request.method == 'POST':
        ngame = game.Game()
        ngame.admin = current_user.id
        ngame.title = form.title.data
        arr = [str(i) for i in range(1, len(db_sess.query(question.Question).all()) + 1)]
        random.shuffle(arr)
        ngame.questions_id = form.by_id_form.data
        ngame.key = str(len(db_sess.query(game.Game).all()) + 1)
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
    return render_template('create_game.html', title='Создание комнаты', form=form, max_arr=max_arr)


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
            res.set_cookie('game_key', form.key.data, max_age=60 * 60 * 24)
            return res
    return render_template('choice_game.html', title='Создание комнаты', form=form)


@app.route('/newgame', methods=['GET', 'POST'])
def newgame():
    form = AnswerForm()
    key = str(request.cookies.get("game_key", ''))
    print(key)
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        current_game = db_sess.query(game.Game).filter(game.Game.key == key).first()
        print(current_game.questions_id)
        try:
            pos = int(request.cookies.get("pos", 0))
        except ValueError:
            res = make_response(redirect('/newgame'))
            res.set_cookie('pos', '0', max_age=0)
            return res
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
            data['data'][str(current_user.id)] = data['data'].get(str(current_user.id), []) + [
                [qust.answer, form.answer.data, qust.question]]
            # Тест, что вообще такое есть
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
        try:
            pos = int(request.cookies.get("pos", 0))
        except ValueError:
            res = make_response(redirect('/newgame'))
            res.set_cookie('pos', '0', max_age=0)
            return res
        try:
            qust_id = int(current_game.questions_id.split(';')[pos])
            qust = db_sess.query(question.Question).filter(question.Question.id == qust_id).first()
            print(qust.path_to_file)
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
        db_sess.query(question.Question).filter(question.Question.id == qust_id).first().answer
        for qust_id in cgame.questions_id.split(';')
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
    if request.method == 'POST':
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


@app.route('/points', methods=['GET', 'POST'])
def points():
    form = BuyForm()
    if request.method == 'POST':
        db_sess = db_session.create_session()
        user = db_sess.query(users.User).filter(users.User.id == current_user.id).first()
        print(current_user.points)
        user.points -= 1000
        print(current_user.points)
        user.plus_ruls = True
        db_sess.commit()
        print(current_user.points)
        return redirect('/')
    elif current_user.points < 1000 and not(current_user.plus_ruls):
        return render_template('points_false.html', title='Создание комнаты', msg='Возвращайся, когда у тебя будет больше 1000 очков')
    elif current_user.plus_ruls:
        return render_template('points_false.html', title='Создание комнаты', msg='Ты уже купил дополнительные права')
    return render_template('points_true.html', title='Создание комнаты', form=form)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect("/")


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
    image = FileField(FileAllowed(['jpg', 'png'], 'Images only!'))
    create = SubmitField('Создать')


class GameForm(FlaskForm):
    title = StringField('Тема', validators=[DataRequired()])
    num_questions = IntegerField('Количество Вопросов', validators=[DataRequired()])
    by_id_form = StringField('Впишите сюда номера вопросов через ";"', validators=[DataRequired()])
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


class BuyForm(FlaskForm):
    buy = SubmitField('Купить дополнительные права')


if __name__ == '__main__':
    db_sess = db_session.create_session()
    app.run(port=8080, host='127.0.0.1')
