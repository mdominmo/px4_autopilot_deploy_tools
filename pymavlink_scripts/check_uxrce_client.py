from pymavlink import mavutil
import time

mav = mavutil.mavlink_connection('/dev/ttyACM0', baud=2000000)
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

send_command(mav, "uxrce_dds_client status\n")
send_command(mav, "mavlink status\n")