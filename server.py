import socket
import time
import select
import asyncio
from friend import Friend
import os
from typing import Final
from discord import Intents, Client, Message, VoiceClient
from dotenv import load_dotenv


load_dotenv()
TOKEN: Final[str] = os.getenv("DISCORD_TOKEN")

# BOT SETUP
intents: Intents = Intents.default()
intents.message_content = True
client: Client = Client(intents=intents)

client_list = []  # client list is global var now


def trigger_buzzer(name):

    for friend in client_list:
        if friend.name == name:
            friend.send_message("trigger alarm")


def trigger_buzzers_for_all_devices():
    global client_list
    for friend in client_list:
        trigger_buzzer(friend)
    # O(n^2) my beloved, will be small lists so complexity isnt relevant


@client.event
async def on_message(message: Message) -> None:
    global client_list

    if message.author == client.user:
        return

    if message.content.startswith("!goon"):
        if message.author.id not in goon_users:
            goon_users.add(message.author.id)
            await message.channel.send(
                f"{message.author.mention} has joined the gooning squad! {len(goon_users)}/2"
            )

            if len(goon_users) == 2:
                await message.channel.send("It's gooning time!")
                trigger_buzzers_for_all_devices(goon_users)
                goon_users.clear()


def start_server(ip, port):
    server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_sock.setblocking(False)
    server_sock.bind((ip, port))
    server_sock.listen()
    print(f"Server started at {ip}:{port}")
    return server_sock


def handshake(client_socket):
    try:
        client_socket.settimeout(5)
        data = client_socket.recv(1024).decode()
        client_socket.sendall(b"hello")
        print("Handshake successful!")
        return True, Friend(data, client_socket)
    except socket.timeout:
        print("Handshake timeout.")
    except Exception as e:
        print(f"Error during handshake: {e}")
    return False, None


async def manage_clients(server_sock, client_list):
    while True:
        try:
            ready_to_read, _, _ = select.select([server_sock], [], [], 0)
            if ready_to_read:
                try:
                    client_socket, client_address = server_sock.accept()
                    print(f"New connection from {client_address}")

                    success, to_add = handshake(client_socket)

                    if success:
                        client_list.append(to_add)
                    else:
                        client_socket.close()
                except Exception as e:
                    print(f"Error accepting connection: {e}")

            await asyncio.sleep(2)
            # os.system("clear")
            print("current friend list\n")
            for friend in client_list:
                print(friend)
            print("\n\n\n\n\n")

        except KeyboardInterrupt:
            print("Shutting down server...")
            break


async def prune_client_list(client_list):
    while True:

        tasks = [friend.keep_alive(client_list) for friend in client_list]
        await asyncio.gather(*tasks)

        await asyncio.sleep(5)


async def run_server(ip, port):
    global client_list
    server_sock = start_server(ip, port)

    manage_task = asyncio.create_task(manage_clients(server_sock, client_list))
    prune_task = asyncio.create_task(prune_client_list(client_list))

    await asyncio.gather(manage_task, prune_task)


async def main():
    await run_server("192.168.1.3", 42069)


asyncio.run(main())