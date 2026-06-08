from pymavlink import mavutil
import pymavlink.mavutil as mavutil_module

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

mav.mav.command_long_send(
    mav.target_system, mav.target_component,
    mavutil.mavlink.MAV_CMD_PREFLIGHT_REBOOT_SHUTDOWN,
    0, 1, 0, 0, 0, 0, 0, 0
)
print("Reiniciando...")
