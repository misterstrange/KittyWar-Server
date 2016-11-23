from queue import Queue


class Logger:
    _log_queue = Queue()

    @staticmethod
    def log(message):
        Logger._log_queue.put(message)

    @staticmethod
    def log_count():
        return Logger._log_queue.qsize()

    @staticmethod
    def retrieve():
        return Logger._log_queue.get()
