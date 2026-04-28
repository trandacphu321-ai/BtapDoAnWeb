from shop import db


class Admin(db.Document):
    name = db.StringField(max_length=50, required=True)
    username = db.StringField(max_length=80, unique=True, required=True)
    email = db.StringField(max_length=120, unique=True, required=True)
    password = db.StringField(max_length=180, required=True)
    profile = db.StringField(max_length=180, required=True, default='profile.jpg')

    meta = {'collection': 'admin'}

    def __repr__(self):
        return '<User %r>' % self.username
