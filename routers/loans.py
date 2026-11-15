from datetime import date, timedelta

from flask import Blueprint, jsonify, request

from helpers import *
from repositories import book_repository, loan_repository, member_repository

loans_bp = Blueprint("loans", __name__)


def loan_json(loan):
    return {
        "id": loan["id"],
        "book_id": loan["book_id"],
        "member_id": loan["member_id"],
        "due_date": loan["due_date"],
        "returned": bool(loan["returned"]),
        "fine": money(loan["fine"]),
        "fine_paid": bool(loan["fine_paid"]),
        "renewals": loan["renewals"],
        "checked_out": loan["checked_out"],
    }


@loans_bp.route("/loans", methods=["GET"])
def list_loans():
    rows = loan_repository.list_loans()
    result = []
    for loan in rows:
        current_fine = loan["fine"]
        days_late = (date.today() - date.fromisoformat(loan["due_date"])).days
        if loan["returned"] == 0:
            current_fine = max(0, days_late) * 0.50
        if request.args.get("overdue") == "true" and (loan["returned"] == 1 or days_late <= 0):
            continue
        item = loan_json(loan)
        item["current_fine"] = money(current_fine)
        result.append(item)
    return jsonify(result)


@loans_bp.route("/loans/<int:loan_id>", methods=["GET"])
def get_loan(loan_id):
    loan = loan_repository.get_loan(loan_id)
    if loan is None:
        return jsonify({"error": "loan not found"}), 404
    current_fine = loan["fine"]
    if loan["returned"] == 0:
        days_late = (date.today() - date.fromisoformat(loan["due_date"])).days
        current_fine = max(0, days_late) * 0.50
    item = loan_json(loan)
    item["current_fine"] = money(current_fine)
    return jsonify(item)


@loans_bp.route("/loans", methods=["POST"])
def create_loan():
    data = request.get_json(silent=True) or {}
    if not data.get("book_id") or not data.get("member_id"):
        return jsonify({"error": "book_id and member_id are required"}), 400
    if data.get("due_date") and not check(data["due_date"], "date"):
        return jsonify({"error": "invalid due_date"}), 400

    book = book_repository.get_book(data["book_id"])
    if book is None:
        return jsonify({"error": "book not found"}), 404
    member = member_repository.get_member(data["member_id"])
    if member is None:
        return jsonify({"error": "member not found"}), 404
    if book["available"] == 0:
        return jsonify({"error": "book is not available"}), 409

    rows = loan_repository.list_loans_for_member(data["member_id"])
    owed = 0
    open_loans = 0
    for loan in rows:
        if loan["returned"] == 0:
            open_loans += 1
            days_late = (date.today() - date.fromisoformat(loan["due_date"])).days
            if days_late > 0:
                owed += days_late * 0.5
        elif loan["fine_paid"] == 0:
            owed += loan["fine"]
    if owed > 0:
        return jsonify({"error": "member has unpaid fines"}), 409
    limit = 3
    if member["type"] == "staff":
        limit = 5
    if open_loans >= limit:
        return jsonify({"error": "loan limit reached"}), 409

    today = date.today()
    due_date = data.get("due_date") or (today + timedelta(days=14)).isoformat()
    loan = loan_repository.create_loan(data["book_id"], data["member_id"], due_date, today.isoformat())

    notify(member["email"], "checkout", book["title"])

    return jsonify(loan_json(loan)), 201


@loans_bp.route("/loans/<int:loan_id>/return", methods=["POST"])
def return_book(loan_id):
    loan = loan_repository.get_loan(loan_id)
    if loan is None:
        return jsonify({"error": "loan not found"}), 404
    if loan["returned"] == 1:
        return jsonify({"error": "loan already returned"}), 409

    days_late = (date.today() - date.fromisoformat(loan["due_date"])).days
    fine = max(0, days_late) * 0.50
    loan_repository.mark_returned(loan_id, loan["book_id"], fine)
    member = member_repository.get_member(loan["member_id"])
    book = book_repository.get_book(loan["book_id"])
    updated = loan_repository.get_loan(loan_id)

    with open("outbox.txt", "a") as f:
        f.write(
            "TO: " + member["email"] + " | SUBJECT: Book returned | BODY: You returned " + book["title"]
            + ". Fine: $" + str(money(fine)) + "\n"
        )

    return jsonify(loan_json(updated))


@loans_bp.route("/loans/<int:loan_id>/renew", methods=["POST"])
def renew_loan(loan_id):
    loan = loan_repository.get_loan(loan_id)
    if loan is None:
        return jsonify({"error": "loan not found"}), 404
    if loan["returned"] == 1:
        return jsonify({"error": "loan already returned"}), 409
    if date.fromisoformat(loan["due_date"]) < date.today():
        return jsonify({"error": "overdue loans cannot be renewed"}), 409
    if loan["renewals"] >= 1:
        return jsonify({"error": "loan was already renewed"}), 409

    new_due = (date.fromisoformat(loan["due_date"]) + timedelta(days=14)).isoformat()
    loan_repository.extend_loan(loan_id, new_due)
    member = member_repository.get_member(loan["member_id"])
    book = book_repository.get_book(loan["book_id"])
    updated = loan_repository.get_loan(loan_id)

    notify(member["email"], "renew", book["title"])

    return jsonify(loan_json(updated))


@loans_bp.route("/loans/<int:loan_id>/pay-fine", methods=["POST"])
def pay_fine(loan_id):
    loan = loan_repository.get_loan(loan_id)
    if loan is None:
        return jsonify({"error": "loan not found"}), 404
    if loan["returned"] == 0:
        return jsonify({"error": "return the book before paying"}), 409
    if loan["fine"] <= 0 or loan["fine_paid"] == 1:
        return jsonify({"error": "no fine to pay"}), 409

    loan_repository.mark_fine_paid(loan_id)
    member = member_repository.get_member(loan["member_id"])
    updated = loan_repository.get_loan(loan_id)

    with open("outbox.txt", "a") as f:
        f.write(
            "TO: " + member["email"] + " | SUBJECT: Fine paid | BODY: We received $" + str(money(loan["fine"])) + "\n"
        )

    return jsonify(loan_json(updated))