from flask import Blueprint, jsonify, request
from utils import validation
from helpers import *
from repositories import book_repository

book_bp = Blueprint("books", __name__)


def book_json(book):
    return {"id": book["id"], "title": book["title"], "author": book["author"], "isbn": book["isbn"], "available": bool(book["available"])}


@book_bp.route("/books", methods=["GET"])
def list_books():
    rows = book_repository.list_books(request.args.get("available") == "true")
    result = []
    for r in rows:
        result.append(book_json(r))
    return jsonify(result)


@book_bp.route("/books/<int:book_id>", methods=["GET"])
def get_book(book_id):
    r = book_repository.get_book(book_id)
    if r is None:
        return jsonify({"error": "book not found"}), 404
    return jsonify(book_json(r))


@book_bp.route("/books", methods=["POST"])
def create_book():
    data = request.get_json(silent=True) or {}
    if not data.get("title") or not data.get("author"):
        return jsonify({"error": "title and author are required"}), 400
    if not validation.is_valid_isbn(data.get("isbn")):
        return jsonify({"error": "invalid isbn"}), 400
    r = book_repository.create_book(data["title"], data["author"], data["isbn"])
    return jsonify(book_json(r)), 201


@book_bp.route("/books/<int:book_id>", methods=["DELETE"])
def delete_book(book_id):
    r = book_repository.get_book(book_id)
    if r is None:
        return jsonify({"error": "book not found"}), 404
    if r["available"] == 0:
        return jsonify({"error": "book is on loan"}), 409
    book_repository.delete_book(book_id)
    return "", 204