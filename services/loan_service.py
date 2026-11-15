from datetime import date, timedelta

from repositories import book_repository, loan_repository, member_repository
from utils import fines, notifications, validation
from utils.errors import error
from utils.fines import money

LOAN_DAYS = 14
STUDENT_LIMIT = 3
STAFF_LIMIT = 5


# ---------- small rules (used by other services too) ----------


def loan_limit(member):
    if member["type"] == "staff":
        return STAFF_LIMIT
    return STUDENT_LIMIT


def amount_owed(loan):
    if loan["returned"] == 0:
        return fines.fine_for(loan["due_date"])
    if loan["fine_paid"] == 0:
        return loan["fine"]
    return 0


def total_owed(loans):
    total = 0
    for loan in loans:
        total += amount_owed(loan)
    return total


def count_open_loans(loans):
    count = 0
    for loan in loans:
        if loan["returned"] == 0:
            count += 1
    return count


def current_fine(loan):
    if loan["returned"] == 0:
        return fines.fine_for(loan["due_date"])
    return loan["fine"]


def is_overdue(loan):
    return loan["returned"] == 0 and fines.days_late(loan["due_date"]) > 0


# ---------- one function per route ----------


def list_loans(only_overdue):
    loans = loan_repository.list_loans()
    if only_overdue:
        result = []
        for loan in loans:
            if is_overdue(loan):
                result.append(loan)
        return result
    return loans


def get_loan(loan_id):
    loan = loan_repository.get_loan(loan_id)
    if loan is None:
        raise error("loan not found", 404)
    return loan


def create_loan(data):
    if not data.get("book_id") or not data.get("member_id"):
        raise error("book_id and member_id are required", 400)
    if data.get("due_date") and not validation.is_valid_date(data["due_date"]):
        raise error("invalid due_date", 400)

    book = book_repository.get_book(data["book_id"])
    if book is None:
        raise error("book not found", 404)
    member = member_repository.get_member(data["member_id"])
    if member is None:
        raise error("member not found", 404)
    if book["available"] == 0:
        raise error("book is not available", 409)

    loans = loan_repository.list_loans_for_member(member["id"])
    if total_owed(loans) > 0:
        raise error("member has unpaid fines", 409)
    if count_open_loans(loans) >= loan_limit(member):
        raise error("loan limit reached", 409)

    today = date.today()
    due_date = data.get("due_date") or (today + timedelta(days=LOAN_DAYS)).isoformat()
    loan = loan_repository.create_loan(book["id"], member["id"], due_date, today.isoformat())

    notifications.send_email(member["email"], "Book checked out", "You checked out " + book["title"])
    return loan


def return_book(loan_id):
    loan = get_loan(loan_id)
    if loan["returned"] == 1:
        raise error("loan already returned", 409)

    fine = fines.fine_for(loan["due_date"])
    loan_repository.mark_returned(loan_id, loan["book_id"], fine)

    member = member_repository.get_member(loan["member_id"])
    book = book_repository.get_book(loan["book_id"])
    notifications.send_email(
        member["email"],
        "Book returned",
        "You returned " + book["title"] + ". Fine: $" + str(money(fine)),
    )
    return loan_repository.get_loan(loan_id)


def renew_loan(loan_id):
    loan = get_loan(loan_id)
    if loan["returned"] == 1:
        raise error("loan already returned", 409)
    if date.fromisoformat(loan["due_date"]) < date.today():
        raise error("overdue loans cannot be renewed", 409)
    if loan["renewals"] >= 1:
        raise error("loan was already renewed", 409)

    new_due = (date.fromisoformat(loan["due_date"]) + timedelta(days=LOAN_DAYS)).isoformat()
    loan_repository.extend_loan(loan_id, new_due)

    member = member_repository.get_member(loan["member_id"])
    book = book_repository.get_book(loan["book_id"])
    notifications.send_email(member["email"], "Loan renewed", "You renewed " + book["title"])
    return loan_repository.get_loan(loan_id)


def pay_fine(loan_id):
    loan = get_loan(loan_id)
    if loan["returned"] == 0:
        raise error("return the book before paying", 409)
    if loan["fine"] <= 0 or loan["fine_paid"] == 1:
        raise error("no fine to pay", 409)

    loan_repository.mark_fine_paid(loan_id)

    member = member_repository.get_member(loan["member_id"])
    notifications.send_email(member["email"], "Fine paid", "We received $" + str(money(loan["fine"])))
    return loan_repository.get_loan(loan_id)
