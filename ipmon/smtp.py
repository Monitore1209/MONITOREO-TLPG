'''Librerias SMTP'''
import os
import sys
import smtplib
import json

import flask_login
from email.mime.text import MIMEText
from flask import Blueprint, render_template, redirect, url_for, request, flash

sys.path.append(os.path.dirname(os.path.realpath(__file__)) + '/../')
from ipmon import db, log
from ipmon.database import SmtpServer
from ipmon.api import get_smtp_configured, get_smtp_config
from ipmon.forms import SmtpConfigForm

smtp = Blueprint('smtp', __name__)


##########################
# Routes #################
##########################
@smtp.route("/configureSMTP", methods=['GET', 'POST', 'DELETE'])
@flask_login.login_required
def configure_smtp():
    '''Configuración SMTP'''
    form = SmtpConfigForm()
    if request.method == 'GET':
        return render_template('smtpConfig.html', smtp=json.loads(get_smtp_config()), form=form)
    elif request.method == 'POST':
        if request.form.get('action') == 'delete':
            try:
                smtp_conf = SmtpServer.query.first()
                smtp_conf.smtp_server = ''
                smtp_conf.smtp_port = ''
                smtp_conf.smtp_sender = ''
                smtp_conf.smtp_user = ''
                smtp_conf.smtp_password = ''
                db.session.commit()
                flash('Configuración SMTP eliminada correctamente', 'success')
            except Exception:
                flash('Error al eliminar Configuración SMTP', 'danger')
            return redirect(url_for('smtp.configure_smtp'))
        else:
            # Código existente para actualizar configuración SMTP
            if form.validate_on_submit():
                try:
                    smtp_conf = SmtpServer.query.first()
                    smtp_conf.smtp_server = form.server.data
                    smtp_conf.smtp_port = form.port.data
                    smtp_conf.smtp_sender = form.sender.data
                    smtp_conf.smtp_user = form.user.data
                    smtp_conf.smtp_password = form.password.data
                    db.session.commit()
                    flash('Configuración de SMTP actualizada correctamente', 'success')
                except Exception as exc:
                    flash('Error al actualizar SMTP : {}'.format(exc), 'danger')
            else:
                for dummy, errors in form.errors.items():
                    for error in errors:
                        flash(error, 'danger')
            return redirect(url_for('smtp.configure_smtp'))
        
@smtp.route("/smtpTest", methods=['POST'])
@flask_login.login_required
def smtp_test():
    '''Enviar correo de prueba SMTP'''
    if request.method == 'POST':
        results = request.form.to_dict()
        subject = 'IPMON SMTP Test Message'
        message = 'IPMON SMTP Test Message'

        try:
            send_smtp_message(results['recipient'], subject, message)
            flash('Mensaje de prueba SMTP enviado correctamente', 'success')
        except Exception as exc:
            flash('Error al enviar el mensaje de prueba SMTP: {}'.format(exc), 'danger')

    return redirect(url_for('smtp.configure_smtp'))


##########################
# Functions ##############
##########################
def send_smtp_message(recipient, subject, message):
    '''Enviar mensaje SMTP '''
    current_smtp = json.loads(get_smtp_config())
    if not json.loads(get_smtp_configured())['smtp_configured']:
        log.error('Attempting to send SMTP message but SMTP not configured.')
        return

    msg = MIMEText(message, 'html')
    msg['Subject'] = subject
    msg['From'] = current_smtp['smtp_sender']

    try:
        server = smtplib.SMTP(current_smtp['smtp_server'], int(current_smtp['smtp_port']), timeout=10)
        server.set_debuglevel(1)   # Muestra detalles para debug en consola
        server.ehlo()
        server.starttls()
        server.ehlo()

        # Login SMTP con usuario y contraseña
        smtp_user = current_smtp.get('smtp_user')
        smtp_password = current_smtp.get('smtp_password')
        if smtp_user and smtp_password:
            server.login(smtp_user, smtp_password)

        server.sendmail(current_smtp['smtp_sender'], recipient, msg.as_string())
        server.quit()
    except Exception as exc:
        log.error(f'Error enviando correo SMTP: {exc}')
        raise exc
