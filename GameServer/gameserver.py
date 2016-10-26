#!/usr/bin/python3
# Kittywar game server
# TCP Port 2056

from socket import socket, AF_INET, SOCK_STREAM
from threading import Thread, Event
from queue import Queue
from sessions import *


def main():

    # Create server
    server = socket(AF_INET, SOCK_STREAM)
    server_address = ('localhost', 2056)

    # Prepare lobby and match making thread
    match_event = Event()
    lobby = Queue()

    # Start match making thread
    matchmaker_thread = Thread(target=matchmaker, args=(match_event, lobby))
    matchmaker_thread.daemon = True
    matchmaker_thread.start()

    # Start server and listen for clients
    server.bind(server_address)
    server.listen(5)
    while True:

        client, client_address = server.accept()
        print("Client connected from address: " + client_address[0])
        session = Session((client, client_address), lobby, match_event)
        session.start()


def matchmaker(match_event, lobby):

    while True:

        # Wait until someone queues for a match
        match_event.wait()

        # Check if an opponent is available
        if lobby.qsize() >= 2:

            # Grab two ready clients and pass them to a match thread
            session1 = lobby.get()
            session2 = lobby.get()

            match = Match((session1.client, session2.client))
            session1.match = match
            session2.match = match

            match.start()


if __name__ == "__main__":
    main()
