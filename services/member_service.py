from repositories import loan_repository, member_repository
from services import loan_service
from utils import validation
from utils.errors import error


def list_members():
    return member_repository.list_members()


def get_member(member_id):
    member = member_repository.get_member(member_id)
    if member is None:
        raise error("member not found", 404)
    return member


def create_member(data):
    if not data.get("name"):
        raise error("name is required", 400)
    if not validation.is_valid_email(data.get("email")):
        raise error("invalid email", 400)
    member_type = data.get("type", "student")
    if not validation.is_valid_member_type(member_type):
        raise error("type must be student or staff", 400)
    if member_repository.get_member_by_email(data["email"]) is not None:
        raise error("email already registered", 409)
    return member_repository.create_member(data["name"], data["email"], member_type)


def member_account(member_id):
    member = get_member(member_id)
    loans = loan_repository.list_loans_for_member(member_id)
    owed = loan_service.total_owed(loans)
    remaining = loan_service.loan_limit(member) - loan_service.count_open_loans(loans)
    return loans, owed, remaining
