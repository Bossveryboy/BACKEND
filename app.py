from flask import Flask, jsonify,request
import sqlite3
import hashlib
import os
from dotenv import load_dotenv
from functools import wraps
from flask_cors import CORS


load_dotenv()
API_TOKEN = os.getenv("API_TOKEN")
app = Flask(__name__)
CORS(app) 
def require_token(f):
     @wraps(f)
     def decorated_function(*args,**kwargs):
          token = request.headers.get("Authorization")
          if token != f"Bearer {API_TOKEN}":
               return jsonify({"message":"Unauthorization"}) , 401
          return f(*args, **kwargs)
     return decorated_function

def get_db_connection(name):
     change_name=name + ".db"
     import os
     BASE_DIR = os.path.dirname(os.path.abspath(__file__))
     db_path = os.path.join(BASE_DIR,change_name)
     conn = sqlite3.connect(db_path)
     conn.row_factory = sqlite3.Row
     return conn
@app.route('/init/<name>',methods= ['GET'])
def init_db(name):
     conn = get_db_connection(name)
     if name == "products":
          conn.execute("""
                    CREATE TABLE IF NOT EXISTS products(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL
                    )
                         """)
     if name == "users":
          conn.execute("""
                         CREATE TABLE IF NOT EXISTS users(
                         id INTEGER PRIMARY KEY AUTOINCREMENT,
                         username TEXT UNIQUE NOT NULL,
                         password TEXT NOT NULL
                         )
                              """)
     conn.commit()
     conn.close()
     return jsonify({"message":"database connected"})
@app.route('/')
def hello():
     return jsonify({"message":"hello everyone"})


@app.route('/products',methods=['GET'])
def get_products():
     if request.method == 'GET':
          conn = get_db_connection("products")
          rows = conn.execute("SELECT * FROM products").fetchall()
          conn.close()
          return jsonify([dict(row) for row in rows]) ,200
     
@app.route('/products',methods=['POST'])
@require_token
def add_products():
     data = request.get_json()
     conn = get_db_connection("products")
     cursor = conn.cursor()
     name = data.get("name")
     cursor.execute("INSERT INTO products(name) VALUES(?)",(name,) )
     conn.commit()
     new_id = cursor.lastrowid
     conn.close()
     new_product ={
          "id": new_id,
          "name": name
          }
     return jsonify({"message":"added ok","product added":new_product}),201

@app.route('/register',methods=['POST'])
def register():
     data = request.get_json()
     username = data.get("username")
     password = data.get("password")

     if not username or not password :
          return jsonify({"message":"error missing "}) ,400
     hashed_password = hashlib.sha256(password.encode()).hexdigest()

     try:
          conn = get_db_connection("users")
          conn.execute("INSERT INTO users(username,password) VALUES(?,?)",(username,hashed_password))
          conn.commit()
          conn.close()
          return jsonify({"message":"Register successfully"}), 201 
     except  sqlite3.IntegrityError :
          return jsonify({"error":"username already exists"}) , 409
@app.route('/login',methods=['POST'])
def login():
     data = request.get_json()
     username= data.get("username")
     password= data.get("password")
     if not username or not password : 
          return jsonify({"message":"missing"}) , 400
     hash_password = hashlib.sha256(password.encode()).hexdigest()
     conn = get_db_connection("users")
     user = conn.execute("SELECT * FROM users WHERE username=? AND password = ?",(username,hash_password)).fetchone()
     conn.close()
     if user :
          return jsonify({"message": f"welcome{username}"}) , 200 
     else :
          return jsonify({"message":"invalid credentials"}) , 401
if (__name__=="__main__"):
     app.run(debug=True)
