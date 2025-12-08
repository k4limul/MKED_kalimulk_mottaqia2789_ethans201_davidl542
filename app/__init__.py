'''
Kalimul Kaif, David Lee, Ethan Saldanha, Mottaqi Abedin
MKED
SoftDev 2025
P01 -- ArRESTed Development
2025-12-22
Time spent: 0 hr
'''
from flask import Flask, request, session, redirect, url_for, render_template
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

def initialize_db():
  db = sqlite3.connect(DB_FILE)
  c = db.cursor()
  
  c.execute("CREATE TABLE IF NOT EXISTS users(username TEXT, password TEXT, email TEXT, creation_date DATE);")
  c.execute("CREATE TABLE IF NOT EXISTS saved_locations(id TEXT, username TEXT, state TEXT, city TEXT, job_title TEXT, avg_salary INTEGER, weather_condition TEXT, date_saved DATE);")
  c.execute("CREATE TABLE IF NOT EXISTS search_history(id TEXT, username TEXT, timestamp DATE, job_title TEXT, filters_applied TEXT);")

  db.commit()
  db.close()

@app.route("/", methods=['GET', 'POST'])
def index():
  return render_template('login.html')

@app.route("/login", methods=["GET", "POST"])
def login():
    return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    return "<h1>temp</h1>"

if __name__ == "__main__":
  app.debug = True
  app.run()