from machine import WDT
import network
import time
import utime
import _thread
import socket
import select
import uasyncio as asyncio

pain = _thread.allocate_lock()
sound_pin = machine.Pin(1, machine.Pin.OUT)
led1_pin = machine.Pin(10, machine.Pin.OUT)
led2_pin = machine.Pin(14, machine.Pin.OUT)
wifi_led = machine.Pin("LED", machine.Pin.OUT)
timer = 4


def led_thread():  # allows for flashing LEDs and buzzer pseudo-pwming simultaneously
    end = time.time() + 14
    while time.time() < end:
        pain.acquire()
        led1_pin.on()
        led2_pin.off()
        pain.release()

        time.sleep(1)

        pain.acquire()
        led1_pin.off()
        led2_pin.on()
        pain.release()

        time.sleep(1)
        pain.acquire()
        led1_pin.off()
        led2_pin.off()
        pain.release()
    _thread.exit()


def goontime():
    global wdt
    end = time.time() + 10
    _thread.start_new_thread(led_thread, ())

    while time.time() < end:
        wdt.feed()
        print("fed dog")
        pain.acquire()
        time.sleep(13 / 3200)
        sound_pin.on()
        time.sleep(13 / 3200)
        sound_pin.off()
        pain.release()

    pain.acquire()
    led1_pin.off()
    led2_pin.off()
    pain.release()
    wdt.feed()
    time.sleep(5)
    wdt.feed()


def connect_to_server(ip, port):
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        client_socket.connect((ip, port))
        print(f"Connected to server at {ip}:{port}")
        return client_socket
    except Exception as e:
        print(f"Connection failed: {e}")
        return None


def perform_handshake(client_socket):
    try:
        client_socket.sendall(b"")  # NAME GOES HERE
        response = client_socket.recv(1024).decode()
        if response == "hello":
            print("Handshake successful with server!")
            return True
        else:
            print(f"Invalid handshake response: {response}")
            return False
    except Exception as e:
        print(f"Error during handshake: {e}")
        return False


def recv_message(client_socket):
    try:
        response = client_socket.recv(1024).decode()
        return response
    except Exception as e:
        print(f"Error receiving message: {e}")
        return e


def send_message(client_socket, message):
    try:
        client_socket.sendall(message.encode())
        print(f"Sent: {message}")
    except Exception as e:
        print(f"Error sending message: {e}")
        return e


timeout = 0

wlan = network.WLAN(network.STA_IF)

wlan.active(True)


wlan.connect("", "")  # POPULATE WIFI HERE

while wlan.isconnected() == False and timeout <= 15:
    wifi_led.on()
    time.sleep(1)
    wifi_led.off()
    time.sleep(1)
    timeout = timeout + 1
if wlan.isconnected() == False:
    print("wifi dead")
    led1_pin.on()
    machine.reset()


wifi_led.on()
server_ip = ""  # POPULATE IP OF THE SERVER
server_port = 42069
wdt = WDT(timeout=8000)

client_socket = connect_to_server(server_ip, server_port)

if client_socket and perform_handshake(client_socket):
    client_socket.setblocking(False)
    while True:
        try:

            ready_to_read, _, _ = select.select([client_socket], [], [], 1)
            if client_socket in ready_to_read:
                comms = recv_message(client_socket)
                print(comms)
                if comms == "trigger alarm":
                    send_message(client_socket, "signal ack")
                    goontime()
                    client_socket.close()
                    machine.reset()
                elif comms:
                    send_message(client_socket, "ack")
                    wdt.feed()
                else:
                    print("Server disconnected.")
                    machine.reset()

        except Exception as e:
            machine.reset()


else:
    print("Could not establish a connection.")
    machine.reset()
