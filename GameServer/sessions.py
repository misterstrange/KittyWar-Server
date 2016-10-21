from threading import Thread
from time import sleep
from struct import pack, unpack
import MySQLdb
import re


class GameThread(Thread):

    def __init__(self):

        Thread.__init__(self)
        self.daemon = True

    @staticmethod
    def receive_data(client, data_size):

        received_data = b''
        while len(received_data) < data_size:

            packet = client.recv(data_size - len(received_data))

            if not packet:
                return None

            received_data += packet

        return received_data

    @staticmethod
    def process_data(data):

        data = unpack('!I', data)[0]
        flag = 0xff000000 & data
        flag >>= 24
        size = 0x00ffffff & data

        return flag, size

    @staticmethod
    def database_connection():
        return MySQLdb.connect('69.195.124.204', 'deisume_kittywar', 'kittywar', 'deisume_kittywar')


class Session(GameThread):

    def __init__(self, client_info, lobby, match_event):

        GameThread.__init__(self)

        self.match = None
        self.client = client_info[0]
        self.client_address = client_info[1]
        self.lobby = lobby
        self.match_event = match_event

    def run(self):

        print("Session started")

        while True:

            # Receive flag and incoming data size
            data = self.receive_data(self.client, 4)
            if data is None: break

            request = self.process_data(data)
            status = self.process_request(request)
            if not status: break

        print("Client disconnected")
        self.client.close()

    # Finds match and records match results once match is finished
    def find_match(self):

        print("Finding match")
        self.lobby.put(self)

        # Periodically notify matchmaker until match is found
        while self.match is None:

            self.match_event.set()
            self.match_event.clear()
            sleep(1)

        # Wait until match is over to continue session
        self.match.join()

        # Record match logic etc

    def process_request(self, request):

        data = self.receive_data(self.client, request[1])
        if data is None: return 0

        data = data.decode('utf-8')
        print(data)

        flag = request[0]
        if flag == 0:

            expr = "^username=(.+)&password=(.+)$"
            match = re.search(expr, data)
            print(match.group(1))
            print(match.group(2))

        return 1


class Match(GameThread):

    def __init__(self, clients):

        GameThread.__init__(self)

        self.clients = clients

    def run(self):
        print("Handle match logic here")
