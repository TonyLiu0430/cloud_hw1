from flask import Flask, request, jsonify, make_response, g
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from dotenv import load_dotenv
import os
import psycopg2
import bcrypt
from datetime import timedelta


load_dotenv()

app = Flask(__name__)
app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY')
app.config['JWT_TOKEN_LOCATION'] = ['cookies']
app.config['JWT_ACCESS_COOKIE_NAME'] = 'Authorization'
app.config['JWT_COOKIE_CSRF_PROTECT'] = False
jwt = JWTManager(app)


@app.route('/')
def home():
    return '''
    <h2>API 測試首頁</h2>
    <ul>
        <li><a href="/login">登入測試</a></li>
        <li><a href="/register">註冊測試</a></li>
        <li><a href="/posts">取得貼文測試</a></li>
        <li><a href="/post/create">發文測試</a></li>
    </ul>
    '''
@app.route('/login')
def login_test():
    return '''
    <h3>登入測試</h3>
    <form method="post" action="/api/login" onsubmit="event.preventDefault(); fetch('/api/login', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({username:login_username.value, password:login_password.value})}).then(r=>r.json()).then(d=>result.innerText=JSON.stringify(d));">
        <input name="username" id="login_username" placeholder="username"><br>
        <input name="password" id="login_password" type="password" placeholder="password"><br>
        <button type="submit">登入</button>
    </form>
    <pre id="result"></pre>
    <a href="/">回首頁</a>
    '''

@app.route('/register')
def register_test():
    return '''
    <h3>註冊測試</h3>
    <form method="post" action="/api/register" onsubmit="event.preventDefault(); fetch('/api/register', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({username:reg_username.value, password:reg_password.value})}).then(r=>r.json()).then(d=>result.innerText=JSON.stringify(d));">
        <input name="username" id="reg_username" placeholder="username"><br>
        <input name="password" id="reg_password" type="password" placeholder="password"><br>
        <button type="submit">註冊</button>
    </form>
    <pre id="result"></pre>
    <a href="/">回首頁</a>
    '''

@app.route('/posts')
def posts_test():
    return '''
    <h3>取得貼文測試</h3>
    <form onsubmit="event.preventDefault(); fetch(`/api/posts?num=${num.value}&end=${end.value}`).then(r=>r.json()).then(d=>result.innerText=JSON.stringify(d));">
        num: <input name="num" id="num" value="5"><br>
        end: <input name="end" id="end" value="20"><br>
        <button type="submit">取得貼文</button>
    </form>
    <pre id="result"></pre>
    <a href="/">回首頁</a>
    '''

@app.route('/post/create')
def post_test():
    return '''
    <h3>發文測試</h3>
    <form onsubmit="event.preventDefault(); fetch('/api/post', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({title:title.value, content:content.value})}).then(r=>r.json()).then(d=>result.innerText=JSON.stringify(d));">
        title: <input name="title" id="title"><br>
        content: <input name="content" id="content"><br>
        <button type="submit">發文</button>
    </form>
    <pre id="result"></pre>
    <a href="/">回首頁</a>
    '''

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data['username']
    password = data['password']
    if username is None or password is None:
        return bad_request('Missing Parameter `username` or `password`')
    db = g.db_conn
    cur = db.cursor()
    cur.execute("SELECT id, password FROM users WHERE username = %s", (username,))
    row = cur.fetchone()
    app.logger.debug(f"row: {row}")
    cur.close()
    if row is None:
        return bad_request(f'User {username} does not exist')
    id, db_passwd = row
    if bcrypt.checkpw(password.encode('utf-8'), bytes(db_passwd)) == False:
        return {"error": "Unauthorized", "detail": "Password incorrect"}, 401
    access_token = create_access_token(identity=str(id), expires_delta=timedelta(weeks=2))
    resp = make_response(jsonify(username=username))
    cookie_name = str(app.config.get('JWT_ACCESS_COOKIE_NAME', 'Authorization')) # type: ignore
    resp.set_cookie(cookie_name, access_token, httponly=True)
    return resp

@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data['username']
    password = data['password']
    if username is None or password is None:
        return bad_request('Missing Parameter `username` or `password`')
    db = g.db_conn
    cur = db.cursor()
    cur.execute("SELECT password FROM users WHERE username = %s", (username,))
    row = cur.fetchone()
    if row is not None:
        return bad_request(f'User {username} already exists')
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    cur.execute("INSERT INTO users (username, password) VALUES (%s, %s) RETURNING id", (username, hashed_password))
    user_id = cur.fetchone()[0]
    db.commit()
    cur.close()
    access_token = create_access_token(identity=str(user_id), expires_delta=timedelta(weeks=2))
    resp = make_response(jsonify({'message': 'register success', 'user_id': user_id}))
    resp.set_cookie(app.config['JWT_ACCESS_COOKIE_NAME'], access_token, httponly=True) # type: ignore
    return resp

def bad_request(detail : str):
    return {"error" : "Bad Request", "detail" : detail}, 400

@app.route('/api/posts', methods=['GET'])
def get_posts():
    num = request.args.get('num', type = int)
    if num is None:
        return bad_request("Parameter `num` must be a number")
    if num > 20 or num < 0:
        return bad_request("Parameter `num` must in range [0, 20]")
    end = request.args.get('end', type = int)
    if end is not None and end < 0:
        return bad_request("Parameter `end` must in greater than 0")
    db = g.db_conn
    cur = db.cursor()

    cur.execute(
        """
        SELECT posts.id, users.username, posts.title, posts.content
        FROM posts
        JOIN users ON posts.user_id = users.id
        WHERE posts.id <= %s
        ORDER BY posts.id DESC
        LIMIT %s
        """
        , (end, num)
    )

    res = cur.fetchall()
    cur.close()
    return jsonify(res)

@app.route('/api/post', methods=['POST'])
@jwt_required()
def post_a_post():
    data = request.get_json()
    title = data['title']
    content = data['content']
    db = g.db_conn
    cur = db.cursor()
    userId = get_jwt_identity()
    cur.execute(
        "INSERT INTO posts (user_id, title, content) VALUES (%s, %s, %s)",
        (userId, title, content)
    )
    db.commit()
    cur.close()
    return {'message' : 'success'}, 200

def get_db_conn():
    if 'db_conn' not in g:
        db_conn_str = os.environ.get('DATABASE_CONNECTION_STRING')
        g.db_conn = psycopg2.connect(db_conn_str)
    return g.db_conn

@app.before_request
def before_request():
    get_db_conn()

@app.teardown_appcontext
def close_db_conn(exception): # type: ignore
    db_conn = g.pop('db_conn', None)
    if db_conn is not None:
        db_conn.close()


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')