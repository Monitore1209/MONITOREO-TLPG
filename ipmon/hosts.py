'''Hosts Module'''
import json
import os
import sys
import ipaddress
import platform
import subprocess

from multiprocessing.pool import ThreadPool

import flask_login
from flask import Blueprint, flash, redirect, render_template, request, url_for, jsonify

from ipmon import config, db, log
from ipmon.api import get_all_hosts
from ipmon.database import HostAlerts, Hosts, PollHistory
from ipmon.forms import AddHostsForm
from ipmon.polling import poll_host

sys.path.append(os.path.dirname(os.path.realpath(__file__)) + '/../')

hosts = Blueprint('hosts', __name__)

######################
# Routes #############
######################

@hosts.route('/addHosts', methods=['GET', 'POST'])
@flask_login.login_required
def add_hosts():
    '''Add Hosts Page'''
    form = AddHostsForm()
    if request.method == 'GET':
        return render_template('addHosts.html', form=form)

    elif request.method == 'POST':
        if form.validate_on_submit():
            pool = ThreadPool(config['Max_Threads'])
            threads = []

            for line in form.ip_address.data.strip().split('\n'):
                line = line.strip()
                if not line:
                    continue

                parts = line.split(',')
                ip_address = parts[0].strip()
                hostname = parts[1].strip() if len(parts) > 1 else ""
                ciudad = parts[2].strip() if len(parts) > 2 else ""
                dispositivo = parts[3].strip() if len(parts) > 3 else ""

                # Validar dirección IP
                try:
                    ipaddress.IPv4Address(ip_address)
                except ipaddress.AddressValueError:
                    flash(f'{ip_address} no es una dirección IP válida.', 'danger')
                    continue

                # Verificar si ya existe
                if Hosts.query.filter_by(ip_address=ip_address).first():
                    flash(f'La dirección IP {ip_address} ya existe!.', 'danger')
                    continue

                # Encolar el proceso
                threads.append(
                    pool.apply_async(_add_hosts_threaded, (ip_address, hostname, ciudad, dispositivo))
                )

            pool.close()
            pool.join()

            for thread in threads:
                try:
                    new_host = thread.get()
                    db.session.add(new_host)
                    flash(f'Añadida exitosamente {new_host.ip_address} ({new_host.hostname})', 'success')
                except Exception as exc:
                    flash(f'Fallo al agregar {new_host.ip_address}', 'danger')
                    log.error(f'Failed to add host to database. Exception: {exc}')
                    continue

            try:
                db.session.commit()
            except Exception as exc:
                db.session.rollback()
                flash('Error al guardar los cambios en la base de datos.', 'danger')
                log.error(f'Database commit failed: {exc}')
        else:
            for dummy, errors in form.errors.items():
                for error in errors:
                    flash(error, 'danger')

        return redirect(url_for('hosts.add_hosts'))


@hosts.route('/updateHosts', methods=['GET', 'POST'])
@flask_login.login_required
def update_hosts():
    '''Update Hosts'''
    if request.method == 'GET':
        return render_template('updateHosts.html', hosts=json.loads(get_all_hosts()))
    elif request.method == 'POST':
        results = request.form.to_dict()
        host = Hosts.query.filter_by(id=int(results['id'])).first()
        try:
            if results['hostname']:
                host.hostname = results['hostname']
            if results['ip_address']:
                host.ip_address = results['ip_address']
            if results['ciudad']:
                host.ciudad = results['ciudad']
            if results['dispositivo']:
                host.dispositivo = results['dispositivo']
            if results['alerts'] != str(host.alerts_enabled):
                host.alerts_enabled = False if results['alerts'] == 'False' else True
            db.session.commit()
            flash('Dispositivo actualizado correctamente {}'.format(host.hostname), 'success')
        except Exception:
            flash('Fallo al actualizar la información del dispositivo {}'.format(host.hostname), 'danger')

        return redirect(url_for('hosts.update_hosts'))


@hosts.route('/deleteHost', methods=['POST'])
@flask_login.login_required
def delete_host():
    '''Delete Hosts Page'''
    if request.method == 'POST':
        results = request.form.to_dict()
        host_id = int(results['id'])
        try:
            PollHistory.query.filter_by(host_id=host_id).delete()
            HostAlerts.query.filter_by(host_id=host_id).delete()
            Hosts.query.filter_by(id=host_id).delete()
            db.session.commit()
            flash('Dispositivo eliminado exitosamente! {}'.format(results['hostname']), 'success')
        except Exception as exc:
            flash('No se pudo eliminar el dispositivo {}: {}'.format(results['hostname'], exc), 'danger')

        return redirect(url_for('hosts.update_hosts'))


######################
# Private Functions ##
######################

def _add_hosts_threaded(ip_address, hostname, ciudad, dispositivo):
    status, current_time, resolved_hostname = poll_host(ip_address, new_host=True)
    hostname = hostname if hostname else resolved_hostname
    return Hosts(
        ip_address=ip_address,
        hostname=hostname,
        ciudad=ciudad,
        dispositivo=dispositivo,
        status=status,
        last_poll=current_time
    )

@hosts.route('/')
def index():
    hosts_list = Hosts.query.all()
    return render_template('index.html', hosts=hosts_list)

@hosts.route('/forzar_ping/<int:host_id>', methods=['GET'])
def forzar_ping(host_id):
    host = Hosts.query.get_or_404(host_id)

    try:
        if platform.system().lower() == 'windows':
            comando = ['ping', '-n', '1', host.ip_address]
        else:
            comando = ['ping', '-c', '1', host.ip_address]

        response = subprocess.run(
            comando,
            capture_output=True,
            text=True
        )

        if response.returncode == 0:
            return jsonify({"success": True, "message": f"Ping exitoso a {host.ip_address}"}), 200
        else:
            return jsonify({"success": False, "message": f"❌ Error al hacer ping a {host.ip_address}"}), 400

    except Exception as e:
        return jsonify({"success": False, "message": f"Excepción al hacer ping: {e}"}), 500

