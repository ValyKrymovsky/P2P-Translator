from src.server import Server
import sys

if __name__ == "__main__":
    server = Server()
    server.start_server()

while True:
    x: str = input()

    if x == "exit":
        sys.exit()
