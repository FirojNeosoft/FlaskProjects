from flask_wtf import Form
from wtforms import StringField, IntegerField, TextAreaField, SubmitField, RadioField,SelectField

from wtforms import validators


class TeacherForm(Form):
   name = StringField("Name Of Teacher",[validators.DataRequired("Please enter name.")])
   gender = RadioField('Gender', choices = [('M','Male'),('F','Female')])
   address = TextAreaField("address")
   
   email = StringField("Email",[validators.DataRequired("Please enter your email address."),
   validators.Email("Please enter your email address.")])
   
   age = IntegerField("Age")
   lang = SelectField('Language', choices = [('cpp', 'C++'), ('py', 'Python')])
   submit = SubmitField("Save")
