import contextlib
import os
import sys
import platform
import subprocess
import tempfile
import time
from pathlib import Path

import psutil

# Path to the test data folder.
TEST_DATA_DIR = Path(__file__).parent / "data"


def get_process_listening_port(proc):
    conn = None
    if platform.system() == "Windows":
        current_process = psutil.Process(proc.pid)
        children = []
        while children == []:
            time.sleep(0.01)
            children = current_process.children(recursive=True)
            if (3, 6) <= sys.version_info < (3, 7):
                children = [current_process]
        for child in children:
            while child.connections() == [] and not any(conn.status == "LISTEN" for conn in child.connections()):
                time.sleep(0.01)

            conn = next(filter(lambda conn: conn.status == "LISTEN", child.connections()))
    else:
        psutil_proc = psutil.Process(proc.pid)
        while not any(conn.status == "LISTEN" for conn in psutil_proc.connections()):
            time.sleep(0.01)

        conn = next(filter(lambda conn: conn.status == "LISTEN", psutil_proc.connections()))
    return conn.laddr.port


@contextlib.contextmanager
def get_paling_server(example_py, start_html):
    """Run an Paling example with the mode/port overridden so that no browser is launched and a random port is assigned"""
    test = None

    try:
        with tempfile.NamedTemporaryFile(mode='w', dir=os.path.dirname(example_py), delete=False) as test:
            # We want to run the examples unmodified to keep the test as realistic as possible, but all of the examples
            # want to launch browsers, which won't be supported in CI. The below script will configure paling to open on
            # a random port and not open a browser, before importing the Python example file - which will then
            # do the rest of the set up and start the paling server. This is definitely hacky, and means we can't
            # test mode/port settings for examples ... but this is OK for now.
            test.write(f"""
import paling

paling._start_args['mode'] = None
paling._start_args['port'] = 0

import {os.path.splitext(os.path.basename(example_py))[0]}
""")
        proc = subprocess.Popen(
                [sys.executable, test.name],
                cwd=os.path.dirname(example_py),
            )
        paling_port = get_process_listening_port(proc)

        yield f"http://localhost:{paling_port}/{start_html}"

        proc.terminate()

    finally:
        if test:
            try:
                os.unlink(test.name)
            except FileNotFoundError:
                pass


def get_console_logs(driver, minimum_logs=0):
    console_logs = driver.get_log('browser')

    while len(console_logs) < minimum_logs:
        console_logs += driver.get_log('browser')
        time.sleep(0.1)

    return console_logs
