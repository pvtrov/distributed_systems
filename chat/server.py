import datetime
import socket
import threading

MAX_CLIENTS_NUM = 3
CODING = 'utf-8'


class ServerException(Exception):
    pass


class Server:
    def __init__(self):
        self.server_port = 5660
        self.server_ip = '127.0.0.1'
        self.clients = []  # (client_socket, nickname, address)
        self.tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP)
        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)

    def start_server(self):
        try:
            print('~~~~~ PYTHON SERVER ~~~~~')
            print('Server listening...')
            self.tcp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.tcp_socket.bind((self.server_ip, self.server_port))
            self.tcp_socket.listen(MAX_CLIENTS_NUM)
            self.udp_socket.bind((self.server_ip, self.server_port))

            threading.Thread(target=self._connect_with_tcp_client).start()
            threading.Thread(target=self._handle_udp_message).start()

        except OSError:
            print("Adress already in use! Please end all of your previous connections")
            return 98

        except KeyboardInterrupt:
            self.close_connections()
            print("Server disappeared!")

    def _broadcast_tcp(self, message):
        [client[0].send(message) for client in self.clients]

    def _broadcast_udp(self, message):
        [self.udp_socket.sendto(message, client[2]) for client in self.clients]

    def _handle_tcp_message(self, client):
        while True:
            try:
                message = client[0].recv(1024)
                if not message:
                    raise ServerException("Client ended connection.")

                print(f"[TCP][{client[2]}][{datetime.datetime.now()}] Got message from {client[1]}")
                self._broadcast_tcp(message)

            except ServerException:
                self._disconnect_client(client)
                return

    def _handle_udp_message(self):
        while True:
            message, address = self.udp_socket.recvfrom(1024)
            nickname = next((client[1] for client in self.clients if client[2] == address), None)
            print(f"[UDP][{address}][{datetime.datetime.now()}] Got message from {nickname}")
            self._broadcast_udp(message)

    def _disconnect_client(self, client):
        client[0].close()
        self.clients.remove(client)
        nickname = client[1]
        print(f"[{datetime.datetime.now()}] {nickname} left the chat")
        self._broadcast_tcp(f"{nickname} left the chat.".encode(CODING))
        return

    def _connect_with_tcp_client(self):
        try:
            while True:
                client, address = self.tcp_socket.accept()
                print(f"[{datetime.datetime.now()}] Client {address} connected!")

                client.send('NICK'.encode('ascii'))
                nickname = client.recv(1024).decode(CODING)
                print(f"Nickname set to {nickname}")
                self.clients.append((client, nickname, address))

                self._broadcast_tcp(f"{nickname} joined the chat.".encode(CODING))
                client.send("Connected to server!".encode(CODING))

                threading.Thread(target=self._handle_tcp_message, args=((client, nickname, address),)).start()
        except KeyboardInterrupt:
            self.close_connections()
            print("Server disappeared!")

    def close_connections(self):
        for client in self.clients:
            client[0].send("SERVER_SHUTDOWN".encode(CODING))
            client[0].close()


if __name__ == '__main__':
    try:
        server = Server()
        server.start_server()

    except KeyboardInterrupt:
        server.close_connections()
        print("Server disappeared!")
