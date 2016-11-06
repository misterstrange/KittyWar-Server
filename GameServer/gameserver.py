#!/usr/bin/python3
# Kittywar game server
# TCP Port 2056

import socket as sock
from threading import Thread, Event
from queue import Queue
import sessions as session
import tkinter
import tkinter.scrolledtext

server_running = True
log_queue = Queue()


def main():

    # Create server
    server = sock.socket(sock.AF_INET, sock.SOCK_STREAM)
    server_address = ('localhost', 2056)

    # Prepare lobby and match making thread
    match_event = Event()
    lobby = Queue()

    # Start match making thread
    matchmaker_thread = Thread(target=match_maker, args=(match_event, lobby))
    matchmaker_thread.daemon = True
    matchmaker_thread.start()

    # Bind server and listen for clients
    server.bind(server_address)
    server.settimeout(1)
    server.listen(5)

    # Set GameThread variables for debugging and matchmaking to apply to all sessions
    session.GameThread.log_queue = log_queue
    session.GameThread.lobby = lobby
    session.GameThread.match_event = match_event

    # Create thread dedicated to listening for clients
    polling_thread = Thread(target=poll_connections, args=(server,))
    polling_thread.daemon = True
    polling_thread.start()

    # Server GUI code
    root = tkinter.Tk()
    root.geometry("500x500")
    root.title("KittyWar Game Server")

    # Create text display
    server_display = tkinter.scrolledtext.ScrolledText(root)
    server_display.config(state=tkinter.DISABLED)
    server_display.pack()

    # Create shutdown button
    shutdown_button = tkinter.Button(root, text="Shutdown Server", command=shutdown_server)
    shutdown_button.pack()

    # Start GUI and set update to every 100ms
    root.after(100, update_display, (root, server_display))
    root.mainloop()


def update_display(root_display):

    root = root_display[0]
    server_display = root_display[1]

    queue_length = log_queue.qsize()
    for i in range(0, queue_length):

        server_display.config(state=tkinter.NORMAL)
        server_display.insert(tkinter.END, log_queue.get() + "\n")
        server_display.pack()
        server_display.config(state=tkinter.DISABLED)

    root.after(100, update_display, (root, server_display))


def poll_connections(server):

    log_queue.put("Server started")
    connections = []

    while server_running:

        # Occasionlly timeout from polling to check if the server is still running
        try:
            client, client_address = server.accept()
        except sock.timeout:
            continue

        log_queue.put("Client connected from address: " + client_address[0])
        new_session = session.Session((client, client_address))
        new_session.start()

        connections.append(new_session)

    for connection in connections:
        if connection.is_alive():
            connection.kill()

    server.shutdown(sock.SHUT_RDWR)
    server.close()
    log_queue.put("Server stopped")


def match_maker(match_event, lobby):

    while True:

        # Wait until someone queues for a match
        match_event.wait()

        # Check if an opponent is available
        if lobby.qsize() >= 2:

            # Grab two ready clients and pass them to a match thread
            session1 = lobby.get()
            session2 = lobby.get()

            match = session.Match((session1.client, session2.client))
            session1.match = match
            session2.match = match

            match.start()


def shutdown_server():

    log_queue.put("Server stopping")
    global server_running
    server_running = False


if __name__ == "__main__":
    main()
