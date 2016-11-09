from threading import Thread
from time import sleep
from enum import IntEnum
import socket as sock
import pymysql


# Enum to map flag literals to a name
class Flags(IntEnum):

    FAILURE = 0
    SUCCESS = 1

    LOGIN = 0
    LOGOUT = 1
    FIND_MATCH = 2
    USER_PROFILE = 3

    def packet(self):
        return self.value & 0xFF


# Generic game thread for session and match threads / holds basic functionality between the two
class GameThread(Thread):

    server_running = True

    # Variables used by all sessions that must be set for it to work
    log_queue = None
    lobby = None
    match_event = None

    def __init__(self):

        Thread.__init__(self)
        self.daemon = False

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

        packet = b''
        received_data = bytearray()
        while len(received_data) < data_size:

            try:
                packet = client.recv(data_size - len(received_data))
            except ConnectionResetError:
                pass

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
            pass

    @staticmethod
    def parse_request(data):

        flag = data[0]
        token = data[1:25].decode('utf-8')
        size = int.from_bytes(data[25:28], byteorder='big')

        request = {'flag': flag, 'token': token, 'size': size}
        return request

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

    def __init__(self, client_info):

        GameThread.__init__(self)

        self.authenticated = False
        self.userinfo = {'username': 'Anonymous'}
        self.client = client_info[0]
        self.client_address = client_info[1]

        self.match = None

    # Session Thread loop - runs until server is being shutdown or client disconnects
    def run(self):

        self.log_queue.put("New session started")

        while self.server_running:

            # Receive flag and incoming data size
            data = self.receive_data(self.client, 28)
            if data is None:
                break

            # Process clients request and check if successful
            request = self.parse_request(data)
            successful = self.process_request(request)
            if not successful:
                break

        # Start shutting down session thread
        self.logout()
        self.kill()
        self.client.close()

        self.log_queue.put(self.userinfo['username'] + " disconnected")
        self.log_queue.put("Session thread for " + self.userinfo['username'] + " ending")

    def kill(self):

        try:
            self.client.shutdown(sock.SHUT_RDWR)
        except OSError:
            pass

        GameThread.server_running = False

    def process_request(self, request):

        self.log_queue.put("Request: " + str(request))

        success = True
        flag = request['flag']

        # Login
        if flag == Flags.LOGIN:
            success = self.login(request)

        # Logout
        elif flag == Flags.LOGOUT:
            success = self.logout()

        # Find match
        elif flag == Flags.FIND_MATCH:
            success = self.find_match()

        # Grab user profile information
        elif flag == Flags.USER_PROFILE:
            success = self.user_profile()

        return success

    # Verifies user has actually logged through token authentication
    def login(self, request):

        # Prepare client response
        response = self.generate_response(Flags.LOGIN.packet(), self.int_3byte(1))

        # Retreive username from request body
        username = self.receive_data(self.client, request['size'])

        # If the user does not send username or connection error close connection
        if username is None:
            return False

        # Convert username to string by decoding
        username = username.decode('utf-8')
        self.log_queue.put(username)
        self.userinfo['username'] = username

        sql_stmts = [
            'SELECT id FROM auth_user WHERE username=%s;',
            'SELECT token FROM KittyWar_userprofile WHERE user_id=%s;'
        ]

        # Retreive user id tied to username
        user_id = self.sql_query(sql_stmts[0], username)
        if user_id is not None:

            # With user id query users login token
            token = self.sql_query(sql_stmts[1], user_id)
            if token is not None and request['token'] == token[0]:

                self.userinfo['userid'] = user_id[0]
                self.userinfo['token'] = token[0]
                self.authenticated = True

                self.log_queue.put(username + " authenticated")
                response.append(Flags.SUCCESS.packet())

            else:
                self.log_queue.put(username + " failed authentication")
                response.append(Flags.FAILURE.packet())

        else:
            # Username is verified through django server so force close connection
            self.log_queue.put("No username/id found for " + username +
                               ", force closing connection")
            return False

        self.send_data(self.client, response)
        return True

    # Logs the user out by deleting their token and ending the session
    def logout(self):

        # Generate response to notify logout completed
        response = self.generate_response(Flags.LOGOUT.packet(), self.int_3byte(1))

        if self.authenticated:

            sql_stmt = "UPDATE KittyWar_userprofile SET token='' WHERE user_id=%s;"
            self.sql_query(sql_stmt, self.userinfo['userid'])
            self.authenticated = False

            self.log_queue.put(self.userinfo['username'] + " logged out")
            response.append(Flags.SUCCESS.packet())

        else:
            response.append(Flags.FAILURE.packet())

        self.send_data(self.client, response)
        return False

    # Grab user profile information from database and send back to the client
    def user_profile(self):

        sql_stmts = []
        return True

    # Finds a match and records match results once match is finished
    def find_match(self):

        self.log_queue.put(self.userinfo['username'] + " is finding a match")
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
