'''Biblioteca de sondeo del host'''
import os
import sys
import platform
import subprocess
import socket
import time
import json

from multiprocessing.pool import ThreadPool
from datetime import date, timedelta

sys.path.append(os.path.dirname(os.path.realpath(__file__)) + '/../')
from ipmon import app, db, scheduler, log, config
from ipmon.database import Hosts, PollHistory, HostAlerts
from ipmon.api import get_all_hosts, get_host, get_polling_config, get_poll_history


def poll_host(host, new_host=False, count=3):
    """Hacer sondeo al host vía ping ICMP para verificar si está activo/inactivo"""
    hostname = None

    if platform.system().lower() == 'windows':
        command = ['ping', '-n', str(count), '-w', '1000', host]  # timeout 1 seg
    else:
        command = ['ping', '-c', str(count), '-W', '1', host]

    try:
        # Capturamos salida para analizarla
        response = subprocess.run(
            command,
            capture_output=True,
            text=True
        )

        salida = response.stdout.lower()

        if platform.system().lower() == 'windows':
            exito = "ttl=" in salida
        else:
            exito = (response.returncode == 0)

        if new_host:
            hostname = get_hostname(host)

        return ('Up' if exito else 'Down', time.strftime('%Y-%m-%d %T'), hostname)

    except Exception as e:
        return ('Down', time.strftime('%Y-%m-%d %T'), hostname)

def update_poll_scheduler(poll_interval):
    '''Actualiza la programación de sondeo de hosts mediante APScheduler'''
    # Attempt to remove the current scheduler
    try:
        scheduler.remove_job('Poll Hosts')
    except Exception:
        pass

    scheduler.add_job(id='Poll Hosts', func=_poll_hosts_threaded, trigger='interval', seconds=int(poll_interval), max_instances=1)


def add_poll_history_cleanup_cron():
    '''Agrega crong job para la limpieza del historial de sondeo'''
    scheduler.add_job(id='Poll History Cleanup', func=_poll_history_cleanup_task, trigger='cron', hour='0', minute='30')


def get_hostname(ip_address):
    '''Obtiene el FQDN a partir de una dirección IP'''
    try:
        hostname = socket.getfqdn(ip_address)
    except socket.error:
        hostname = 'Unknown'

    return hostname



def _poll_hosts_threaded():
    log.debug('Starting host polling')
    s = time.perf_counter()

    from math import ceil
    import time as t

    def chunk_list(lst, n):
        for i in range(0, len(lst), n):
            yield lst[i:i + n]

    MAX_BATCH_SIZE = 50  # Número de IPs a la vez
    WAIT_BETWEEN_BATCHES = 1  # Segundos de espera

    with app.app_context():
        all_hosts = json.loads(get_all_hosts())
        batches = list(chunk_list(all_hosts, MAX_BATCH_SIZE))

        for i, batch in enumerate(batches):
            pool = ThreadPool(min(len(batch), config['Max_Threads']))
            threads = []

            for host in batch:
                threads.append(
                    pool.apply_async(_poll_host_task, (host['id'],))
                )

            pool.close()
            pool.join()

            for thread in threads:
                host_info, new_poll_history, host_alert = thread.get()
                host = Hosts.query.filter_by(id=int(host_info['id'])).first()
                host.previous_status = host_info['previous_status']
                host.status = host_info['status']
                host.last_poll = host_info['last_poll']
                db.session.add(new_poll_history)
                if host_alert:
                    db.session.add(host_alert)

            db.session.commit()

            if i < len(batches) - 1:
                log.debug(f"Esperando {WAIT_BETWEEN_BATCHES}s antes de siguiente lote...")
                t.sleep(WAIT_BETWEEN_BATCHES)

    log.debug("Host polling finished executing in {} seconds.".format(time.perf_counter() - s))


def _poll_host_task(host_id):
    with app.app_context():
        host_info = json.loads(get_host(int(host_id)))
        status, poll_time, hostname = poll_host(host_info['ip_address'])
        host_alert = None

        # Update host status
        host_info['previous_status'] = host_info['status']
        host_info['status'] = status
        host_info['last_poll'] = poll_time

        # Add poll history for host
        if hostname:
            host_info['hostname'] = hostname

        new_poll_history = PollHistory(
            host_id=host_info['id'],
            poll_time=poll_time,
            poll_status=status
        )

        log.info('{} - {}'.format(host_info['alerts_enabled'], type(host_info['alerts_enabled'])))
        if host_info['alerts_enabled'] and host_info['previous_status'] != status:
            # Create alert if status changed
            host_alert = HostAlerts(
                host_id=host_info['id'],
                hostname=host_info['hostname'],
                ip_address=host_info['ip_address'],
                host_status=host_info['status'],
                poll_time=host_info['last_poll']
            )

    return host_info, new_poll_history, host_alert


def _poll_history_cleanup_task():
    log.debug('Starting poll history cleanup')
    s = time.perf_counter()

    with app.app_context():
        retention_days = json.loads(get_polling_config())['history_truncate_days']
        current_date = date.today()

        # Delete poll history where date_created < today - retention_days
        PollHistory.query.filter(
            PollHistory.date_created < (current_date - timedelta(days=retention_days))
        ).delete()

        db.session.commit()

    log.debug("Poll history cleanup finished executing in {} seconds.".format(time.perf_counter() - s))
