from flask import Flask
from flask_bootstrap import Bootstrap
from flask_mail import Mail
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from config import config
from flask_uploads import UploadSet, IMAGES, configure_uploads

app = Flask(__name__)
bootstrap = Bootstrap()
mail = Mail()
moment = Moment()
db = SQLAlchemy()

# manage login and protect user with strong session protection
login_manager = LoginManager()
login_manager.session_protection = 'strong'
login_manager.login_view = 'auth.login'

# Configure image upload with flask upload
images = UploadSet('images', IMAGES)
app.config['UPLOADED_IMAGES_DEST'] = 'app/static/images/'
app.config['UPLOADED_IMAGES_URL'] = 'http://127.0.0.1:5000/static/images/'
configure_uploads(app, images)


def create_app(config_name):
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)

    bootstrap.init_app(app)
    mail.init_app(app)
    moment.init_app(app)
    login_manager.init_app(app)
    db.init_app(app)

    from .main import main as main_blueprint
    app.register_blueprint(main_blueprint)

    from .auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint)

    return app
