import socket

client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)


message: str = 'test'

try:
    client_socket.connect(("127.0.0.1", 1234))
    client_socket.send(bytes(message, "utf-8"))
    print("Message sent")
except:
    print("Error")