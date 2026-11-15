# This is a MOCK of a real email service.
# A real app would connect to a mail server here.
# Our mock just writes each email as one line in outbox.txt,
# so we (and the tests) can see what would have been sent.

OUTBOX_PATH = "outbox.txt"


def send_email(email, subject, body):
    with open(OUTBOX_PATH, "a") as f:
        f.write("TO: " + email + " | SUBJECT: " + subject + " | BODY: " + body + "\n")