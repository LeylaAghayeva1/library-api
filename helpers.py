import os
import re
import sqlite3
from datetime import date, timedelta
from flask import Blueprint, jsonify, request

# ---------- helpers ----------
def notify(email ,kind, title="", send=True):
    if not send:
        return
    if kind == "checkout":
        subject = "Book checked out"
        body = "You checked out " + title
    elif kind == "renew":
        subject = "Loan renewed"
        body = "You renewed " + title
    else:
        subject = "Library notice"
        body = title
    with open("outbox.txt", "a") as f:
        f.write("TO: " + email + " | SUBJECT: " + subject + " | BODY: " + body + "\n")

