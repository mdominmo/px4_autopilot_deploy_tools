from pymavlink import mavutil
import time
import argparse

parser = argparse.ArgumentParser(description='Configura la IP de eth0 en el Pixhawk via USB')
parser.add_argument('--ip', default='10.10.10.10', help='IP a asignar al Pixhawk (default: 10.10.10.10)')
parser.add_argument('--mask', default='255.255.255.0', help='Mascara de red (default: 255.255.255.0)')
parser.add_argument('--device', default='/dev/ttyACM0')
parser.add_argument('--baud', default=2000000, type=int)
args = parser.parse_args()

mav = mavutil.mavlink_connection(args.device, baud=args.baud)
mav.wait_heartbeat()
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

send_command(mav, f"ifconfig eth0 {args.ip} netmask {args.mask}\n")
time.sleep(0.5)
send_command(mav, "ifconfig eth0\n")
