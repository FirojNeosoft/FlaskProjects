from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Teachers(db.Model):
    __tablename__ = 'teachers'

    id = db.Column('teacher_id', db.Integer, primary_key = True)
    name = db.Column(db.String(100))
    gender = db.Column(db.String(1))  
    address = db.Column(db.String(200))
    email = db.Column(db.String(100))
    age = db.Column(db.Integer)
    lang = db.Column(db.String(3))

    def __init__(self, name, gender, address, email, age, lang):
        self.name = name
        self.gender = gender
        self.address = address
        self.email = email
        self.age = age
        self.lang = lang

    def __repr__(self):
        return '%s(%s)'.format(self.name, self.lang)
