from pymavlink import mavutil
import time
import argparse
import os
import struct

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOCAL_PARAMS_DIR = os.path.join(REPO_ROOT, 'params')

parser = argparse.ArgumentParser(description='Carga parametros desde un fichero local al autopiloto PX4')
parser.add_argument('file', help='Nombre del fichero en params/ (o ruta completa)')
parser.add_argument('--device', default='/dev/ttyACM0')
parser.add_argument('--baud', default=2000000, type=int)
mode = parser.add_mutually_exclusive_group(required=True)
mode.add_argument('--load', action='store_true', help='Reset a defaults + aplicar fichero (restauracion completa)')
mode.add_argument('--merge', action='store_true', help='Aplicar solo los parametros del fichero sin resetear')
args = parser.parse_args()

if os.path.isfile(args.file):
    file_path = args.file
else:
    file_path = os.path.join(LOCAL_PARAMS_DIR, args.file)

if not os.path.isfile(file_path):
    print(f"Error: no se encuentra el fichero {file_path}")
    exit(1)

params = {}
with open(file_path, 'r') as f:
    for line in f:
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        parts = line.split('\t')
        if len(parts) != 2:
            continue
        param_id, value = parts
        try:
            if '.' in value or 'e' in value.lower():
                params[param_id] = float(value)
            else:
                params[param_id] = int(value)
        except ValueError:
            print(f"Aviso: no se pudo parsear '{param_id} = {value}', saltando.")

print(f"Leidos {len(params)} parametros de {file_path}")

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

if args.load:
    print("Reseteando parametros a defaults...")
    result = send_command(mav, "param reset_all\n")
    print(result)
    time.sleep(1)

def set_param(mav, param_id, value):
    param_id_bytes = param_id.encode('utf-8')
    if isinstance(value, float):
        param_type = mavutil.mavlink.MAV_PARAM_TYPE_REAL32
        param_value = value
    else:
        param_type = mavutil.mavlink.MAV_PARAM_TYPE_INT32
        param_value = struct.unpack('f', struct.pack('i', value))[0]

    mav.mav.param_set_send(
        mav.target_system, mav.target_component,
        param_id_bytes,
        param_value,
        param_type
    )

    msg = mav.recv_match(type='PARAM_VALUE', blocking=True, timeout=5)
    if msg and msg.param_id == param_id:
        return True
    return False

print(f"Enviando {len(params)} parametros ({'load' if args.load else 'merge'})...")
ok = 0
fail = 0
for i, (param_id, value) in enumerate(sorted(params.items()), 1):
    if set_param(mav, param_id, value):
        ok += 1
    else:
        fail += 1
        print(f"\n  Fallo: {param_id}")
    print(f"\r  {i}/{len(params)} (ok: {ok}, fail: {fail})", end='', flush=True)

print(f"\n\nCompletado: {ok} ok, {fail} fallidos")

if args.load:
    print("Guardando y reiniciando...")
    send_command(mav, "param save\n")
    time.sleep(0.5)
    mav.mav.command_long_send(
        mav.target_system, mav.target_component,
        mavutil.mavlink.MAV_CMD_PREFLIGHT_REBOOT_SHUTDOWN,
        0, 1, 0, 0, 0, 0, 0, 0
    )
    print("Reiniciando autopiloto...")
else:
    print("Guardando parametros...")
    send_command(mav, "param save\n")
    print("Hecho.")
