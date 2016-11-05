from threading import Thread
from time import sleep
from enum import IntEnum
import gameserver
import pymysql


# Enum to map flag literals to a name
class Flags(IntEnum):

    FAILURE = 0
    SUCCESS = 1

    LOGIN = 0
    LOGOUT = 1
    FIND_MATCH = 2

    def packet(self):
        return self.value & 0xFF


# Generic game thread for session and match threads / holds basic functionality between the two
class GameThread(Thread):

    def __init__(self):

        Thread.__init__(self)
        self.daemon = True

    @staticmethod
    # Translates an int to 3 bytes
    def int_3byte(num):
            return num & 0xFFFFFF

    @staticmethod
    # Creates response header with flag and size
    def generate_response(flag, size):

        response = bytearray()
        response.append(flag)
        response.append(size)
        return response

    # Receives a fixed amount of data from client or returns none if error receiving
    @staticmethod
    def receive_data(client, data_size):

        received_data = bytearray()
        while len(received_data) < data_size:

            packet = client.recv(data_size - len(received_data))

            if not packet:
                return None

            received_data += packet

        return received_data

    # Sends a response to client based on previous request
    @staticmethod
    def send_data(client, data):

        try:
            client.sendall(data)
        except:
            print("Error sending data, closed connection")

    @staticmethod
    def parse_request(data):

        flag = data[0]
        token = data[1:25].decode('utf-8')
        size = int.from_bytes(data[25:28], byteorder='big')

        return flag, token, size

    @staticmethod
    def sql_query(query, string_insert):

        db_connection = pymysql.connect(
            host='69.195.124.204', user='deisume_kittywar',
            password='kittywar', db='deisume_kittywar', autocommit=True)

        try:
            with db_connection.cursor() as cursor:

                cursor.execute(query, string_insert)
                result = cursor.fetchone()

        finally:
            db_connection.close()

        return result


class Session(GameThread):

    def __init__(self, client_info, lobby, match_event):

        GameThread.__init__(self)

        self.authenticated = False
        self.useridentity = []
        self.client = client_info[0]
        self.client_address = client_info[1]

        self.lobby = lobby
        self.match_event = match_event
        self.match = None

    # Session Thread loop - runs until server is being shutdown or client disconnects
    def run(self):

        gameserver.message_queue.put("New session started")

        while True:

            # Receive flag and incoming data size
            data = self.receive_data(self.client, 28)
            if data is None:
                break

            # Process clients request and check if successful
            request = self.parse_request(data)
            successful = self.process_request(request)
            if not successful:
                break

        # If the user has disconnected and was authenticated force logout
        if self.authenticated:
            self.logout()

        #System.message_queue.put("Client disconnected")
        #System.message_queue.put("Session thread " + str(self.ident) + " ending")
        self.client.close()

    def process_request(self, request):

        success = True
        flag = request[0]

        # Login
        if flag == Flags.LOGIN:
            success = self.login(request)

        # Logout
        elif flag == Flags.LOGOUT:
            success = self.logout()

        # Find match
        elif flag == Flags.FIND_MATCH:
            success = self.find_match()

        return success

    # Verifies user has actually logged through token authentication
    def login(self, request):

        # Prepare a client response in the event it is needed
        response = self.generate_response(Flags.LOGIN.packet(), self.int_3byte(1))

        username = self.receive_data(self.client, request[2])
        if username is None:
            return False
        username = username.decode('utf-8')

        sql_stmts = [
            'SELECT id FROM auth_user WHERE username=%s;',
            'SELECT token FROM KittyWar_userprofile WHERE user_id=%s;'
        ]

        user_id = self.sql_query(sql_stmts[0], username)
        if user_id is not None:

            token = self.sql_query(sql_stmts[1], user_id)
            if request[1] == token[0]:

                self.useridentity.append(username)
                self.useridentity.append(user_id[0])
                self.useridentity.append(token[0])
                self.authenticated = True

                #System.message_queue.put(username + " authenticated")
                response.append(Flags.SUCCESS.packet())

            else:
                #System.message_queue.put(username + " failed authentication")
                response.append(Flags.FAILURE.packet())

            self.send_data(self.client, response)

        else:
            #System.message_queue.put("Username does not exist, closing connection")
            return False

        return True

    # Logs the user out by deleting their token and ending the session
    def logout(self):

        # Generate response to notify logout completed
        response = self.generate_response(Flags.LOGOUT.packet(), self.int_3byte(1))

        if self.authenticated:

            sql_stmt = "UPDATE KittyWar_userprofile SET token='' WHERE user_id=%s;"
            self.sql_query(sql_stmt, self.useridentity[1])
            self.authenticated = False

            #System.message_queue.put(self.useridentity[0] + " logging out and closing connection")

            response.append(Flags.SUCCESS.packet())
            self.send_data(self.client, response)

        else:
            response.append(Flags.FAILURE.packet())
            self.send_data(self.client, response)

        return False

    # Finds a match and records match results once match is finished
    def find_match(self):

        #System.message_queue.put(self.useridentity[0] + " is finding a match")
        self.lobby.put(self)

        # Periodically notify matchmaker until match is found
        while self.match is None:

            self.match_event.set()
            self.match_event.clear()
            sleep(1)

        # Wait until match is over to continue session
        self.match.join()

        return False
        # Record match logic etc


class Match(GameThread):

    def __init__(self, clients):

        GameThread.__init__(self)

        self.clients = clients

    def run(self):
        print("Handle match logic here")
