import db
import os
from flask import Flask, jsonify, request
from routers.book import book_bp
from routers.members import members_bp
from routers.loans import loans_bp
from routers.reports import reports_bp
from db import init_db
from utils.errors import LibraryError
app = Flask(__name__)
@app.errorhandler(LibraryError)
def handle_library_error(err):
    return jsonify({"error": err.message}), err.status
app.register_blueprint(book_bp)
app.register_blueprint(members_bp)
app.register_blueprint(loans_bp)
app.register_blueprint(reports_bp)

if not os.path.exists("library.db"):
    db.init_db()
