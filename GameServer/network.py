import pymysql
from pymysql.cursors import DictCursor


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
