import datetime
import sqlalchemy
from sqlalchemy import orm
from .db_session import SqlAlchemyBase


class Question(SqlAlchemyBase):
    __tablename__ = 'questions'

    id = sqlalchemy.Column(sqlalchemy.Integer,
                           primary_key=True, autoincrement=True)
    autor = sqlalchemy.Column(sqlalchemy.Integer,
                                    sqlalchemy.ForeignKey("users.id"))
    question = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    answer = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    is_private = sqlalchemy.Column(sqlalchemy.Boolean, default=False)
    create_date = sqlalchemy.Column(sqlalchemy.DateTime, default=datetime.datetime.now)
    path_to_file = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    content_type = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    content_len = sqlalchemy.Column(sqlalchemy.Integer, nullable=True, default=0)
    user = orm.relation('User')

    def __repr__(self):
        return "<Question> " + str(self.question) + " " + str(self.answer) + " " + str(self.create_date)