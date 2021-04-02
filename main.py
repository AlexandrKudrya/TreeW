import random

from flask import Flask, render_template, redirect, make_response
from flask_login import login_user, current_user, LoginManager
from flask_wtf import FlaskForm
from wtforms import PasswordField, BooleanField, SubmitField, StringField, IntegerField, FieldList
from wtforms.fields.html5 import EmailField
from wtforms.validators import DataRequired
import datetime
from data import db_session
from data import users, question, game

app = Flask(__name__)
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'
db_session.global_init("db/3W.sqlite")
login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    return db_sess.query(users.User).get(user_id)


@app.route("/")
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
        ngame.questions_id = ";".join([str(random.randint(1, len(db_sess.query(question.Question).all())))
                                          for i in range(form.num_questions.data)])
        ngame.key = ''.join(str(random.randint(1, 150)) for i in range(10))
        db_sess.add(ngame)

        db_sess.commit()
        res = make_response(render_template("start_game.html", title="Главная Страница"))
        res.set_cookie("visits_count", ngame.key,
                       max_age=60 * 60 * 24)
        return res
    return render_template('create_game.html', title='Создание комнаты', form=form)


@app.route('/game', methods=['GET', 'POST'])
def create_game():

    return render_template('create_game.html', title='Создание комнаты', form=form)


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


if __name__ == '__main__':
    db_sess = db_session.create_session()
    app.run(port=8080, host='127.0.0.1')