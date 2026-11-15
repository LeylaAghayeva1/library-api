from repositories import book_repository
from utils import checks, validation
from utils.errors import error


def list_books(only_available):
    return book_repository.list_books(only_available)


def get_book(book_id):
    book = book_repository.get_book(book_id)
    if book is None:
        raise error("book not found", 404)
    return book


def create_book(data):
    if not data.get("title") or not data.get("author"):
        raise error("title and author are required", 400)
    if not validation.is_valid_isbn(data.get("isbn")):
        raise error("invalid isbn", 400)
    return book_repository.create_book(data["title"], data["author"], data["isbn"])


def delete_book(book_id):
    book = get_book(book_id)
    if not checks.is_available(book):
        raise error("book is on loan", 409)
    book_repository.delete_book(book_id)