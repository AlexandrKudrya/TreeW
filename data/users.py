import datetime
import sqlalchemy
from .db_session import SqlAlchemyBase
from flask_login import UserMixin


class User(SqlAlchemyBase, UserMixin):
    __tablename__ = 'users'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    name = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    email = sqlalchemy.Column(sqlalchemy.String, index=True, unique=True, nullable=True)
    hashed_password = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    modifed_date = sqlalchemy.Column(sqlalchemy.DateTime, default=datetime.datetime.now)


    def __repr__(self):
            return "<User> " + str(self.name) + " " + str(self.modifed_date)

    def check_password(self, pass2check):
        return self.hashed_password == pass2check