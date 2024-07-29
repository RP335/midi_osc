import socket
import mido
from pythonosc import udp_client, dispatcher, osc_server
import time
import numpy as np
from collections import deque
from midi_analyser import MidiAnalyzer
import threading

print(mido.get_output_names())

analyzer = MidiAnalyzer()

td_client = udp_client.SimpleUDPClient("192.168.0.181", 10000)

midiout = mido.open_output('IAC Driver Bus 2')

midiin = mido.open_input('IAC Driver Bus 1')

gyrosc_client = udp_client.SimpleUDPClient("127.0.0.1", 9999)


# Map MIDI CC numbers to GyrOSC parameters
cc_to_gyrosc = {
    21: '/test/ax',  # CC 21 controls acceleration X
    22: '/test/ay',  # CC 22 controls acceleration Y
    23: '/test/az',  # CC 23 controls acceleration Z
    24: '/test/pitch',  # CC 24 controls pitch
    25: '/test/roll',  # CC 25 controls roll
    26: '/test/yaw',  # CC 26 controls yaw
}

def process_midi_input(msg):
    if msg.type == 'control_change' and msg.control in cc_to_gyrosc:
        osc_address = cc_to_gyrosc[msg.control]
        osc_value = msg.value / 127.0  # Normalize to 0-1 range
        print(f"Sending OSC: {osc_address} {osc_value}")
        gyrosc_client.send_message(osc_address, osc_value)
        midiout.send(msg)


def midi_input_loop():
    print("Starting MIDI input loop...")
    inport = mido.open_input('IAC Driver Bus 3')  # Replace with your MIDI input port name
    while True:
        for msg in inport.iter_pending():
            process_midi_input(msg)
def process_midi(msg):
    if msg.type == 'note_on':
        note = msg.note
        velocity = msg.velocity
        analyzer.add_note(note, velocity)
        return 'note_on', note, velocity
    elif msg.type == 'note_off':
        note = msg.note
        analyzer.remove_note(note)
        return 'note_off', note, 0
    elif msg.type == 'control_change':
        return 'control_change', msg.control, msg.value
    return None, None, None

def send_osc(address, value):
    td_client.send_message(address, value)

def play_and_capture_midi():
    inport = mido.open_input('IAC Driver Bus 1')  # Replace with your MIDI input port name

    while True:
        for msg in inport.iter_pending():
            print(msg)
            msg_type, data, value = process_midi(msg)
            if msg_type is not None:
                if msg_type in ['note_on', 'note_off']:
                    send_osc("/midi/note", data)
                    send_osc("/midi/velocity", value)
                    send_osc("/midi/notes", analyzer.get_active_notes())
                    send_osc("/midi/chord", analyzer.get_current_chord())
                    send_osc("/midi/intensity", analyzer.get_playing_intensity())
                    send_osc("/midi/pitch_range", analyzer.get_pitch_range())
                elif msg_type == 'control_change':
                    send_osc(f"/midi/cc/{data}", value / 127.0)
        time.sleep(0.01)


def attitude_handler(address, *args):
    value = args[0]
    control = {'pitch': 1, 'roll': 2, 'yaw': 3}[address.split('/')[-1]]
    # print(f"Received attitude data: {address}={value}")
    midiout.send(mido.Message('control_change', control=control, value=int(value)))
    # print(f"Sent MIDI CC message for {address}")


def accel_handler(address, *args):
    value = args[0]
    control = {'ax': 4, 'ay': 5, 'az': 6}[address.split('/')[-1]]
    # print(f"Received acceleration data: {address}={value}")
    midiout.send(mido.Message('control_change', control=control, value=int(value)))
    # print(f"Sent MIDI CC message for {address}")


def rotation_rate_handler(address, *args):
    value = args[0]
    control = {'rx': 7, 'ry': 8, 'rz': 9}[address.split('/')[-1]]
    # print(f"Received rotation rate data: {address}={value}")
    midiout.send(mido.Message('control_change', control=control, value=int(value)))
    # print(f"Sent MIDI CC message for {address}")


def gravity_handler(address, *args):
    value = args[0]
    control = {'gx': 10, 'gy': 11, 'gz': 12}[address.split('/')[-1]]
    # print(f"Received gravity data: {address}={value}")
    midiout.send(mido.Message('control_change', control=control, value=int(value)))
    # print(f"Sent MIDI CC message for {address}")


def get_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP


if __name__ == "__main__":
    # Set up OSC server
    dispatcher = dispatcher.Dispatcher()

    # Map the OSC addresses (keep your existing mappings)
    for addr in ['/test/pitch', '/test/roll', '/test/yaw']:
        dispatcher.map(addr, attitude_handler)

    for addr in ['/test/ax', '/test/ay', '/test/az']:
        dispatcher.map(addr, accel_handler)

    for addr in ['/test/rx', '/test/ry', '/test/rz']:
        dispatcher.map(addr, rotation_rate_handler)

    for addr in ['/test/gx', '/test/gy', '/test/gz']:
        dispatcher.map(addr, gravity_handler)

    ip = get_ip()
    port = 9999
    server = osc_server.ThreadingOSCUDPServer((ip, port), dispatcher)
    print(f"Serving on {ip}:{port}")
    print("Use this IP address and port in your GyrOSC app")

    midi_thread = threading.Thread(target=play_and_capture_midi)
    midi_thread.start()

    midi_input_thread = threading.Thread(target=midi_input_loop)
    midi_input_thread.start()

    server.serve_forever()