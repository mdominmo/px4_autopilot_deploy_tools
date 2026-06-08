from pymavlink import mavutil
import pymavlink.mavutil as mavutil_module
import time

original_add_message = mavutil_module.add_message
def patched_add_message(messages, mtype, msg):
    try:
        original_add_message(messages, mtype, msg)
    except TypeError:
        messages[mtype] = msg
mavutil_module.add_message = patched_add_message

mav = mavutil.mavlink_connection('/dev/ttyACM0', baud=2000000)
try:
    mav.wait_heartbeat(timeout=10)
except:
    pass
print("Conectado")

cmd = 'cat /fs/microsd/etc/extras.txt\n'
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
