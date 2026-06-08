from pymavlink import mavutil
import pymavlink.mavutil as mavutil_module
import time
import struct

original_add_message = mavutil_module.add_message
def patched_add_message(messages, mtype, msg):
    try:
        original_add_message(messages, mtype, msg)
    except TypeError:
        messages[mtype] = msg
mavutil_module.add_message = patched_add_message

OP_RemoveFile       = 8
OP_CreateFile       = 6
OP_TerminateSession = 1
OP_WriteFile        = 7
OP_Ack              = 128
OP_Nack             = 129

def mavftp_send(mav, opcode, session, offset, data=b'', seq=1):
    header = struct.pack('<HBBBBBBI', seq, session, opcode, len(data), 0, 0, 0, offset)
    payload = bytearray(251)
    payload[0:12] = header
    payload[12:12+len(data)] = data
    mav.mav.file_transfer_protocol_send(0, mav.target_system, mav.target_component, bytes(payload))

def wait_ack(mav, timeout=3):
    t = time.time()
    while time.time() - t < timeout:
        msg = mav.recv_match(type='FILE_TRANSFER_PROTOCOL', blocking=True, timeout=1)
        if msg:
            return bytearray(msg.payload)
    return None

def shell(mav, cmd):
    cmd = cmd + '\n'
    mav.mav.serial_control_send(
        mavutil.mavlink.SERIAL_CONTROL_DEV_SHELL,
        mavutil.mavlink.SERIAL_CONTROL_FLAG_EXCLUSIVE |
        mavutil.mavlink.SERIAL_CONTROL_FLAG_RESPOND,
        0, 0, len(cmd),
        [ord(c) for c in cmd.ljust(70, '\0')][:70]
    )
    time.sleep(0.5)
    out = ''
    while True:
        msg = mav.recv_match(type='SERIAL_CONTROL', blocking=True, timeout=1)
        if not msg:
            break
        out += bytes(msg.data[:msg.count]).decode('utf-8', errors='replace')
    print(out)

mav = mavutil.mavlink_connection('/dev/ttyACM0', baud=2000000)
try:
    mav.wait_heartbeat(timeout=10)
except:
    pass
print("Conectado")

content = b"uxrce_dds_client start -t udp -h 10.10.10.11 -p 8888\n"
path = b'/fs/microsd/etc/extras.txt\x00'

mavftp_send(mav, OP_RemoveFile, 0, 0, path, seq=1)
ack = wait_ack(mav)
print(f"RemoveFile: opcode={ack[3] if ack else 'timeout'}")

mavftp_send(mav, OP_CreateFile, 0, 0, path, seq=2)
ack = wait_ack(mav)
if not ack or ack[3] == OP_Nack:
    print(f"ERROR CreateFile: {ack[12] if ack else 'timeout'}")
    exit(1)
session = ack[2]
print(f"CreateFile: opcode={ack[3]} session={session}")

mavftp_send(mav, OP_WriteFile, session, 0, content, seq=3)
ack = wait_ack(mav)
if not ack or ack[3] == OP_Nack:
    print(f"ERROR WriteFile: {ack[12] if ack else 'timeout'}")
    exit(1)
print(f"WriteFile: opcode={ack[3]} size={ack[4]}")

mavftp_send(mav, OP_TerminateSession, session, 0, seq=4)
print("Sesion cerrada")

time.sleep(0.5)
shell(mav, 'cat /fs/microsd/etc/extras.txt')
