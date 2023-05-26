import socket
import time
import threading
import ast
import struct
from rpi_ws281x import PixelStrip, Color

SERVER_HOST = '192.168.7.44'
SERVER_PORT = 5007
BUFFER_SIZE = 4096


LED_COUNT = 86
LED_PIN = 18
LED_FREQ_HZ = 800000
LED_DMA = 10
LED_BRIGHTNESS = 255
LED_INVERT = False
LED_CHANNEL = 0

client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, BUFFER_SIZE)
client_socket.connect((SERVER_HOST, SERVER_PORT))

led_metadata = []
led_metadata_lock = threading.Lock()


strip = PixelStrip(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL)
strip.begin()

class LedData:
    def __init__(self):
        self.metadata = None
        self.metadata_lock = threading.Lock()
        self.subscribers = []

    def set_metadata(self, metadata):
        # print('SETMETA')
        # print(metadata)
        with self.metadata_lock:
            self.metadata = metadata

        self.notify_subscribers()

    def subscribe(self, subscriber):
        with self.metadata_lock:
            self.subscribers.append(subscriber)

    def unsubscribe(self, subscriber):
        with self.metadata_lock:
            self.subscribers.remove(subscriber)

    def notify_subscribers(self):
        with self.metadata_lock:
            for subscriber in self.subscribers:
                subscriber(self.metadata)


def unpack_led_data(packed_data):
    unpacked_data = []
    while packed_data:
        led_index, r, g, b = struct.unpack('!I3B', packed_data[:7])
        unpacked_data.append((led_index, (r, g, b)))
        packed_data = packed_data[7:]
    return unpacked_data

def receive_led_metadata(led_data):
    while True:
        data_length_bytes = client_socket.recv(4)
        data_length = struct.unpack('!I', data_length_bytes)[0]
        received_data = bytearray()
        while len(received_data) < data_length:
            chunk = client_socket.recv(4096)
            received_data.extend(chunk)
        led_data.set_metadata(unpack_led_data(received_data))

def perform_led_sequence(metadata):
    for led_info in metadata:
        led_index, led_color = led_info

        strip.setPixelColor(led_index, Color(*led_color))
        strip.show()
        time.sleep(.01)
        pass

def led_sequence(led_data):
    def execute_led_sequence(metadata):
        if metadata is not None:
            print('UPDATED')
            print(metadata)
            perform_led_sequence(metadata)

    led_data.subscribe(execute_led_sequence)

    while True:
        with led_data.metadata_lock:
            current_metadata = led_data.metadata

        if current_metadata is None:
            time.sleep(0.1)
            continue

        print('CURRENT')
        print(current_metadata)
        perform_led_sequence(current_metadata)

        time.sleep(0.1)

if __name__ == "__main__":
    led_data = LedData()

    led_thread = threading.Thread(target=led_sequence, args=(led_data,))
    led_thread.start()

    receive_led_metadata(led_data)

    led_thread.join()

    client_socket.close()
