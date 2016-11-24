import pymysql
from pymysql.cursors import DictCursor
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
    END_MATCH = 9

    OP_CAT = 49
    GAIN_HP = 50
    OP_GAIN_HP = 51
    DMG_MODIFIED = 52
    OP_DMG_MODIFIED = 53
    GAIN_CHANCE = 54
    OP_GAIN_CHANCE = 55
    GAIN_ABILITY = 56

    NEXT_PHASE = 98
    READY = 99
    SELECT_CAT = 100
    USE_ABILITY = 101
    TARGET = 102


class Request:

    def __init__(self, flag, token, size):

        self.flag = flag
        self.token = token
        self.size = size


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

    @staticmethod
    def parse_request(data):

        flag = data[0]
        token = data[1:25].decode('utf-8')
        size = int.from_bytes(data[25:28], byteorder='big')

        request = Request(flag, token, size)
        return request

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
