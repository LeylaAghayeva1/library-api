from flask import Blueprint, jsonify

from services import report_service
from utils.fines import money

reports_bp = Blueprint("reports", __name__)


@reports_bp.route("/reports/overdue", methods=["GET"])
def report_overdue():
    items, total = report_service.overdue_report()
    for item in items:
        item["fine"] = money(item["fine"])
    return jsonify({"items": items, "total_fines": money(total)})


@reports_bp.route("/reports/summary", methods=["GET"])
def report_summary():
    total_books, on_loan, outstanding = report_service.summary_report()
    return jsonify({"total_books": total_books, "on_loan": on_loan, "fines_outstanding": money(outstanding)})
