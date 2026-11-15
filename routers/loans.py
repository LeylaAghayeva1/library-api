from flask import Blueprint, jsonify, request

from services import loan_service
from utils.fines import money

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


def loan_json_with_fine(loan):
    item = loan_json(loan)
    item["current_fine"] = money(loan_service.current_fine(loan))
    return item


@loans_bp.route("/loans", methods=["GET"])
def list_loans():
    only_overdue = request.args.get("overdue") == "true"
    result = []
    for loan in loan_service.list_loans(only_overdue):
        result.append(loan_json_with_fine(loan))
    return jsonify(result)


@loans_bp.route("/loans/<int:loan_id>", methods=["GET"])
def get_loan(loan_id):
    return jsonify(loan_json_with_fine(loan_service.get_loan(loan_id)))


@loans_bp.route("/loans", methods=["POST"])
def create_loan():
    data = request.get_json(silent=True) or {}
    return jsonify(loan_json(loan_service.create_loan(data))), 201


@loans_bp.route("/loans/<int:loan_id>/return", methods=["POST"])
def return_book(loan_id):
    return jsonify(loan_json(loan_service.return_book(loan_id)))


@loans_bp.route("/loans/<int:loan_id>/renew", methods=["POST"])
def renew_loan(loan_id):
    return jsonify(loan_json(loan_service.renew_loan(loan_id)))


@loans_bp.route("/loans/<int:loan_id>/pay-fine", methods=["POST"])
def pay_fine(loan_id):
    return jsonify(loan_json(loan_service.pay_fine(loan_id)))
