import socket, os, re, threading, logging as log, atexit

from src.configReader import configReader

filepath = os.path.basename(__file__)
filename = os.path.splitext(filepath)

class Server():

    def __init__(self):
        self.word_dictionary = {"apple": "jablko", "car": "auto", "year": "rok", "water": "voda", "glass": "sklo"}
        self.server_addr = None
        self.server_socket = None
        log.basicConfig(
            level=log.DEBUG,
            format='%(asctime)s | %(levelname)s | %(message)s',
            filename='./log/%s.log' % filename[0],
            filemode='w'
        )

    def command_listener(self, connection, client_addr):
        command = ""

        while True:
            data = connection.recv(4096).decode()
            if not data:
                log.info("Client connection was closed at %s:%d" % (client_addr[0], client_addr[1]))
                connection.shutdown(0)
                connection.close()
                break
            command = data

            if re.match("^((TRANSLATELOCL)(\"[^\"\r\n]*\"))$", command) != None:
                log.info("Command received from client %s:%d, command: %s" % (client_addr[0], client_addr[1], command))
                message = command[14:-1]
                answer = self.get_translation(message)
                connection.sendall(bytes(answer, "utf-8"))
                log.info("Answer sent to client %s:%d, answer: %s" % (client_addr[0], client_addr[1], answer))
            elif re.match("^((TRANSLATEPING)(\"[^\"\r\n]*\"))$", command) != None:
                log.info("Command received from client %s:%d, command: %s" % (client_addr[0], client_addr[1], command))
                message = command[14:-1]
                scan_connection = socket.create_connection((self.server_addr[0], self.server_addr[1]), int(configReader.c_timeouts["ping_timeout"]))
                answer = self.get_program(scan_connection)
                connection.sendall(bytes(str(answer), "utf-8"))
                scan_connection.shutdown(0)
                scan_connection.close()
                log.info("Answer sent to client %s:%d, answer: %s" % (client_addr[0], client_addr[1], answer))
            elif re.match("^((TRANSLATESCAN)(\"[^\"\r\n]*\"))$", command) != None:
                log.info("Command received from client %s:%d, command: %s" % (client_addr[0], client_addr[1], command))
                message = command[14:-1]
                addresses = list(configReader.c_server["available_addresses"].split(","))
                if self.server_addr[0] not in addresses:
                    addresses.insert(0, self.server_addr[0])
                ports = list(configReader.c_server["available_ports"].split(","))
                if self.server_addr[1] not in ports:
                    ports.insert(0, self.server_addr[1])
                finished = False
                successful = False
                self_scanned = False
                self_scan = True
                for a in addresses:
                    if finished or successful: break
                    for p in ports:
                        try:
                            if self_scan == True:
                                self_scan = False
                                self_scanned = True
                                message = command[14:-1]
                                answer = self.get_translation(message)
                                if re.match("^((TRANSLATESUC)(\"[^\"\r\n]*\"))$", answer) != None:
                                    connection.sendall(bytes(answer, "utf-8"))
                                    finished = True
                                    successful = True
                                    log.info("Translation found at local dictionary")
                                    log.info("Answer sent to client %s:%d, answer: %s" % (client_addr[0], client_addr[1], answer))
                                    break
                            else:
                                server_connection = socket.create_connection((a, int(p)), 5)
                                log.info("Successfully connected to peer: %s:%d" % (server_connection.getpeername()[0], server_connection.getpeername()[1]))
                                server_connection.sendall(bytes("TRANSLATELOCL\"" + message + "\"", "utf-8"))
                                answer = server_connection.recv(4096).decode()
                                if re.match("^((TRANSLATESUC)(\"[^\"\r\n]*\"))$", answer) != None:
                                    connection.sendall(bytes(answer, "utf-8"))
                                    finished: bool = True
                                    successful = True
                                    log.info("Translation found at peer: %s:%d" % (server_connection.getpeername()[0], server_connection.getpeername()[1]))
                                    log.info("Answer sent to client %s:%d, answer: %s" % (client_addr[0], client_addr[1], answer))
                                    log.info("Closing connection to peer %s:%d" % (server_connection.getpeername(),))
                                    server_connection.shutdown(0)
                                    server_connection.close()
                                    break
                                elif re.match("^((TRANSLATEDERR)(\"[^\"\r\n]*\"))$", answer) != None:
                                    # connection.sendall(bytes(answer, "utf-8"))
                                    log.info("Translation was not found at peer: %s:%d" % (server_connection.getpeername()[0], server_connection.getpeername()[1]))
                                    log.info("Closing connection to peer %s:%d" % (server_connection.getpeername(),))
                                    server_connection.shutdown(0)
                                    server_connection.close()

                        except:
                            log.debug("Could not connect to peer: %s:%d" % (a, int(p)))
                            continue

                if successful == False:
                    answer = "TRANSLATEDERR" + "\"" + "nenalezeno " + message + "\""
                    connection.sendall(bytes(answer, "utf-8"))
                    log.info("Answer sent to client %s:%d, answer: %s" % (client_addr[0], client_addr[1], answer))
                if self_scanned == False:
                    log.info("Closing last connection for safety measures, connection: %s:%d" % (server_connection.getpeername()[0], server_connection.getpeername()[1]))
                    server_connection.shutdown(0)
                    server_connection.close()

            elif command == "\r\n":
                pass
            else:
                message = "TRANSLATEDERR\"neznamy prikaz\""
                connection.sendall(bytes(message, "utf-8"))
                log.info("Command not identified from client %s:%d, command: %s" % (client_addr[0], client_addr[1], command))

    def start_server(self):
        try:
            self.server_addr = (configReader.c_server["address"], int(configReader.c_server["port"]))
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.bind(self.server_addr)
            self.server_socket.listen()

            log.info("Server started at ip %s:%d" % (self.server_socket.getsockname()[0], self.server_socket.getsockname()[1]))

            while True:
                connection, client_address = self.server_socket.accept()
                atexit.register(self.close_server, connection)
                # signal.signal(__handler=(signal.SIGINT), target=(self.close_server), args=(connection,))
                # signal.signal(__handler=(signal.SIGTERM), target=(self.close_server), args=(connection,))
                log.info("Client connected from %s:%d" % (client_address[0], client_address[1]))
                client_thread = threading.Thread(target=self.command_listener, args=(connection, client_address))
                client_thread.start()

        except:
            connection.shutdown(0)
            connection.close()

            self.server_socket.shutdown(0)
            self.server_socket.close()

        finally:
            connection.shutdown(0)
            connection.close()

            self.server_socket.shutdown(0)
            self.server_socket.close()

    def get_translation(self, word: str):
        if word in self.word_dictionary:
            return "TRANSLATESUC\"" + self.word_dictionary[word] + "\""
        else:
            return "TRANSLATEDERR" + "\"" + "nenalezeno " + word + "\""

    def get_program(self, scan_con):
        return "TRANSLATEPONG\"" + socket.gethostbyaddr(scan_con.getpeername()[0])[0] + "\""
        # if scan_con.getpeername() != None:
        #     return "TRANSLATEPONG\"" + scan_con.getpeername() + "\""
        # else:
        #     return None

    def close_server(self, con):
        log.info("Client connection closed")
        con.shutdown(0)
        con.close()

        log.info("Server closed")
        self.server_socket.shutdown(0)
        self.server_socket.close()



