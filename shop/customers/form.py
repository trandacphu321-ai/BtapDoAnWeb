# -*- coding: utf-8 -*-

from flask_wtf import FlaskForm
from wtforms import (
    StringField,
    PasswordField,
    RadioField,
    SubmitField,
    validators,
    ValidationError
)
from wtforms.validators import DataRequired, Email, Length
from shop.customers.models import Register
import phonenumbers


# ------------------- USER REGISTRATION FORM -------------------
class RegistrationForm(FlaskForm):
    name = StringField('Name', [
        validators.Length(min=4, max=25),
        validators.DataRequired()
    ])
    username = StringField('Username', [
        validators.Length(min=4, max=25),
        validators.DataRequired()
    ])
    email = StringField('Email Address', [
        validators.Length(min=6, max=35),
        validators.Email(),
        validators.DataRequired()
    ])
    password = PasswordField('Password', [
        validators.DataRequired(),
        validators.EqualTo('confirm', message='Passwords must match')
    ])
    confirm = PasswordField('Repeat Password', [
        validators.DataRequired()
    ])


# ------------------- ADMIN LOGIN FORM -------------------
class LoginForm(FlaskForm):
    email = StringField('Email Address', [
        validators.Email(),
        validators.DataRequired()
    ])
    password = PasswordField('Password', [
        validators.DataRequired()
    ])


# ------------------- CUSTOMER REGISTER FORM -------------------
class CustomerRegisterForm(FlaskForm):
    username = StringField('Username: ', [
        validators.DataRequired(),
        validators.Length(min=4, max=20)
    ])
    first_name = StringField('Fist Name: ')
    last_name = StringField('Last Name: ')
    email = StringField('Email: ', [
        validators.Email(),
        validators.DataRequired()
    ])
    phone_number = StringField('Phone: ', [
        validators.DataRequired()
    ])
    gender = RadioField('Gender:', default='M',
                        choices=[('M', 'Male'), ('F', 'Female')])
    password = PasswordField('Password: ', [
        validators.DataRequired(),
        validators.EqualTo('confirm', message=' Both password must match! ')
    ])
    confirm = PasswordField('Repeat Password: ', [
        validators.DataRequired()
    ])
    submit = SubmitField('Register')

    def validate_username(self, username):
        if Register.objects(username=username.data).first():
            raise ValidationError("This username is already in use!")

    def validate_email(self, email):
        if Register.objects(email=email.data).first():
            raise ValidationError("This email address is already in use!")

    def validate_phone_number(self, phone_number):
        if Register.objects(phone_number=phone_number.data).first():
            raise ValidationError("This phone number is already in use!")
        try:
            input_number = phonenumbers.parse(phone_number.data)
            if not phonenumbers.is_valid_number(input_number):
                raise ValidationError('Invalid phone number.')
        except Exception:
            input_number = phonenumbers.parse("+84" + phone_number.data)
            if not phonenumbers.is_valid_number(input_number):
                raise ValidationError('Invalid phone number.')


# ------------------- CUSTOMER LOGIN FORM (MỚI THÊM) -------------------
# class CustomerLoginForm(FlaskForm):
#     email = StringField("Email", validators=[
#         DataRequired(),
#         Email()
#     ])
#     password = PasswordField("Password", validators=[
#         DataRequired()
#     ])
#     submit = SubmitField("Login")
    # FILE: shop/customers/form.py

class CustomerLoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Login")

# Kết thúc bổ sung user