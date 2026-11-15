# Yes/no checks about the library's rules.
# Each function answers one question with True or False.
# (validation.py checks if INPUT is well-formed;
#  checks.py checks the STATE of books and loans.)

from utils import fines


def is_available(book):
    return book["available"] == 1


def is_returned(loan):
    return loan["returned"] == 1


def is_overdue(loan):
    return not is_returned(loan) and fines.days_late(loan["due_date"]) > 0


def was_renewed(loan):
    return loan["renewals"] >= 1


def has_fine_to_pay(loan):
    return loan["fine"] > 0 and loan["fine_paid"] == 0


def has_reached_limit(open_loans, limit):
    return open_loans >= limit
