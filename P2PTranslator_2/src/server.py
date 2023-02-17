import socket, re
import threading
from src.configReader import configReader

class Server():

    def __init__(self):
        self.word_dictionary = {"pear": "hruska", "ball": "míč", "month": "měsíc", "tree": "strom", "iron": "železo"}
        self.server_addr = None
        self.server_socket = None
        self.client_address = None
        self.hostname = None

    def command_listener(self, connection):
        command = ""

        while True:
            data = connection.recv(4096).decode()
            if not data: break
            command = data

            if re.match("^((TRANSLATELOCL)(\"[^\"\r\n]*\"))$", command) != None:
                message = command[14:-1]
                answer = self.get_translation(message)
                connection.send(bytes(answer, "utf-8"))
            elif re.match("^((TRANSLATEPING)(\"[^\"\r\n]*\"))$", command) != None:
                message = command[14:-1]
                answer = self.get_program(message)
                connection.send(bytes(answer, "utf-8"))
            elif command == "test":
                connection.sendall(bytes("test", "utf-8"))
                print("test successful")
            elif command == "\r\n":
                pass
            else:
                message = "TRANSLATEDERR\"neznamy prikaz\""
                connection.send(bytes(message, "utf-8"))

    def start_server(self):
        try:
            self.server_addr = (configReader.c_server["address"], int(configReader.c_server["port"]))
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.bind(self.server_addr)
            self.hostname = socket.gethostname()

            print("Server start on " + str(self.server_addr[0]) + ":" + str(self.server_addr[1]))

            self.server_socket.listen()
            while True:
                connection, self.client_address = self.server_socket.accept()
                print("Client connection accepted from " + str(self.client_address[0]) + ":" + str(self.client_address[1]))
                client_thread = threading.Thread(target=self.command_listener, args=(connection,))
                client_thread.start()

        finally:
            connection.close()
            print("Client connection closed")


            self.server_socket.close()
            print("Server is closed")

    def get_translation(self, word: str):
        if word in self.word_dictionary:
            return "TRANSLATESUC\"" + self.word_dictionary[word] + "\""
        else:
            return "TRANSLATEDERR" + "\"" + "nenalezeno " + word + "\""

    def get_program(self, word: str):
        pass
