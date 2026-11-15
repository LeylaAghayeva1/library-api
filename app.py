import db
import os
import re
import sqlite3
from datetime import date, timedelta
from flask import Flask, jsonify, request
from routers.book import book_bp
from routers.members import members_bp
from routers.loans import loans_bp
from routers.reports import reports_bp
from utils import validation, fines, notifications
from db import init_db
app = Flask(__name__)
app.register_blueprint(book_bp)
app.register_blueprint(members_bp)
app.register_blueprint(loans_bp)
app.register_blueprint(reports_bp)

if not os.path.exists("library.db"):
    db.init_db()
