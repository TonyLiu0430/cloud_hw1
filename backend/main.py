from flask import Flask, request, jsonify, make_response, g, send_file
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from dotenv import load_dotenv
import os
import psycopg2
import bcrypt
from datetime import datetime, timedelta
from werkzeug.datastructures import FileStorage
import uuid


load_dotenv()

app = Flask(__name__)
app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY')
app.config['JWT_TOKEN_LOCATION'] = ['cookies']
app.config['JWT_ACCESS_COOKIE_NAME'] = 'Authorization'
app.config['JWT_COOKIE_CSRF_PROTECT'] = False
app.config['UPLOAD_FOLDER'] = 'uploads'
jwt = JWTManager(app)

@app.route('/')
def test_vue():
    return 'You are in the backend index page, Go back'

@app.route('/api/login/check', methods=['POST'])
@jwt_required()
def check_login():
    return {'message': 'logged in'}, 200

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
    return {"error" : "Bad Request", "message" : detail}, 400

@app.route('/api/sale_item', methods=['POST'])
@jwt_required()
def sale_a_item():
    data = request.get_json()
    title = data['title']
    description = data['description']
    starting_price = data['starting_price']
    end_date_str = data['end_date']
    end_date = datetime.fromisoformat(end_date_str)
    if title is None or description is None or starting_price is None:
        return bad_request("Parameter `title` and `description` and `starting_price` must be not empty")
    db = g.db_conn
    cur = db.cursor()
    seller_id = str(get_jwt_identity())
    cur.execute(
        "INSERT INTO sale_items (title, description, starting_price, end_date, seller_id) VALUES (%s, %s, %s, %s, %s) RETURNING id",
        (title, description, starting_price, end_date, seller_id)
    )
    db.commit()
    item_uuid = cur.fetchone()[0]
    cur.close()
    return {'message' : 'success', 'item_uuid' : str(item_uuid)}

@app.route('/api/sale_item/<item_uuid>/bid', methods=['POST'])
@jwt_required()
def place_bid(item_uuid: str): # type: ignore
    data = request.get_json()
    price = data['price']
    if price is None:
        return bad_request("Parameter `price` cannot be empty")
    userId = str(get_jwt_identity())
    db = g.db_conn
    cur = db.cursor()
    cur.execute(
        "SELECT end_date FROM sale_items WHERE id = %s",
        (item_uuid,)
    )
    row = cur.fetchone()
    if row is None:
        return bad_request("Item not found")
    end_date = row[0]
    if end_date < datetime.now():
        return bad_request("Cannot place bid after auction end date")
    
    cur.execute("SELECT starting_price FROM sale_items WHERE id = %s FOR UPDATE", (item_uuid,))
    starting_price_row = cur.fetchone()
    if starting_price_row is None:
        return bad_request("Item not found")
    starting_price = int(starting_price_row[0])
    
    cur.execute("SELECT MAX(price) FROM bids WHERE sale_item_id = %s", (item_uuid,))
    max_price_row = cur.fetchone()
    max_price = max_price_row[0]

    current_price = int(max_price) if max_price is not None else starting_price

    if price <= current_price:
        return {"error": "Bid too low", "detail": "price less than current price"}, 409
    
    cur.execute(
        "INSERT INTO bids (sale_item_id, user_id, price) VALUES (%s, %s, %s) RETURNING id",
        (item_uuid, userId, price)
    )
    bids_id = cur.fetchone()[0]
    db.commit()
    return {"message" : "success", "bid_id": bids_id}, 201 # type: ignore

@app.route('/api/sale_item/<item_uuid>', methods=['GET'])
def get_item(item_uuid: str):
    db = get_db_conn()
    cur = db.cursor()
    cur.execute(
        """
        SELECT id, title, description, starting_price, end_date, seller_id
        FROM sale_items
        WHERE id = %s
        """,
        (item_uuid,)
    )
    item = cur.fetchone()
    if item is None:
        cur.close()
        return bad_request("Item not found")

    cur.execute(
        """
        SELECT b.id, b.user_id, b.price, b.created_at
        FROM bids b
        WHERE b.sale_item_id = %s
        ORDER BY b.price DESC
        LIMIT 10
        """,
        (item_uuid,)
    )
    bids = cur.fetchall()
    cur.close()
    return jsonify({
        "item": {
            "id": item[0],
            "title": item[1],
            "description": item[2],
            "starting_price": int(item[3]),
            "end_date": item[4].isoformat(),
            "seller_id": item[5]
        },
        "bids": [
            {
                "id": bid[0],
                "user_id": bid[1],
                "price": int(bid[2]),
                "created_at": bid[3].isoformat() if bid[3] else None
            }
            for bid in bids
        ]
    })


@app.route('/api/sale_items', methods=['GET'])
def get_sale_items():
    db = get_db_conn()
    cur = db.cursor()
    cur.execute(
        """
        SELECT s.id, s.title, s.description, s.starting_price, s.end_date, s.seller_id,
               COALESCE(MAX(b.price), s.starting_price) AS current_price,
               (
                   SELECT image_url
                   FROM sale_item_images img
                   WHERE img.sale_item_id = s.id
                   ORDER BY img.id ASC
                   LIMIT 1
               ) AS first_image_url
        FROM sale_items s
        LEFT JOIN bids b ON s.id = b.sale_item_id
        GROUP BY s.id
        ORDER BY s.end_date ASC
        """
    )
    items = cur.fetchall()
    cur.close()
    result = [ # type: ignore
        {
            "id": item[0],
            "title": item[1],
            "description": item[2],
            "starting_price": item[3],
            "end_date": item[4].isoformat(),
            "seller_id": item[5],
            "current_price": item[6],
            "img_url": item[7]
        }
        for item in items
    ]
    return jsonify(result)


def save_file(file: FileStorage) -> str:
    if file.filename is None or file.filename == '':
        raise ValueError("No selected file")
    ext = os.path.splitext(file.filename)[1]
    if ext not in ['.jpeg', '.jpg', '.png']:
        raise ValueError("Not support file")
    file_uuid = f"{uuid.uuid4().hex}{ext}"
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], file_uuid) # type: ignore
    file.save(filepath)
    return file_uuid

@app.route('/api/img/upload/<sale_item_uuid>', methods=['POST'])
@jwt_required()
def upload_image(sale_item_uuid: str):
    if 'image' not in request.files:
        return jsonify({'error': 'No image uploaded'}), 400
    userId = str(get_jwt_identity())
    db = get_db_conn()
    cur = db.cursor()
    cur.execute("SELECT seller_id FROM sale_items WHERE id = %s", (sale_item_uuid,))
    row = cur.fetchone()
    if row is None:
        cur.close()
        return bad_request("Sale item not found")
    seller_id = row[0]
    if seller_id != userId:
        cur.close()
        return jsonify({'error': 'Unauthorized'}), 403
    image_file = request.files['image']
    try:
        file_uuid = save_file(image_file)
    except Exception as e:
        cur.close()
        return jsonify({'error': str(e)}), 400
    file_url = f"/api/img/{file_uuid}"
    cur.execute(
        "INSERT INTO sale_item_images (sale_item_id, image_url) VALUES (%s, %s)",
        (sale_item_uuid, file_url)
    )
    db.commit()
    cur.close()
    return jsonify({'message': 'Image uploaded'}), 200

# 機制可能有問題 順序可能會錯 但是先不管
@app.route('/api/sale_item/images/<sale_item_uuid>', methods=['GET'])
def get_item_images(sale_item_uuid: str):
    db = get_db_conn()
    cur = db.cursor()
    cur.execute(
        "SELECT image_url FROM sale_item_images WHERE sale_item_id = %s ORDER BY id ASC",
        (sale_item_uuid,)
    )
    images = [row[0] for row in cur.fetchall()]
    cur.close()
    return jsonify({'images': images})

@app.route('/api/img/<file_uuid>', methods=['GET'])
def get_image(file_uuid: str):
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], file_uuid) # type: ignore
    if not os.path.exists(filepath):
        return jsonify({'error': 'File not found'}), 404
    return send_file(filepath)

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