import socket
import time


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
        client_socket.sendall(b"scrounch")
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


def send_message(client_socket, message):
    try:
        client_socket.sendall(message.encode())
        print(f"Sent: {message}")
    except Exception as e:
        print(f"Error sending message: {e}")


def recv_message(client_socket):
    """Receive a message from the server."""
    try:
        response = client_socket.recv(1024).decode()
        print(response)
        return response
    except Exception as e:
        print(f"Error receiving message: {e}")
        return e


# this is not real, just for testing.
if __name__ == "__main__":
    server_ip = "192.168.1.3"
    server_port = 42069

    client_socket = connect_to_server(server_ip, server_port)

    if client_socket and perform_handshake(client_socket):
        while True:
            try:
                comms = recv_message(client_socket)
                if comms is not None:
                    send_message(client_socket, "ack")
                    print("sending ack")
            except Exception as e:
                print("message send failed, comms must be dead")

    else:
        print("Could not establish a connection.")
