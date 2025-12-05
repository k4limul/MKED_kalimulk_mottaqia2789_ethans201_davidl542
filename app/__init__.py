'''
Kalimul Kaif, David Lee, Ethan Saldanha, Mottaqi Abedin
MKED
SoftDev 2025
P01 -- ArRESTed Development
2025-12-22
Time spent: 0 hr
'''
from flask import Flask
from flask import request
from flask import session
from flask import redirect
from flask import url_for
import csv
import sqlite3
import random
import time
from datetime import datetime

app = Flask(__name__)

app.secret_key = "secret_key_testing"
DB_FILE = "api_website.db"
