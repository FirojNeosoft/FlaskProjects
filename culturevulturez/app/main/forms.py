from xml.dom import ValidationErr

from flask_admin.contrib.sqla import validators
from flask_wtf.form import FlaskForm
from flask_wtf.recaptcha import validators
from wtforms import widgets, StringField, PasswordField, BooleanField, SubmitField, SelectField, DateField, TextAreaField, SelectMultipleField
from wtforms.validators import DataRequired, Length, Email, Regexp, Optional
from wtforms import ValidationError
from flask_wtf.file  import FileAllowed, FileField, FileRequired
from flask_login import current_user
from ..models import User, Role
from app import images
from markupsafe import Markup
import pycountry


class MultiCheckboxField(SelectMultipleField):
    widget = widgets.ListWidget(prefix_label=False)
    option_widget = widgets.CheckboxInput()


#Regular user info editing form
class EditInfoForm(FlaskForm):
    profile_pic = FileField('Profile Picture', validators=[Optional(), FileAllowed(images, 'Images only!')])
    first_name = StringField('First Name', validators=[Length(0, 64)])
    last_name = StringField('Last Name', validators=[Length(0, 64)])
    dob = DateField('Date of Birth')
    gender = SelectField('Gender', choices=[('Male', 'Male'),('Female', 'Female'), ('other', 'Other')])
    nationality = SelectField('Nationality', choices=[(country.name, country.name) for country in pycountry.countries])
    residence = SelectField('Residence', choices=[(country.name, country.name) for country in pycountry.countries])
    postal_code = StringField('Postal Code or City')
    email = StringField('Email', validators=[Email()])
    bio = StringField('Short Self Description', validators=[Length(0, 100)])
    about_me = TextAreaField('About Me')
    submit = SubmitField('Update Profile')

    def validate_email(self, field):
        if field.data != current_user.email and User.query.filter_by(email=field.data).first():
            raise ValidationError('Email already in use')


#Admin level user info editing
class AdminUserInfoEditForm(FlaskForm):
    first_name = StringField('First Name', validators=[DataRequired(), Length(1, 64)])
    last_name = StringField('Last Name', validators=[DataRequired(), Length(1, 64)])
    dob = DateField('Date of Birth', validators=[DataRequired()])
    gender = SelectField('Gender', choices=[('Male', 'Male'),('Female', 'Female'), ('other', 'Other')], validators=[DataRequired()])
    nationality = SelectField('Nationality', choices=[(country.alpha_2, country.name) for country in pycountry.countries], validators=[DataRequired()])
    residence = SelectField('Residence', choices=[(country.alpha_2, country.name) for country in pycountry.countries], validators=[DataRequired()])
    postal_code = StringField('Postal Code', validators=[DataRequired()])
    username = StringField('Username', validators=[DataRequired(), Length(1, 64), Regexp('^[A-Za-z][A-Za-z0-9_.]*$', 0, 'Username must only have letters,''numbers, dots or underscores')])
    email = StringField('Email', validators=[DataRequired(), Email()])
    about_me = TextAreaField('About Me')
    confirmed = BooleanField('Confirmed')
    role = SelectField('Role', coerce=int)
    submit = SubmitField('Update Profile')

    #Enable Admin role change for users
    def __init__(self, user, *args, **kwargs):
        super(AdminUserInfoEditForm, self).__init__(*args, **kwargs)
        self.role.choices = [(role.id, role.name)
                             for role in Role.query.order_by(Role.name).all()]
        self.user = user

    #validate changed email
    def validate_email(self, field):
        if field.data != self.user.email and User.query.filter_by(email=field.data).first():
            raise ValidationError('Email already in use')

    #Validate changed username
    def validate_username(self,field):
        if field.data != self.user.username and User.query.filter_by(username=field.data).first():
            raise ValidationError('Username already in use')

photo_value = Markup('<span class="icon icon-camera"></span>')

class PostForm(FlaskForm):
    body = TextAreaField("What's on your mind about culture?", validators =[DataRequired()])
    photo = FileField('Photo',  validators=[Optional(), FileAllowed(images, 'Images only!')])
    submit = SubmitField('Post')

class CommentForm(FlaskForm):
    body = TextAreaField('', validators=[DataRequired()])
    submit = SubmitField('Comment')

class SettingsForm(FlaskForm):
    profile_pic = FileField('Profile Picture', validators=[Optional()])
    nationality = SelectField('Nationality', choices=[(country.name, country.name) for country in pycountry.countries])
    residence = SelectField('Resident Country', choices=[(country.name, country.name) for country in pycountry.countries])
    postal_code = StringField('City, Zip or Postal Code')
    bio = StringField('Short Self Description', validators=[Length(0, 100)])
    about_me = TextAreaField('About Me')
    interests = MultiCheckboxField('What are your cultural interests', choices=[('Automobile', 'Automobile'), ('Business', 'Business'),
                                                                                 ('Charity', 'Charity'), ('Clothing','Clothing'),
                                                                                 ('Dance', 'Dance'), ('Education', 'Education'),
                                                                                 ('Entertainment', 'Entertainment'), ('Environment', 'Environment'),
                                                                                 ('Food', 'Food'), ('Fun','Fun'),
                                                                                 ('Government', 'Government'), ('History', 'History'),
                                                                                 ('Language', 'Language'), ('Law', 'Law'),
                                                                                 ('Lifestyle', 'Lifestyle'), ('Literature', 'Literature'),
                                                                                 ('Music', 'Music'), ('News', 'News'),
                                                                                 ('Night Life', 'Night Life'), ('Performing Arts', 'Performing Arts'),
                                                                                 ('Poetry', 'Poetry'), ('Politics', 'Politics'),
                                                                                 ('Religion', 'Religion'), ('Science', 'Science'),
                                                                                 ('Social', 'Social'), ('Sports', 'Sports'),
                                                                                 ('Technology', 'Technology'), ('Visual Arts', 'Visual Arts')],
                                    validators=[DataRequired()])
    submit = SubmitField("Let's go!")
