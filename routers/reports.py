from datetime import date, timedelta
from helpers import *
from flask import Blueprint, jsonify, request
from repositories import book_repository, loan_repository, report_repository
from utils import fines
from utils.fines import money
reports_bp = Blueprint("reports", __name__)

@reports_bp.route("/reports/overdue", methods=["GET"])
def report_overdue():
    rows = report_repository.list_open_loans_with_details()
    items = []
    total = 0
    for r in rows:
        days_late = (date.today() - date.fromisoformat(r[3])).days
        if days_late > 0:
            fine = fines.fine_for(r[3])
            total += fine
            items.append(
                {"loan_id": r[0], "title": r[1], "member": r[2], "days_late": days_late, "fine": money(fine)}
            )
    return jsonify({"items": items, "total_fines": money(total)})


@reports_bp.route("/reports/summary", methods=["GET"])
def report_summary():
    total_books = book_repository.count_books()
    rows = loan_repository.list_loans()
    on_loan = 0
    outstanding = 0
    for loan in rows:
        if loan[4] == 0:
            on_loan += 1
            days_late = (date.today() - date.fromisoformat(loan[3])).days
            outstanding += fines.fine_for(loan[3])
        elif loan[6] == 0:
            outstanding += loan[5]
    return jsonify({"total_books": total_books, "on_loan": on_loan, "fines_outstanding": money(outstanding)})
