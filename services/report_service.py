from repositories import book_repository, loan_repository, report_repository
from services import loan_service
from utils import fines


def overdue_report():
    items = []
    total = 0
    for row in report_repository.list_open_loans_with_details():
        days_late = fines.days_late(row["due_date"])
        if days_late > 0:
            fine = fines.fine_for(row["due_date"])
            total += fine
            items.append(
                {"loan_id": row["id"], "title": row["title"], "member": row["name"], "days_late": days_late, "fine": fine}
            )
    return items, total


def summary_report():
    loans = loan_repository.list_loans()
    total_books = book_repository.count_books()
    on_loan = loan_service.count_open_loans(loans)
    outstanding = loan_service.total_owed(loans)
    return total_books, on_loan, outstanding
