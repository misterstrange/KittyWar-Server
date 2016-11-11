import socket as sock
import pymysql

from pymysql.cursors import DictCursor
from threading import Thread
from time import sleep
from enum import IntEnum


# Enum to map flag literals to a name
class Flags(IntEnum):

    FAILURE = 0
    SUCCESS = 1

    LOGIN = 0
    LOGOUT = 1
    FIND_MATCH = 2
    USER_PROFILE = 3
    ALL_CARDS = 4
    CAT_CARDS = 5
    BASIC_CARDS = 6
    CHANCE_CARDS = 7
    ABILITY_CARDS = 8


# Helper class that contains useful network functions
class Network:

    # Translates an int to 3 bytes - returns bytearray object
    @staticmethod
    def int_3byte(num):

        _3byte = bytearray()
        for i in range(0, 3):

            _3byte.insert(0, num & 0xFF)
            num >>= 8

        return _3byte

    # Creates response header with flag and size
    @staticmethod
    def generate_responseh(flag, size):

        response = bytearray()
        response.append(flag)
        response += Network.int_3byte(size)
        return response

    # Creates header with flag and size and attaches response body
    @staticmethod
    def generate_responseb(flag, size, body):

        response = Network.generate_responseh(flag, size)
        response += body.encode('utf-8')
        return response

    # Creates and returns a database connection
    @staticmethod
    def db_connection():
        return pymysql.connect(
            host='69.195.124.204', user='deisume_kittywar',
            password='kittywar', db='deisume_kittywar', autocommit=True)

    # Alternative to db_connection, executes an sql statement for you
    @staticmethod
    def sql_query(query):

        db = Network.db_connection()

        try:
            with db.cursor(DictCursor) as cursor:

                cursor.execute(query)
                result = cursor.fetchall()

        finally:
            db.close()

        return result

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

        # noinspection PyBroadException
        try:
            client.sendall(data)
        except:
            pass


class Session(Thread):

    # Variables used by all sessions that must be set for it to work
    server_running = True

    card_information = None
    log_queue = None
    lobby = None
    match_event = None

    @staticmethod
    def parse_request(data):

        flag = data[0]
        token = data[1:25].decode('utf-8')
        size = int.from_bytes(data[25:28], byteorder='big')

        request = {'flag': flag, 'token': token, 'size': size}
        return request

    def __init__(self, client_info):

        Thread.__init__(self)
        self.daemon = False

        self.authenticated = False
        self.userprofile = {'username': 'Anonymous'}
        self.client = client_info[0]
        self.client_address = client_info[1]

        self.match = None

    # Session Thread loop - runs until server is being shutdown or client disconnects
    def run(self):

        Session.log_queue.put("New session started")

        while self.server_running:

            # Receive flag and incoming data size
            data = Network.receive_data(self.client, 28)
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

        Session.log_queue.put(self.userprofile['username'] + " disconnected")
        Session.log_queue.put(
            "Session thread for " + self.userprofile['username'] + " ending")

    def kill(self):

        try:
            self.client.shutdown(sock.SHUT_RDWR)
        except OSError:
            pass
        self.server_running = False

    def process_request(self, request):

        Session.log_queue.put("Request: " + str(request))

        flag = request['flag']

        '''
        # Check user identity for sensitive operations
        if flag >= Flags.FIND_MATCH:
            if not self.verified(request):
                Session.log_queue.put(
                    self.userprofile['username'] + " is not authorized to use flag " +
                    str(flag) + ", closing this connection")
                return False
        '''

        success = False
        try:
            success = request_map[flag](self, request)
        except KeyError:
            Session.log_queue.put(
                "Server does not support flag " + str(flag)
                + ", closing this connection")

        return success

    def verified(self, request):

        if self.authenticated:
            if request['token'] == self.userprofile['token']:
                return True

        return False

    # Verifies user has actually logged through token authentication
    def login(self, request=None):

        # Prepare client response
        response = Network.generate_responseh(Flags.LOGIN, 1)

        # Retreive username from request body
        username = Network.receive_data(self.client, request['size'])

        # If the user does not send username or connection error close connection
        if username is None:
            return False

        # Convert username to string by decoding
        username = username.decode('utf-8')
        Session.log_queue.put("Body: " + username)
        self.userprofile['username'] = username

        sql_stmts = [
            'SELECT id FROM auth_user WHERE username=\'{}\';',
            'SELECT token FROM KittyWar_userprofile WHERE user_id=\'{}\';'
        ]

        # Retreive user id tied to username
        result = Network.sql_query(sql_stmts[0].format(username))
        if result:

            user_id = result[0]['id']
            # With user id query users login token
            result = Network.sql_query(sql_stmts[1].format(user_id))

            if result and request['token'] == result[0]['token']:

                self.userprofile['userid'] = user_id
                self.userprofile['token'] = result[0]['token']
                self.authenticated = True

                Session.log_queue.put(username + " authenticated")
                response.append(Flags.SUCCESS)

            else:
                Session.log_queue.put(username + " failed authentication")
                response.append(Flags.FAILURE)

        else:
            # Username is verified through django server so force close connection
            Session.log_queue.put(
                "No username/id found for " + username + ", force closing connection")
            return False

        Network.send_data(self.client, response)
        return True

    # Logs the user out by deleting their token and ending the session
    def logout(self, request=None):

        # Generate response to notify logout completed
        response = Network.generate_responseh(Flags.LOGOUT, 1)

        if self.authenticated:

            sql_stmt = 'UPDATE KittyWar_userprofile SET token='' WHERE user_id=\'{}\';'
            Network.sql_query(sql_stmt.format(self.userprofile['userid']))
            self.authenticated = False

            Session.log_queue.put(self.userprofile['username'] + " logged out")
            response.append(Flags.SUCCESS)

        else:
            response.append(Flags.FAILURE)

        Network.send_data(self.client, response)
        return False

    # Grab user profile information from database
    # then save it and send it back to the client
    def user_profile(self, request=None):

        sql_stmts = [
            'SELECT draw,loss,wins,matches FROM KittyWar_userprofile WHERE user_id=\'{}\';',
            'SELECT catcard_id FROM KittyWar_userprofile_cats WHERE userprofile_id=\'{}\';'
        ]

        sql_stmt = sql_stmts[0].format(self.userprofile['userid'])
        records = Network.sql_query(sql_stmt)
        sql_stmt = sql_stmts[1].format(self.userprofile['userid'])
        cats = Network.sql_query(sql_stmt)

        records = records[0]
        records['cats'] = []

        for cat in cats:
            records['cats'].append(cat['catcard_id'])

        self.userprofile['records'] = records

        body = str(records)
        response = Network.generate_responseb(Flags.USER_PROFILE, len(body), body)
        Network.send_data(self.client, response)

        return True

    # Sends all card data to the client
    def all_cards(self, request=None):

        body = str(self.card_information)
        response = Network.generate_responseb(Flags.ALL_CARDS, len(body), body)
        Network.send_data(self.client, response)
        return True

    # Sends all cat card data to the client
    def cat_cards(self, request=None):

        body = str(self.card_information['cats'])
        response = Network.generate_responseb(Flags.CAT_CARDS, len(body), body)
        Network.send_data(self.client, response)
        return True

    # Sends all moveset card data to the client
    def basic_cards(self, request=None):

        body = str(self.card_information['moves'])
        response = Network.generate_responseb(Flags.BASIC_CARDS, len(body), body)
        Network.send_data(self.client, response)
        return True

    # Sends all chance card data to the client
    def chance_cards(self, request=None):

        body = str(self.card_information['chances'])
        response = Network.generate_responseb(Flags.CHANCE_CARDS, len(body), body)
        Network.send_data(self.client, response)
        return True

    # Sends all ability card data to the client
    def ability_cards(self, request=None):

        body = str(self.card_information['abilities'])
        response = Network.generate_responseb(Flags.ABILITY_CARDS, len(body), body)
        Network.send_data(self.client, response)
        return True

    # Finds a match and records match results once match is finished
    def find_match(self, request=None):

        Session.log_queue.put(self.userprofile['username'] + " is finding a match")
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

request_map = {
    Flags.LOGIN: Session.login, Flags.LOGOUT: Session.logout,
    Flags.FIND_MATCH:    Session.find_match,
    Flags.USER_PROFILE:  Session.user_profile,
    Flags.ALL_CARDS:     Session.all_cards,
    Flags.CAT_CARDS:     Session.cat_cards,
    Flags.BASIC_CARDS:   Session.basic_cards,
    Flags.CHANCE_CARDS:  Session.chance_cards,
    Flags.ABILITY_CARDS: Session.ability_cards}
