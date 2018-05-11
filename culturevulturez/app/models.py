
from flask_login import UserMixin
from sqlalchemy.engine import default

from app import db, login_manager
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from flask import current_app
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, date


# Set website access permissions
class Permission:
    FOLLOW = 0x01
    COMMENT = 0x02
    WRITE_ARTICLES = 0x04
    MODERATE_COMMENTS = 0x08
    ADMINISTER = 0x80


# User roles
class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    default = db.Column(db.Boolean, default=False, index=True)
    permissions = db.Column(db.Integer)
    users = db.relationship('User', backref='role', lazy='dynamic')

    # Crete roles in the db
    @staticmethod
    def insert_roles():
        roles = {
            'User': (Permission.FOLLOW |
                     Permission.COMMENT |
                     Permission.WRITE_ARTICLES, True),
            'Moderator': (Permission.FOLLOW |
                          Permission.COMMENT |
                          Permission.WRITE_ARTICLES |
                          Permission.MODERATE_COMMENTS, False),
            'Administrator': (0xff, False)
        }

        for r in roles:
            role = Role.query.filter_by(name=r).first()
            if role is None:
                role = Role(name=r)
            role.permissions = roles[r][0]
            role.default = roles[r][1]
            db.session.add(role)
        db.session.commit()

    def __repr__(self):
        return '<Role %r>' % self.name


# Follows association table
class Follow(db.Model):
    __tablename__ = 'follows'
    follower_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    followed_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)


# Users table
class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key= True, autoincrement=True)
    first_name = db.Column(db.String(64))
    last_name = db.Column(db.String(64))
    dob = db.Column(db.Date)
    gender = db.Column(db.String(64))
    nationality = db.Column(db.String(64))
    residence = db.Column(db.String(64))
    postal_code = db.Column(db.String(64))
    username = db.Column(db.String(64), unique=True)
    email = db.Column(db.String(64), unique=True)
    password_hash = db.Column(db.String(128))
    member_since = db.Column(db.DateTime(), default=datetime.utcnow)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))
    confirmed = db.Column(db.Boolean, default=False)
    location = db.Column(db.String(64))
    about_me = db.Column(db.Text())
    last_seen = db.Column(db.DateTime(), default=datetime.utcnow)
    bio = db.Column(db.String(100))
    profile_pic = db.Column(db.String, default=None)
    posts = db.relationship('Post', backref='author', lazy='dynamic')
    followed = db.relationship('Follow', foreign_keys=[Follow.follower_id], backref=db.backref('follower', lazy='joined'),
                               lazy='dynamic', cascade='all, delete-orphan')
    followers = db.relationship('Follow', foreign_keys=[Follow.followed_id], backref=db.backref('followed', lazy='joined'),
                                lazy='dynamic', cascade='all, delete-orphan')
    comments = db.relationship('Comment', backref='author', lazy='dynamic')
    interests = db.Column(db.String())
    post_likes = db.relationship('PostLikes', backref=db.backref('user', lazy='joined'),
                                 lazy='dynamic', cascade='all, delete-orphan')
    comment_likes = db.relationship('CommentLikes', backref=db.backref('user', lazy='joined'),
                                 lazy='dynamic', cascade='all, delete-orphan')



    # Define default role for users
    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)
        if self.role is None:
            if self.email == 'hardingalex@live.com':
                self.role = Role.query.filter_by(permissions=0xff).first()
            if self.role is None:
                self.role = Role.query.filter_by(default=True).first()


    # User account confirmation
    def generate_confirmation_token(self, expiration=86400):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'confirm': self.id})

    def confirm(self, token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return False
        if data.get('confirm') != self.id:
            return False
        self.confirmed = True
        db.session.add(self)
        return True

    # Password hashing and verification
    @property
    def password(self):
        raise AttributeError('Password is not a readable attribute')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    # Load and remember logged in user
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Evaluate whether a user has a given permission
    def can(self, permissions):
        return self.role is not None and (self.role.permissions & permissions) == permissions

    def is_administrator(self):
        return self.can(Permission.ADMINISTER)

    #Refresh users last visit
    def ping(self):
        self.last_seen = datetime.utcnow()
        db.session.add(self)

    #Connection helper methods
    def follow(self, user):
        if not self.is_following(user):
            f = Follow(follower=self, followed=user)
            db.session.add(f)

    def unfollow(self, user):
        f = self.followed.filter_by(followed_id=user.id).first()
        if f:
            db.session.delete(f)

    def is_following(self, user):
        return self.followed.filter_by(followed_id=user.id).first() is not None

    def is_followed_by(self, user):
        return self.followers.filter_by(follower_id=user.id).first() is not None

    #get followed posts
    @property
    def followed_posts(self):
        return Post.query.join(Follow, Follow.followed_id == Post.author_id).filter(Follow.follower_id == self.id)

    #Post likes helper methods
    def like_post(self, post):
        if not self.is_liking_post(post):
            p = PostLikes(user=self, post=post)
            db.session.add(p)

    def unlike_post(self, post):
        p = self.post_likes.filter_by(post_id=post.id).first()
        if p:
            db.session.delete(p)

    def is_liking_post(self, post):
        return self.post_likes.filter_by(post_id=post.id).first() is not None


    #Comment Likes helper methods

    def like_comment(self, comment):
        if not self.is_liking_comment(comment):
            c = CommentLikes(user=self, comment=comment)
            db.session.add(c)

    def unlike_comment(self, comment):
        c = self.comment_likes.filter_by(comment_id=comment.id).first()
        if c:
            db.session.delete(c)

    def is_liking_comment(self, comment):
        return self.comment_likes.filter_by(comment_id=comment.id).first() is not None


class Post(db.Model):
    __tablename__ = 'posts'
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.Text())
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    comments = db.relationship('Comment', backref='post', lazy='dynamic')
    user_likes = db.relationship('PostLikes', backref=db.backref('post', lazy='joined'),
                                 lazy='dynamic', cascade='all, delete-orphan')
    photo = db.Column(db.String, default=None)
    photo_url = db.Column(db.String, default=None)
    video_url = db.Column(db.String, default=None)
    about_text = db.Column(db.Text(), default=None)


#comments model
class Comment(db.Model):
    __tablename__ = 'comments'
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.Text)
    timestamp = db.Column(db.DateTime,index=True, default=datetime.utcnow)
    disabled = db.Column(db.Boolean)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'))
    user_likes = db.relationship('CommentLikes', backref=db.backref('comment', lazy='joined'),
                                 lazy='dynamic', cascade='all, delete-orphan')


class PostLikes(db.Model):
    __tablename = 'post_likes'
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'), primary_key=True)
    timestamp = db.Column(db.DateTime,index=True, default=datetime.utcnow)

class CommentLikes(db.Model):
    __tablename = 'comment_likes'
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    comment_id = db.Column(db.Integer, db.ForeignKey('comments.id'), primary_key=True)
    timestamp = db.Column(db.DateTime,index=True, default=datetime.utcnow)
