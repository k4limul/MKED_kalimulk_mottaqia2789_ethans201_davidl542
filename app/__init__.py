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
  if 'username' in session:
    return redirect(url_for('homepage'))
  else:
    text = ""
    return render_template("login.html", text=text)
  return render_template('login.html')

@app.route("/login", methods=["GET", "POST"])
def login():
  if request.method == 'POST':
    username = request.form['username']
    password = request.form['password']
    db = sqlite3.connect(DB_FILE)
    c = db.cursor()
    c.execute("SELECT * FROM users WHERE username = ?", (username,))
    user = c.fetchone()
    db.close()
    
    if user == None or user[0] != username or user[1] != password:
      print("username/password do not match our records")
      text = "login failed, create new acc?"
      return render_template('login.html', text=text)
    elif user[0] == username and user[1] == password:
      session['username'] = username
      return redirect(url_for('homepage'))
    else:
      return redirect(url_for('index'))
  return redirect(url_for('index'))
  return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
  if request.method == 'POST':
    db = sqlite3.connect(DB_FILE)
    c = db.cursor()
    username = request.form['username']
    email = request.form['email']
    password = request.form['password']
    
    cmd = f"SELECT * FROM users WHERE username = '{username}'"
    c.execute(cmd)
    existing_user = c.fetchone()
 
    if existing_user:
      db.close()
      text = "username already taken, try another one!"
      return render_template('register.html', text = text)

    creation_date = int(time.time())

    cmd = f"INSERT into users VALUES ('{username}', '{email}', '{password}', '{creation_date}')"
    c.execute(cmd)
    db.commit()
    db.close()
    session['username'] = username
    return redirect(url_for('homepage'))
  return render_template('register.html')

@app.route("/homepage")
def homepage():
  if 'username' not in session:
    return redirect(url_for('index'))
  db = sqlite3.connect(DB_FILE)
  c = db.cursor()
  db.close()

if __name__ == "__main__":
  initialize_db()
  app.debug = True
  app.run()
