from threading import Thread
from time import sleep


class Session(Thread):

    def __init__(self, client_info, lobby, match_event):

        Thread.__init__(self)
        self.daemon = True

        self.match = None
        self.client = client_info[0]
        self.client_address = client_info[1]
        self.lobby = lobby
        self.match_event = match_event

    def run(self):

        print("Session Started")

        # Find match immediately - testing purposes
        self.find_match()
        self.client.close()

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


class Match(Thread):

    def __init__(self, clients):

        Thread.__init__(self)
        self.daemon = True

        self.clients = clients

    def run(self):
        print("Handle match logic here")