'''Formularios web'''
import os
import sys

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, IntegerField, TextAreaField, SelectField
from wtforms.validators import DataRequired, Email, NumberRange

sys.path.append(os.path.dirname(os.path.realpath(__file__)) + '/../')
from ipmon import config


class FirstTimeSetupForm(FlaskForm):
    password_policy = 'Política de contraseña: longitud mínima ({}), letras mayúscula  mínimas ({}), números mínimos ({}).'.format(
        config['Password_Policy']['Length'],
        config['Password_Policy']['Uppercase'],
        config['Password_Policy']['Nonletters']
    )
    username = StringField('Nombre de Usuario', validators=[DataRequired(message="Nombre de Usuario requerido")])
    email = StringField('Email', validators=[DataRequired(message="Email requerido"), Email(message="Invalid email address")])
    password = PasswordField('Contraseña', description=password_policy, validators=[DataRequired(message="Contraseña requerida")])
    verify_password = PasswordField('Confirmar Contraseña', validators=[DataRequired(message="Verificación contraseña  requerida")])
    poll_interval = IntegerField('Intervalo de consultas (segundos)', validators=[DataRequired(message="Intervalo de consultas requerido")])
    retention_days = IntegerField('Tiempo de almacenamiento de información (Días)', validators=[DataRequired(message="Tiempo de almacenamiento requerido")])
    enable_smtp = BooleanField('Enable SMTP Alerts')
    smtp_server = StringField('Servidor')
    smtp_port = StringField('Puerto')
    smtp_sender = StringField('Correo del remitente')
    smtp_user = StringField('Usuario SMTP')
    smtp_password = PasswordField('Contraseña SMTP')
    submit = SubmitField('Enviar')


class LoginForm(FlaskForm):
    username = StringField('Nombre de Usuario', validators=[DataRequired(message="Nombre de Usuario requerido")])
    password = PasswordField('Contraseña', validators=[DataRequired(message="Contraseña requerida")])
    remember_me = BooleanField('Recuerdame')
    submit = SubmitField('Iniciar Sesión')


class UpdatePasswordForm(FlaskForm):
    desc = 'Politica de contraseña: longitud mínima ({}), mínimo letras mayúsculas minúsculas ({}), mínimo de números ({}).'.format(
        config['Password_Policy']['Length'],
        config['Password_Policy']['Uppercase'],
        config['Password_Policy']['Nonletters']
    )
    current_password = PasswordField('Contraseña  Actual', validators=[DataRequired(message="Contraseña actual requerida")])
    new_password = PasswordField('Nueva Contraseña', description=desc, validators=[DataRequired(message="Contraseña  nueva requerida")])
    verify_password = PasswordField('Confirmar Nueva Contraseña', validators=[DataRequired(message="Confirmar Nueva Contraseña")])
    submit = SubmitField('Actualizar')


class UpdateEmailForm(FlaskForm):
    email = StringField('Nuevo Email', validators=[DataRequired(message="Nuevo email requerido"), Email(message="Invalid email address")])
    email_verify = StringField('Confirmar email', validators=[DataRequired(message="Confirmación email requerida"), Email(message="Invalid email address")])
    password = PasswordField('Contraseña', validators=[DataRequired(message="Contraseña requerida")])
    submit = SubmitField('Actualizar')


class SmtpConfigForm(FlaskForm):
    server = StringField('Servidor', validators=[DataRequired(message="Servidor requerido")])
    port = IntegerField('Puerto', validators=[DataRequired(message="Puerto requerido"), NumberRange(min=0, message="Invalid port number")])
    sender = StringField('Correo del remitente', validators=[DataRequired(message="Correo del remitente requerido"), Email(message="Invalid email address")])
    user = StringField('Usuario SMTP')
    password = PasswordField('Contraseña SMTP')
    submit = SubmitField('Actualizar')


class AddHostsForm(FlaskForm):
    ip_address = TextAreaField('Información del Dispositivo', validators=[DataRequired(message="Ingrese la información")])
    submit = SubmitField('Agregar')


class SelectThemeForm(FlaskForm):
    theme = SelectField('Tema', config['Web_Themes'].items())
    submit = SubmitField('Actualizar')


class PollingConfigForm(FlaskForm):
    interval = StringField('Intervalo de consultas')
    retention_days = StringField('Días de almacenamiento de consultas')
    submit = SubmitField('Actualizar')
