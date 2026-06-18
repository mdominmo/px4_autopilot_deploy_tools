from pymavlink import mavutil
import time
import argparse
import os
from datetime import datetime

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOCAL_PARAMS_DIR = os.path.join(REPO_ROOT, 'params')

parser = argparse.ArgumentParser(description='Guarda los parametros de PX4 en la SD card o descarga al PC')
parser.add_argument('--device', default='/dev/ttyACM0')
parser.add_argument('--baud', default=2000000, type=int)
parser.add_argument('--output', '-o', default=None, help='Nombre del fichero (default: params_YYYYMMDD_HHMMSS)')
parser.add_argument('--local', '-l', action='store_true', help='Descargar parametros al PC (en params/)')
args = parser.parse_args()

if args.output is None:
    args.output = datetime.now().strftime('params_%Y%m%d_%H%M%S')

mav = mavutil.mavlink_connection(args.device, baud=args.baud)
mav.wait_heartbeat()
print(f"Conectado (system {mav.target_system}, component {mav.target_component})")

def send_command(mav, cmd):
    mav.mav.serial_control_send(
        mavutil.mavlink.SERIAL_CONTROL_DEV_SHELL,
        mavutil.mavlink.SERIAL_CONTROL_FLAG_EXCLUSIVE |
        mavutil.mavlink.SERIAL_CONTROL_FLAG_RESPOND,
        0, 0,
        len(cmd),
        [ord(c) for c in cmd.ljust(70, '\0')][:70]
    )
    time.sleep(0.5)
    output = ''
    while True:
        msg = mav.recv_match(type='SERIAL_CONTROL', blocking=True, timeout=1)
        if not msg:
            break
        output += bytes(msg.data[:msg.count]).decode('utf-8', errors='replace')
    return output

if args.local:
    os.makedirs(LOCAL_PARAMS_DIR, exist_ok=True)
    local_path = os.path.join(LOCAL_PARAMS_DIR, args.output)

    mav.mav.param_request_list_send(mav.target_system, mav.target_component)
    print("Descargando parametros...")

    params = {}
    total = None
    last_recv = time.time()

    while True:
        msg = mav.recv_match(type='PARAM_VALUE', blocking=True, timeout=2)
        if msg is None:
            if total is not None and len(params) >= total:
                break
            if time.time() - last_recv > 5:
                print(f"\nTimeout. Recibidos {len(params)}/{total if total else '?'}")
                break
            continue

        last_recv = time.time()
        total = msg.param_count
        params[msg.param_id] = (msg.param_value, msg.param_type)
        print(f"\r  {len(params)}/{total}", end='', flush=True)

        if len(params) >= total:
            break

    print()

    if not params:
        print("No se recibieron parametros.")
        exit(1)

    with open(local_path, 'w') as f:
        for param_id in sorted(params.keys()):
            value, ptype = params[param_id]
            if ptype == 9:
                f.write(f"{param_id}\t{value}\n")
            else:
                f.write(f"{param_id}\t{int(value)}\n")

    print(f"Guardados {len(params)} parametros en {local_path}")

else:
    sd_path = f"/fs/microsd/{args.output}"
    print(f"Guardando parametros en {sd_path} ...")
    result = send_command(mav, f"param save {sd_path}\n")
    print(result)
    print(f"Parametros guardados en {sd_path}")
