import os
import socket
import time
from contextlib import contextmanager
from subprocess import Popen


@contextmanager
def run():
    port = os.environ['FLASK_RUN_PORT']
    wait_for_port(port, status='refuse')
    server = Popen(['flask', 'run'])
    wait_for_port(port)
    try:
        yield server
    finally:
        server.terminate()


def wait_for_port(port, host='localhost', timeout=5.0, status='accept'):
    start_time = time.perf_counter()
    connection_status = None
    while connection_status != status:
        try:
            with socket.create_connection((host, port), timeout=timeout):
                connection_status = 'accept'
        except OSError:
            connection_status = 'refuse'
        if (time.perf_counter() - start_time) >= timeout:
            raise TimeoutError(f'Waited too long for {port}:{host} to be {status}.')
        time.sleep(0.01)