from datetime import date, timedelta
from helpers import *
from flask import Blueprint, jsonify, request
from repositories import loan_repository, member_repository
members_bp = Blueprint("members", __name__)

def member_json(member):
    return {"id": member["id"], "name": member["name"], "email": member["email"], "type": member["type"]}

@members_bp.route("/members", methods=["GET"])
def list_members():
    members = member_repository.list_members()
    return jsonify([member_json(member) for member in members])


@members_bp.route("/members/<int:member_id>", methods=["GET"])
def get_member(member_id):
    member = member_repository.get_member(member_id)
    if not member:
        return jsonify({"error": "member not found"}), 404
    return jsonify(member_json(member))


@members_bp.route("/members", methods=["POST"])
def create_member():
    data = request.get_json(silent=True) or {}
    if not data.get("name"):
        return jsonify({"error": "name is required"}), 400
    if not check(data.get("email"), "email"):
        return jsonify({"error": "invalid email"}), 400
    member_type = data.get("type", "student")
    if not check(member_type, "member_type"):
        return jsonify({"error": "type must be student or staff"}), 400
    existing = member_repository.get_member_by_email(data["email"])
    if existing is not None:
        return jsonify({"error": "email already registered"}), 409
    r = member_repository.create_member(data["name"], data["email"], member_type)
    return jsonify(member_json(r)), 201


@members_bp.route("/members/<int:member_id>/loans", methods=["GET"])
def member_loans(member_id):
    m = member_repository.get_member(member_id)
    if m is None:
        return jsonify({"error": "member not found"}), 404
    rows = loan_repository.list_loans_for_member(member_id)    
    owed = 0
    open_loans = 0
    loans = []
    for loan in rows:
        if loan[4] == 0:
            open_loans += 1
            days_late = (date.today() - date.fromisoformat(loan[3])).days
            if days_late > 0:
                owed += days_late * 0.5
        elif loan[6] == 0:
            owed += loan[5]
        loans.append(
            {
                "id": loan[0],
                "book_id": loan[1],
                "due_date": loan[3],
                "returned": bool(loan[4]),
                "fine": money(loan[5]),
                "fine_paid": bool(loan[6]),
            }
        )
    if m[3] == "staff":
        remaining = 5 - open_loans
    else:
        remaining = 3 - open_loans
    return jsonify({"loans": loans, "total_owed": money(owed), "loans_remaining": remaining})

# @members_bp.route("/members/<int:member_id>", methods=["DELETE"])
# def delete_member(member_id):
#     conn = db.connect()
#     r = conn.execute("SELECT * FROM members WHERE id = ?", (member_id,)).fetchone()
#     if r is None:
#         conn.close()
#         return jsonify({"error": "member not found"}), 404
#     conn.execute("DELETE FROM members WHERE id = ?", (member_id,))
#     conn.commit()
#     conn.close()
#     return "", 204

