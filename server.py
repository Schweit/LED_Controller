import socket
import time
import struct
import random
from flask import Flask, request

SERVER_HOST = '0.0.0.0'
SERVER_PORT = 5007
FLASK_SERVER_HOST = '0.0.0.0'
FLASK_SERVER_PORT = 5008
BUFFER_SIZE = 4096

LED_COUNT = 86

app = Flask(__name__)

client_sockets = []

def start_server():

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, BUFFER_SIZE)

    server_socket.bind((SERVER_HOST, SERVER_PORT))

    server_socket.listen()
    print("Server started. Waiting for client connections...")

    while True:
        client_socket, client_address = server_socket.accept()
        print(f"Client connected: {client_address}")

        client_sockets.append(client_socket)

        print(client_socket)
        time.sleep(1)

@app.route('/trigger-sequence')
def trigger_sequence():
    # red = request.args.get('red', type=int)
    # green = request.args.get('green', type=int)
    # blue = request.args.get('blue', type=int)
    # led_metadata = compute_led_metadata(red, green, blue)
    # send_led_metadata(led_metadata, client_sockets)
    run_sequence()

def run_sequence():
    wave_sequence = []
    while True:
        wave_effect(client_sockets)
        time.sleep(.6)

def wave_effect(client_sockets):
    payload = []

    for client_socket in client_sockets:
        client_data = []
        client_index = client_sockets.index(client_socket)

        for led_index in range(LED_COUNT):
            wave_position = random.uniform(0, 1)
            red = int(255 * (1 + wave_position) / 2)
            green = int(255 * (1 + wave_position) / 4)
            blue = int(255 * (1 - wave_position) / 4)

            # print((led_index, (red, green, blue)))
            client_data.append((led_index, (red, green, blue)))

        # print((client_index, client_data))
        payload.append((client_index, client_data))
    # print(payload)
    send_led_metadata(payload)

def pack_led_data(data):
    packed_data = bytearray()
    for item in data:
        led_index = item[0]
        color = item[1]
        packed_item = struct.pack('!I3B', led_index, *color)
        packed_data.extend(packed_item)
    return packed_data

def send_led_metadata(led_metadata):
    for clientIndex, client_data in led_metadata:
        print('SENDING')
        print(client_data)
        packed_data = pack_led_data(client_data)
        total_sent = 0
        data_length = len(packed_data)
        client_sockets[clientIndex].send(struct.pack('!I', data_length))
        while total_sent < data_length:
            chunk = packed_data[total_sent:total_sent+4096]
            sent = client_sockets[clientIndex].send(chunk)
            total_sent += sent

if __name__ == '__main__':
    import threading
    server_thread = threading.Thread(target=start_server)
    server_thread.start()

    app.run(host=FLASK_SERVER_HOST, port=FLASK_SERVER_PORT)
