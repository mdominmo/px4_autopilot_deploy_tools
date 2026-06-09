from pymavlink import mavutil
import time
import argparse

parser = argparse.ArgumentParser(description='Check and configure Pixhawk ethernet via USB')
parser.add_argument('--device', default='/dev/ttyACM0')
parser.add_argument('--baud', default=2000000, type=int)
parser.add_argument('--set-ip', metavar='IP', help='Assign this IP to eth0 (e.g. 10.10.10.10)')
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

print("\n--- ifconfig eth0 ---")
send_command(mav, "ifconfig eth0\n")

print("\n--- netman show ---")
send_command(mav, "netman show\n")

print("\n--- cat /fs/microsd/net.cfg ---")
send_command(mav, "cat /fs/microsd/net.cfg\n")

if args.set_ip:
    print(f"\n--- Configurando eth0 con {args.set_ip} ---")
    send_command(mav, f"ifconfig eth0 {args.set_ip} netmask 255.255.255.0\n")
    time.sleep(0.5)
    print("\n--- ifconfig eth0 (post-config) ---")
    send_command(mav, "ifconfig eth0\n")
