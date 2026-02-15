import socket
import subprocess
import sys
import os

PORTS = [5002,5003,8000,8888,5000,5001]

def is_port_free(p):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        s.bind(('0.0.0.0', p))
        s.close()
        return True
    except Exception:
        return False

def choose_port():
    for p in PORTS:
        if is_port_free(p):
            return p
    # fallback: ask OS for a free port
    s = socket.socket()
    s.bind(('', 0))
    port = s.getsockname()[1]
    s.close()
    return port

def add_firewall_rule(port):
    try:
        cmd = [
            'netsh', 'advfirewall', 'firewall', 'add', 'rule',
            f'name=SchoolAutoChat_{port}', 'dir=in', 'action=allow',
            'protocol=TCP', f'localport={port}'
        ]
        # run with shell=False; will fail if not elevated
        subprocess.run(cmd, check=True)
        print(f'Firewall rule added for TCP port {port}')
    except subprocess.CalledProcessError:
        print('Не удалось добавить правило в Firewall. Запустите от имени администратора или добавьте правило вручную.')

if __name__ == '__main__':
    # If port passed as first arg, use it
    port = None
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except Exception:
            port = None

    # If env PORT set
    if not port:
        port_env = os.environ.get('PORT')
        if port_env and port_env.isdigit():
            port = int(port_env)

    if not port:
        port = choose_port()

    print(f'Chosen port: {port}')

    # If requested, try to add firewall rule
    open_fw = os.environ.get('OPEN_FIREWALL', '0')
    if open_fw == '1':
        add_firewall_rule(port)

    # Run server.py with chosen port
    python = sys.executable
    os.execv(python, [python, os.path.join(os.path.dirname(__file__), 'server.py'), str(port)])
