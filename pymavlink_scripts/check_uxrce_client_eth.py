from pymavlink import mavutil
import pymavlink.mavutil as mavutil_module
import time
import argparse

original_add_message = mavutil_module.add_message
def patched_add_message(messages, mtype, msg):
    try:
        original_add_message(messages, mtype, msg)
    except TypeError:
        messages[mtype] = msg
mavutil_module.add_message = patched_add_message

parser = argparse.ArgumentParser(description='Check UXRCE DDS client status via Ethernet/UDP')
parser.add_argument('--host', default='0.0.0.0',
                    help='Local IP to listen on (default: 0.0.0.0)')
parser.add_argument('--port', default=14550, type=int,
                    help='MAVLink UDP port (default: 14550)')
args = parser.parse_args()

connection_str = f'udpin:{args.host}:{args.port}'
print(f"Esperando conexion MAVLink en {connection_str} ...")

mav = mavutil.mavlink_connection(connection_str)
try:
    mav.wait_heartbeat(timeout=10)
except Exception:
    pass
print("Conectado")

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
    while True:
        msg = mav.recv_match(type='SERIAL_CONTROL', blocking=True, timeout=1)
        if not msg:
            break
        print(bytes(msg.data[:msg.count]).decode('utf-8', errors='replace'), end='')

send_command(mav, "uxrce_dds_client status\n")
send_command(mav, "mavlink status\n")
