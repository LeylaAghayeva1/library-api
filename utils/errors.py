class LibraryError(Exception):
    def __init__(self, message, status):
        super().__init__(message)
        self.message = message
        self.status = status


def error(message, status):
    return LibraryError(message, status)