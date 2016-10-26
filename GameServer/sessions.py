from threading import Thread
from time import sleep
import pymysql


class GameThread(Thread):

    def __init__(self):

        Thread.__init__(self)
        self.daemon = True

    @staticmethod
    def receive_data(client, data_size):

        received_data = bytearray()
        while len(received_data) < data_size:

            packet = client.recv(data_size - len(received_data))

            if not packet:
                return None

            received_data += packet

        return received_data

    @staticmethod
    def parse_request(data):

        flag = data[0]
        token = data[1:25].decode('utf-8')
        size = int.from_bytes(data[25:28], byteorder='big')

        return flag, token, size

    @staticmethod
    def database_connection():
        return pymysql.connect(
            host='69.195.124.204', user='deisume_kittywar',
            password='kittywar', db='deisume_kittywar', autocommit=True)


class Session(GameThread):

    def __init__(self, client_info, lobby, match_event):

        GameThread.__init__(self)

        self.authenticated = False
        self.userident = []
        self.client = client_info[0]
        self.client_address = client_info[1]

        self.lobby = lobby
        self.match_event = match_event
        self.match = None

    def run(self):

        print("Session started")

        while True:

            # Receive flag and incoming data size
            data = self.receive_data(self.client, 28)
            if data is None: break

            request = self.parse_request(data)
            status = self.process_request(request)
            if not status: break

            break;

        if self.authenticated: self.process_request((1, 0, 0))
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

        flag = request[0]

        # log in
        if flag == 0:

            username = self.receive_data(self.client, request[2])
            if username is None: return False;
            username = username.decode('utf-8')

            sql = [
                'SELECT id FROM auth_user WHERE username=%s;',
                'SELECT token FROM KittyWar_userprofile WHERE user_id=%s;'
            ]

            db = self.database_connection()
            try:
                with db.cursor() as cursor:

                    cursor.execute(sql[0], username)
                    result = cursor.fetchone()
                    cursor.execute(sql[1], result)
                    token = cursor.fetchone()

            finally:
                db.close()

            if request[1] == token[0]:

                self.userident.append(username)
                self.userident.append(result[0])
                self.userident.append(token[0])
                self.authenticated = True

                print(self.userident[0] + ' authenticated')

        # log out
        elif flag == 1:

            sql = "UPDATE KittyWar_userprofile SET token='' WHERE user_id=%s;"

            db = self.database_connection()
            try:
                with db.cursor() as cursor:
                    cursor.execute(sql, self.userident[1])

            finally:
                db.close()

        return True


class Match(GameThread):

    def __init__(self, clients):

        GameThread.__init__(self)

        self.clients = clients

    def run(self):
        print("Handle match logic here")
