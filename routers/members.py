from flask import Blueprint, jsonify, request

from services import member_service
from utils.fines import money

members_bp = Blueprint("members", __name__)


def member_json(member):
    return {"id": member["id"], "name": member["name"], "email": member["email"], "type": member["type"]}


@members_bp.route("/members", methods=["GET"])
def list_members():
    return jsonify([member_json(member) for member in member_service.list_members()])


@members_bp.route("/members/<int:member_id>", methods=["GET"])
def get_member(member_id):
    return jsonify(member_json(member_service.get_member(member_id)))


@members_bp.route("/members", methods=["POST"])
def create_member():
    data = request.get_json(silent=True) or {}
    return jsonify(member_json(member_service.create_member(data))), 201


@members_bp.route("/members/<int:member_id>/loans", methods=["GET"])
def member_loans(member_id):
    loans, owed, remaining = member_service.member_account(member_id)
    result = []
    for loan in loans:
        result.append(
            {
                "id": loan["id"],
                "book_id": loan["book_id"],
                "due_date": loan["due_date"],
                "returned": bool(loan["returned"]),
                "fine": money(loan["fine"]),
                "fine_paid": bool(loan["fine_paid"]),
            }
        )
    return jsonify({"loans": result, "total_owed": money(owed), "loans_remaining": remaining})
