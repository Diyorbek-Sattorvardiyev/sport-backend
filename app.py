from flask import Flask, request, jsonify, g, send_file
from flask_cors import CORS
import sqlite3
import os
import uuid
import datetime
import jwt
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import time



app = Flask(__name__)
CORS(app)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['DATABASE'] = 'sports_school.db'

# Ensure upload directories exist
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])
    os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'news'))
    os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'sports'))
    os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'results'))
    os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'sliders'))

# Database helper functions
def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(app.config['DATABASE'])
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def init_db():
    with app.app_context():
        db = get_db()
        cursor = db.cursor()
        
        # Create Students table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            phone TEXT,
            login TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # Create Coaches table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS coaches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            birth_date TEXT,
            phone TEXT,
            sport_type_id INTEGER,
            login TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (sport_type_id) REFERENCES sport_types(id)
        )
        ''')
        
        # Create Admins table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS admins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            login TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # Create Sliders table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS sliders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            school_name TEXT NOT NULL,
            image_path TEXT,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # Create News table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS news (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content TEXT,
            date TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # Create News Images table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS news_images (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            news_id INTEGER,
            image_path TEXT,
            FOREIGN KEY (news_id) REFERENCES news(id) ON DELETE CASCADE
        )
        ''')
        
        # Create Sport Types table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS sport_types (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            image_path TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # Create Training Schedule table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS training_schedule (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            time TEXT NOT NULL,
            sport_type_id INTEGER,
            coach_id INTEGER,
            room TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (sport_type_id) REFERENCES sport_types(id),
            FOREIGN KEY (coach_id) REFERENCES coaches(id)
        )
        ''')
        
        # Create Results table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            competition_name TEXT NOT NULL,
            date TEXT,
            image_path TEXT,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # Create default admin if not exists
        cursor.execute("SELECT COUNT(*) FROM admins")
        if cursor.fetchone()[0] == 0:
            hashed_password = generate_password_hash('admin123')
            cursor.execute(
                "INSERT INTO admins (first_name, last_name, login, password) VALUES (?, ?, ?, ?)",
                ('Admin', 'User', 'admin', hashed_password)
            )
        
        db.commit()

# JWT token verification decorator
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        if 'Authorization' in request.headers:
            token = request.headers['Authorization'].split(" ")[1]
        
        if not token:
            return jsonify({'message': 'Token is missing!'}), 401
        
        try:
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
            current_user = {
                'id': data['id'],
                'role': data['role'],
                'login': data['login']
            }
        except:
            return jsonify({'message': 'Token is invalid!'}), 401
        
        return f(current_user, *args, **kwargs)
    
    return decorated

# Role-based authorization decorator
def role_required(roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(current_user, *args, **kwargs):
            if current_user['role'] not in roles:
                return jsonify({'message': 'Permission denied!'}), 403
            return f(current_user, *args, **kwargs)
        return decorated_function
    return decorator

# Routes
@app.route('/login', methods=['POST'])
def login():
    data = request.json
    login = data.get('login')
    password = data.get('password')
    
    if not login or not password:
        return jsonify({'message': 'Login and password are required!'}), 400
    
    db = get_db()
    cursor = db.cursor()
    
    # Check in admins
    cursor.execute("SELECT * FROM admins WHERE login = ?", (login,))
    user = cursor.fetchone()
    role = 'admin'
    
    if not user:
        # Check in coaches
        cursor.execute("SELECT * FROM coaches WHERE login = ?", (login,))
        user = cursor.fetchone()
        role = 'coach'
    
    if not user:
        # Check in students
        cursor.execute("SELECT * FROM students WHERE login = ?", (login,))
        user = cursor.fetchone()
        role = 'student'
    
    if not user or not check_password_hash(user['password'], password):
        return jsonify({'message': 'Invalid login or password!'}), 401
    
    token = jwt.encode({
        'id': user['id'],
        'login': user['login'],
        'role': role,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(days=7)
    }, app.config['SECRET_KEY'], algorithm="HS256")
    
    return jsonify({
        'token': token,
        'role': role,
        'id': user['id'],
        'first_name': user['first_name'],
        'last_name': user['last_name']
    })

# Helper function to save file
def save_file(file, folder):
    if not file:
        return None
    
    filename = str(uuid.uuid4()) + os.path.splitext(file.filename)[1]
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], folder, filename)
    file.save(filepath)
    return os.path.join(folder, filename)

# Admin routes for student management
@app.route('/students', methods=['GET'])
@token_required
@role_required(['admin'])
def get_students(current_user):
    db = get_db()
    cursor = db.cursor()
    
    search = request.args.get('search', '')
    if search:
        cursor.execute(
            "SELECT * FROM students WHERE first_name LIKE ? OR last_name LIKE ? OR phone LIKE ? OR login LIKE ?",
            (f'%{search}%', f'%{search}%', f'%{search}%', f'%{search}%')
        )
    else:
        cursor.execute("SELECT * FROM students")
    
    students = cursor.fetchall()
    result = []
    
    for student in students:
        result.append({
            'id': student['id'],
            'first_name': student['first_name'],
            'last_name': student['last_name'],
            'phone': student['phone'],
            'login': student['login'],
            'created_at': student['created_at']
        })
    
    return jsonify(result)

@app.route('/students', methods=['POST'])
@token_required
@role_required(['admin'])
def add_student(current_user):
    data = request.json
    
    if not data.get('first_name') or not data.get('last_name') or not data.get('login') or not data.get('password'):
        return jsonify({'message': 'Required fields are missing!'}), 400
    
    db = get_db()
    cursor = db.cursor()
    
    try:
        hashed_password = generate_password_hash(data['password'])
        cursor.execute(
            "INSERT INTO students (first_name, last_name, phone, login, password) VALUES (?, ?, ?, ?, ?)",
            (data['first_name'], data['last_name'], data.get('phone', ''), data['login'], hashed_password)
        )
        db.commit()
        
        return jsonify({'message': 'Student added successfully!', 'id': cursor.lastrowid})
    except sqlite3.IntegrityError:
        return jsonify({'message': 'Login already exists!'}), 409
    except Exception as e:
        return jsonify({'message': str(e)}), 500

@app.route('/students/<int:student_id>', methods=['PUT'])
@token_required
@role_required(['admin'])
def update_student(current_user, student_id):
    data = request.json
    
    if not data:
        return jsonify({'message': 'No data provided!'}), 400
    
    db = get_db()
    cursor = db.cursor()
    
    try:
        update_fields = []
        params = []
        
        if 'first_name' in data:
            update_fields.append("first_name = ?")
            params.append(data['first_name'])
        
        if 'last_name' in data:
            update_fields.append("last_name = ?")
            params.append(data['last_name'])
        
        if 'phone' in data:
            update_fields.append("phone = ?")
            params.append(data['phone'])
        
        if 'login' in data:
            update_fields.append("login = ?")
            params.append(data['login'])
        
        if 'password' in data:
            update_fields.append("password = ?")
            params.append(generate_password_hash(data['password']))
        
        if not update_fields:
            return jsonify({'message': 'No valid fields to update!'}), 400
        
        params.append(student_id)
        cursor.execute(
            f"UPDATE students SET {', '.join(update_fields)} WHERE id = ?", 
            params
        )
        db.commit()
        
        if cursor.rowcount == 0:
            return jsonify({'message': 'Student not found!'}), 404
        
        return jsonify({'message': 'Student updated successfully!'})
    except sqlite3.IntegrityError:
        return jsonify({'message': 'Login already exists!'}), 409
    except Exception as e:
        return jsonify({'message': str(e)}), 500

@app.route('/students/<int:student_id>', methods=['DELETE'])
@token_required
@role_required(['admin'])
def delete_student(current_user, student_id):
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute("DELETE FROM students WHERE id = ?", (student_id,))
    db.commit()
    
    if cursor.rowcount == 0:
        return jsonify({'message': 'Student not found!'}), 404
    
    return jsonify({'message': 'Student deleted successfully!'})

# Admin & Coach routes for student viewing
@app.route('/students/view', methods=['GET'])
@token_required
@role_required(['admin', 'coach'])
def view_students(current_user):
    db = get_db()
    cursor = db.cursor()
    
    search = request.args.get('search', '')
    if search:
        cursor.execute(
            "SELECT id, first_name, last_name, phone FROM students WHERE first_name LIKE ? OR last_name LIKE ? OR phone LIKE ?",
            (f'%{search}%', f'%{search}%', f'%{search}%')
        )
    else:
        cursor.execute("SELECT id, first_name, last_name, phone FROM students")
    
    students = cursor.fetchall()
    result = []
    
    for student in students:
        result.append({
            'id': student['id'],
            'first_name': student['first_name'],
            'last_name': student['last_name'],
            'phone': student['phone']
        })
    
    return jsonify(result)

# Admin routes for coach management
@app.route('/coaches', methods=['GET'])
@token_required
@role_required(['admin'])
def get_coaches(current_user):
    db = get_db()
    cursor = db.cursor()
    
    search = request.args.get('search', '')
    if search:
        cursor.execute("""
            SELECT c.*, s.name as sport_name FROM coaches c
            LEFT JOIN sport_types s ON c.sport_type_id = s.id
            WHERE c.first_name LIKE ? OR c.last_name LIKE ? OR c.phone LIKE ? OR c.login LIKE ? OR s.name LIKE ?
        """, (f'%{search}%', f'%{search}%', f'%{search}%', f'%{search}%', f'%{search}%'))
    else:
        cursor.execute("""
            SELECT c.*, s.name as sport_name FROM coaches c
            LEFT JOIN sport_types s ON c.sport_type_id = s.id
        """)
    
    coaches = cursor.fetchall()
    result = []
    
    for coach in coaches:
        result.append({
            'id': coach['id'],
            'first_name': coach['first_name'],
            'last_name': coach['last_name'],
            'birth_date': coach['birth_date'],
            'phone': coach['phone'],
            'sport_type_id': coach['sport_type_id'],
            'sport_name': coach['sport_name'],
            'login': coach['login'],
            'created_at': coach['created_at']
        })
    
    return jsonify(result)

@app.route('/coaches', methods=['POST'])
@token_required
@role_required(['admin'])
def add_coach(current_user):
    data = request.json
    
    # Ma'lumotlarni tekshirish
    if 'full_name' in data:
        # Agar full_name kelsa, uni first_name va last_name ga ajratamiz
        full_name = data['full_name'].split()
        if len(full_name) >= 2:
            first_name = full_name[0]
            last_name = ' '.join(full_name[1:])
        else:
            first_name = data['full_name']
            last_name = ""
    else:
        first_name = data.get('first_name', '')
        last_name = data.get('last_name', '')
    
    if not first_name:
        return jsonify({'message': 'Name is required!'}), 400
    
    login = data.get('login', first_name.lower() + last_name.lower())
    password = data.get('password', 'default123')
    
    db = get_db()
    cursor = db.cursor()
    
    try:
        hashed_password = generate_password_hash(password)
        cursor.execute(
            """INSERT INTO coaches (first_name, last_name, birth_date, phone, sport_type_id, login, password) 
            VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                first_name, 
                last_name, 
                data.get('birth_date', ''), 
                data.get('phone', ''), 
                data.get('sport_type_id'), 
                login, 
                hashed_password
            )
        )
        db.commit()
        
        return jsonify({'message': 'Coach added successfully!', 'id': cursor.lastrowid})
    except sqlite3.IntegrityError:
        return jsonify({'message': 'Login already exists!'}), 409
    except Exception as e:
        return jsonify({'message': str(e)}), 500

@app.route('/coaches/<int:coach_id>', methods=['PUT'])
@token_required
@role_required(['admin'])
def update_coach(current_user, coach_id):
    data = request.json
    
    if not data:
        return jsonify({'message': 'No data provided!'}), 400
    
    db = get_db()
    cursor = db.cursor()
    
    try:
        update_fields = []
        params = []
        
        if 'first_name' in data:
            update_fields.append("first_name = ?")
            params.append(data['first_name'])
        
        if 'last_name' in data:
            update_fields.append("last_name = ?")
            params.append(data['last_name'])
        
        if 'birth_date' in data:
            update_fields.append("birth_date = ?")
            params.append(data['birth_date'])
        
        if 'phone' in data:
            update_fields.append("phone = ?")
            params.append(data['phone'])
        
        if 'sport_type_id' in data:
            update_fields.append("sport_type_id = ?")
            params.append(data['sport_type_id'])
        
        if 'login' in data:
            update_fields.append("login = ?")
            params.append(data['login'])
        
        if 'password' in data:
            update_fields.append("password = ?")
            params.append(generate_password_hash(data['password']))
        
        if not update_fields:
            return jsonify({'message': 'No valid fields to update!'}), 400
        
        params.append(coach_id)
        cursor.execute(
            f"UPDATE coaches SET {', '.join(update_fields)} WHERE id = ?", 
            params
        )
        db.commit()
        
        if cursor.rowcount == 0:
            return jsonify({'message': 'Coach not found!'}), 404
        
        return jsonify({'message': 'Coach updated successfully!'})
    except sqlite3.IntegrityError:
        return jsonify({'message': 'Login already exists!'}), 409
    except Exception as e:
        return jsonify({'message': str(e)}), 500

@app.route('/coaches/<int:coach_id>', methods=['DELETE'])
@token_required
@role_required(['admin'])
def delete_coach(current_user, coach_id):
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute("DELETE FROM coaches WHERE id = ?", (coach_id,))
    db.commit()
    
    if cursor.rowcount == 0:
        return jsonify({'message': 'Coach not found!'}), 404
    
    return jsonify({'message': 'Coach deleted successfully!'})

# Coach viewing route for students
@app.route('/coaches/view', methods=['GET'])
@token_required
def view_coaches(current_user):
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute("""
        SELECT c.id, c.first_name, c.last_name, c.birth_date, c.phone, s.name as sport_name 
        FROM coaches c
        LEFT JOIN sport_types s ON c.sport_type_id = s.id
    """)
    
    coaches = cursor.fetchall()
    result = []
    
    for coach in coaches:
        result.append({
            'id': coach['id'],
            'first_name': coach['first_name'],
            'last_name': coach['last_name'],
            'birth_date': coach['birth_date'],
            'phone': coach['phone'],
            'sport_name': coach['sport_name']
        })
    
    return jsonify(result)

# Admin routes for slider management
@app.route('/sliders', methods=['GET'])
@token_required
def get_sliders(current_user):
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute("SELECT * FROM sliders")
    
    sliders = cursor.fetchall()
    result = []
    
    for slider in sliders:
        result.append({
            'id': slider['id'],
            'school_name': slider['school_name'],
            'image_path': slider['image_path'],
            'description': slider['description'],
            'created_at': slider['created_at']
        })
    
    return jsonify(result)

@app.route('/sliders', methods=['POST'])
@token_required
@role_required(['admin'])
def add_slider(current_user):
    if 'image' not in request.files:
        return jsonify({'message': 'No image provided!'}), 400
    
    image = request.files['image']
    school_name = request.form.get('school_name')
    description = request.form.get('description')
    
    if not school_name:
        return jsonify({'message': 'School name is required!'}), 400
    
    image_path = save_file(image, 'sliders')
    
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute(
        "INSERT INTO sliders (school_name, image_path, description) VALUES (?, ?, ?)",
        (school_name, image_path, description)
    )
    db.commit()
    
    return jsonify({'message': 'Slider added successfully!', 'id': cursor.lastrowid})

@app.route('/sliders/<int:slider_id>', methods=['PUT'])
@token_required
@role_required(['admin'])
def update_slider(current_user, slider_id):
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute("SELECT * FROM sliders WHERE id = ?", (slider_id,))
    slider = cursor.fetchone()
    
    if not slider:
        return jsonify({'message': 'Slider not found!'}), 404
    
    school_name = request.form.get('school_name', slider['school_name'])
    description = request.form.get('description', slider['description'])
    image_path = slider['image_path']
    
    if 'image' in request.files and request.files['image'].filename:
        # Delete old image if exists
        if image_path and os.path.exists(os.path.join(app.config['UPLOAD_FOLDER'], image_path)):
            os.remove(os.path.join(app.config['UPLOAD_FOLDER'], image_path))
        
        # Save new image
        image_path = save_file(request.files['image'], 'sliders')
    
    cursor.execute(
        "UPDATE sliders SET school_name = ?, image_path = ?, description = ? WHERE id = ?",
        (school_name, image_path, description, slider_id)
    )
    db.commit()
    
    return jsonify({'message': 'Slider updated successfully!'})

@app.route('/sliders/<int:slider_id>', methods=['DELETE'])
@token_required
@role_required(['admin'])
def delete_slider(current_user, slider_id):
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute("SELECT image_path FROM sliders WHERE id = ?", (slider_id,))
    slider = cursor.fetchone()
    
    if not slider:
        return jsonify({'message': 'Slider not found!'}), 404
    
    # Delete image file if exists
    if slider['image_path'] and os.path.exists(os.path.join(app.config['UPLOAD_FOLDER'], slider['image_path'])):
        os.remove(os.path.join(app.config['UPLOAD_FOLDER'], slider['image_path']))
    
    cursor.execute("DELETE FROM sliders WHERE id = ?", (slider_id,))
    db.commit()
    
    return jsonify({'message': 'Slider deleted successfully!'})

# Admin routes for news management
@app.route('/news', methods=['GET'])
@token_required
def get_news(current_user):
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute("SELECT * FROM news ORDER BY date DESC")
    news_items = cursor.fetchall()
    result = []
    
    for news in news_items:
        cursor.execute("SELECT image_path FROM news_images WHERE news_id = ?", (news['id'],))
        images = cursor.fetchall()
        image_paths = [img['image_path'] for img in images]
        
        result.append({
            'id': news['id'],
            'title': news['title'],
            'content': news['content'],
            'date': news['date'],
            'created_at': news['created_at'],
            'images': image_paths
        })
    
    return jsonify(result)

@app.route('/news', methods=['POST'])
@token_required
@role_required(['admin'])
def add_news(current_user):
    title = request.form.get('title')
    content = request.form.get('content')
    date = request.form.get('date', datetime.datetime.now().strftime('%Y-%m-%d'))
    
    if not title:
        return jsonify({'message': 'Title is required!'}), 400
    
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute(
        "INSERT INTO news (title, content, date) VALUES (?, ?, ?)",
        (title, content, date)
    )
    news_id = cursor.lastrowid
    
    # Handle multiple images
    if 'images' in request.files:
        images = request.files.getlist('images')
        for image in images:
            if image and image.filename:
                image_path = save_file(image, 'news')
                cursor.execute(
                    "INSERT INTO news_images (news_id, image_path) VALUES (?, ?)",
                    (news_id, image_path)
                )
    
    db.commit()
    
    return jsonify({'message': 'News added successfully!', 'id': news_id})

@app.route('/news/<int:news_id>', methods=['PUT'])
@token_required
@role_required(['admin'])
def update_news(current_user, news_id):
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute("SELECT * FROM news WHERE id = ?", (news_id,))
    news = cursor.fetchone()
    
    if not news:
        return jsonify({'message': 'News not found!'}), 404
    
    title = request.form.get('title', news['title'])
    content = request.form.get('content', news['content'])
    date = request.form.get('date', news['date'])
    
    cursor.execute(
        "UPDATE news SET title = ?, content = ?, date = ? WHERE id = ?",
        (title, content, date, news_id)
    )
    
    # Handle replacing images if requested
    if request.form.get('replace_images') == 'true' and 'images' in request.files:
        # Delete old images
        cursor.execute("SELECT image_path FROM news_images WHERE news_id = ?", (news_id,))
        old_images = cursor.fetchall()
        
        for img in old_images:
            if img['image_path'] and os.path.exists(os.path.join(app.config['UPLOAD_FOLDER'], img['image_path'])):
                os.remove(os.path.join(app.config['UPLOAD_FOLDER'], img['image_path']))
        
        cursor.execute("DELETE FROM news_images WHERE news_id = ?", (news_id,))
        
        # Add new images
        images = request.files.getlist('images')
        for image in images:
            if image and image.filename:
                image_path = save_file(image, 'news')
                cursor.execute(
                    "INSERT INTO news_images (news_id, image_path) VALUES (?, ?)",
                    (news_id, image_path)
                )
    # Add additional images
    elif 'images' in request.files:
        images = request.files.getlist('images')
        for image in images:
            if image and image.filename:
                image_path = save_file(image, 'news')
                cursor.execute(
                    "INSERT INTO news_images (news_id, image_path) VALUES (?, ?)",
                    (news_id, image_path)
                )
    
    db.commit()
    
    return jsonify({'message': 'News updated successfully!'})

@app.route('/news/<int:news_id>', methods=['DELETE'])
@token_required
@role_required(['admin'])
def delete_news(current_user, news_id):
    db = get_db()
    cursor = db.cursor()
    
    # Delete associated images first
    cursor.execute("SELECT image_path FROM news_images WHERE news_id = ?", (news_id,))
    images = cursor.fetchall()
    
    for img in images:
        if img['image_path'] and os.path.exists(os.path.join(app.config['UPLOAD_FOLDER'], img['image_path'])):
            os.remove(os.path.join(app.config['UPLOAD_FOLDER'], img['image_path']))
    
    cursor.execute("DELETE FROM news_images WHERE news_id = ?", (news_id,))
    cursor.execute("DELETE FROM news WHERE id = ?", (news_id,))
    db.commit()
    
    if cursor.rowcount == 0:
        return jsonify({'message': 'News not found!'}), 404
    
    return jsonify({'message': 'News deleted successfully!'})

# Admin routes for sport types management
@app.route('/sport-types', methods=['GET'])
@token_required
def get_sport_types(current_user):
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute("SELECT * FROM sport_types")
    
    sports = cursor.fetchall()
    result = []
    
    for sport in sports:
        result.append({
            'id': sport['id'],
            'name': sport['name'],
            'description': sport['description'],
            'image_path': sport['image_path'],
            'created_at': sport['created_at']
        })
    
    return jsonify(result)

@app.route('/sport-types', methods=['POST'])
@token_required
@role_required(['admin'])
def add_sport_type(current_user):
    name = request.form.get('name')
    description = request.form.get('description')
    
    if not name:
        return jsonify({'message': 'Sport name is required!'}), 400
    
    image_path = None
    if 'image' in request.files and request.files['image'].filename:
        image_path = save_file(request.files['image'], 'sports')
    
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute(
        "INSERT INTO sport_types (name, description, image_path) VALUES (?, ?, ?)",
        (name, description, image_path)
    )
    db.commit()
    
    return jsonify({'message': 'Sport type added successfully!', 'id': cursor.lastrowid})

@app.route('/sport-types/<int:sport_id>', methods=['PUT'])
@token_required
@role_required(['admin'])
def update_sport_type(current_user, sport_id):
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute("SELECT * FROM sport_types WHERE id = ?", (sport_id,))
    sport = cursor.fetchone()
    
    if not sport:
        return jsonify({'message': 'Sport type not found!'}), 404
    
    name = request.form.get('name', sport['name'])
    description = request.form.get('description', sport['description'])
    image_path = sport['image_path']
    
    if 'image' in request.files and request.files['image'].filename:
        # Delete old image if exists
        if image_path and os.path.exists(os.path.join(app.config['UPLOAD_FOLDER'], image_path)):
            os.remove(os.path.join(app.config['UPLOAD_FOLDER'], image_path))
        
        # Save new image
        image_path = save_file(request.files['image'], 'sports')
    
    cursor.execute(
        "UPDATE sport_types SET name = ?, description = ?, image_path = ? WHERE id = ?",
        (name, description, image_path, sport_id)
    )
    db.commit()
    
    return jsonify({'message': 'Sport type updated successfully!'})

@app.route('/sport-types/<int:sport_id>', methods=['DELETE'])
@token_required
@role_required(['admin'])
def delete_sport_type(current_user, sport_id):
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute("SELECT image_path FROM sport_types WHERE id = ?", (sport_id,))
    sport = cursor.fetchone()
    
    if not sport:
        return jsonify({'message': 'Sport type not found!'}), 404
    
    # Delete image file if exists
    if sport['image_path'] and os.path.exists(os.path.join(app.config['UPLOAD_FOLDER'], sport['image_path'])):
        os.remove(os.path.join(app.config['UPLOAD_FOLDER'], sport['image_path']))
    
    cursor.execute("DELETE FROM sport_types WHERE id = ?", (sport_id,))
    db.commit()
    
    return jsonify({'message': 'Sport type deleted successfully!'})

# Admin routes for training schedule management
@app.route('/training-schedule', methods=['GET'])
@token_required
def get_training_schedule(current_user):
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute("""
        SELECT ts.*, c.first_name as coach_first_name, c.last_name as coach_last_name, st.name as sport_name
        FROM training_schedule ts
        LEFT JOIN coaches c ON ts.coach_id = c.id
        LEFT JOIN sport_types st ON ts.sport_type_id = st.id
        ORDER BY ts.date, ts.time
    """)
    
    schedules = cursor.fetchall()
    result = []
    
    for schedule in schedules:
        result.append({
            'id': schedule['id'],
            'date': schedule['date'],
            'time': schedule['time'],
            'sport_type_id': schedule['sport_type_id'],
            'sport_name': schedule['sport_name'],
            'coach_id': schedule['coach_id'],
            'coach_name': f"{schedule['coach_first_name']} {schedule['coach_last_name']}",
            'room': schedule['room'],
            'created_at': schedule['created_at']
        })
    
    return jsonify(result)

@app.route('/training-schedule', methods=['POST'])
@token_required
@role_required(['admin'])
def add_training_schedule(current_user):
    data = request.json
    
    if not data.get('date') or not data.get('time'):
        return jsonify({'message': 'Date and time are required!'}), 400
    
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute(
        """INSERT INTO training_schedule (date, time, sport_type_id, coach_id, room) 
        VALUES (?, ?, ?, ?, ?)""",
        (
            data['date'], 
            data['time'], 
            data.get('sport_type_id'), 
            data.get('coach_id'), 
            data.get('room', '')
        )
    )
    db.commit()
    
    return jsonify({'message': 'Training schedule added successfully!', 'id': cursor.lastrowid})

@app.route('/training-schedule/<int:schedule_id>', methods=['PUT'])
@token_required
@role_required(['admin'])
def update_training_schedule(current_user, schedule_id):
    data = request.json
    
    if not data:
        return jsonify({'message': 'No data provided!'}), 400
    
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute("SELECT * FROM training_schedule WHERE id = ?", (schedule_id,))
    schedule = cursor.fetchone()
    
    if not schedule:
        return jsonify({'message': 'Training schedule not found!'}), 404
    
    date = data.get('date', schedule['date'])
    time = data.get('time', schedule['time'])
    sport_type_id = data.get('sport_type_id', schedule['sport_type_id'])
    coach_id = data.get('coach_id', schedule['coach_id'])
    room = data.get('room', schedule['room'])
    
    cursor.execute(
        """UPDATE training_schedule 
        SET date = ?, time = ?, sport_type_id = ?, coach_id = ?, room = ? 
        WHERE id = ?""",
        (date, time, sport_type_id, coach_id, room, schedule_id)
    )
    db.commit()
    
    return jsonify({'message': 'Training schedule updated successfully!'})

@app.route('/training-schedule/<int:schedule_id>', methods=['DELETE'])
@token_required
@role_required(['admin'])
def delete_training_schedule(current_user, schedule_id):
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute("DELETE FROM training_schedule WHERE id = ?", (schedule_id,))
    db.commit()
    
    if cursor.rowcount == 0:
        return jsonify({'message': 'Training schedule not found!'}), 404
    
    return jsonify({'message': 'Training schedule deleted successfully!'})

# Admin routes for results management
@app.route('/results', methods=['GET'])
@token_required
def get_results(current_user):
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute("SELECT * FROM results ORDER BY date DESC")
    
    results = cursor.fetchall()
    result_list = []
    
    for res in results:
        result_list.append({
            'id': res['id'],
            'competition_name': res['competition_name'],
            'date': res['date'],
            'image_path': res['image_path'],
            'description': res['description'],
            'created_at': res['created_at']
        })
    
    return jsonify(result_list)

@app.route('/results', methods=['POST'])
@token_required
@role_required(['admin'])
def add_result(current_user):
    competition_name = request.form.get('competition_name')
    date = request.form.get('date')
    description = request.form.get('description')
    
    if not competition_name:
        return jsonify({'message': 'Competition name is required!'}), 400
    
    image_path = None
    if 'image' in request.files and request.files['image'].filename:
        image_path = save_file(request.files['image'], 'results')
    
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute(
        "INSERT INTO results (competition_name, date, image_path, description) VALUES (?, ?, ?, ?)",
        (competition_name, date, image_path, description)
    )
    db.commit()
    
    return jsonify({'message': 'Result added successfully!', 'id': cursor.lastrowid})

@app.route('/results/<int:result_id>', methods=['PUT'])
@token_required
@role_required(['admin'])
def update_result(current_user, result_id):
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute("SELECT * FROM results WHERE id = ?", (result_id,))
    result = cursor.fetchone()
    
    if not result:
        return jsonify({'message': 'Result not found!'}), 404
    
    competition_name = request.form.get('competition_name', result['competition_name'])
    date = request.form.get('date', result['date'])
    description = request.form.get('description', result['description'])
    image_path = result['image_path']
    
    if 'image' in request.files and request.files['image'].filename:
        # Delete old image if exists
        if image_path and os.path.exists(os.path.join(app.config['UPLOAD_FOLDER'], image_path)):
            os.remove(os.path.join(app.config['UPLOAD_FOLDER'], image_path))
        
        # Save new image
        image_path = save_file(request.files['image'], 'results')
    
    cursor.execute(
        "UPDATE results SET competition_name = ?, date = ?, image_path = ?, description = ? WHERE id = ?",
        (competition_name, date, image_path, description, result_id)
    )
    db.commit()
    
    return jsonify({'message': 'Result updated successfully!'})

@app.route('/results/<int:result_id>', methods=['DELETE'])
@token_required
@role_required(['admin'])
def delete_result(current_user, result_id):
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute("SELECT image_path FROM results WHERE id = ?", (result_id,))
    result = cursor.fetchone()
    
    if not result:
        return jsonify({'message': 'Result not found!'}), 404
    
    # Delete image file if exists
    if result['image_path'] and os.path.exists(os.path.join(app.config['UPLOAD_FOLDER'], result['image_path'])):
        os.remove(os.path.join(app.config['UPLOAD_FOLDER'], result['image_path']))
    
    cursor.execute("DELETE FROM results WHERE id = ?", (result_id,))
    db.commit()
    
    return jsonify({'message': 'Result deleted successfully!'})

# User profile routes
@app.route('/profile', methods=['GET'])
@token_required
def get_profile(current_user):
    db = get_db()
    cursor = db.cursor()
    
    role = current_user['role']
    user_id = current_user['id']
    
    if role == 'admin':
        cursor.execute("SELECT id, first_name, last_name, login FROM admins WHERE id = ?", (user_id,))
    elif role == 'coach':
        cursor.execute("""
            SELECT c.id, c.first_name, c.last_name, c.birth_date, c.phone, c.login, s.name as sport_name 
            FROM coaches c
            LEFT JOIN sport_types s ON c.sport_type_id = s.id
            WHERE c.id = ?
        """, (user_id,))
    elif role == 'student':
        cursor.execute("SELECT id, first_name, last_name, phone, login FROM students WHERE id = ?", (user_id,))
    
    user = cursor.fetchone()
    
    if not user:
        return jsonify({'message': 'User not found!'}), 404
    
    # Convert SQLite Row to dict
    user_dict = dict(user)
    user_dict['role'] = role
    
    return jsonify(user_dict)

@app.route('/profile/update-password', methods=['PUT'])
@token_required
def update_password(current_user):
    data = request.json
    
    if not data.get('current_password') or not data.get('new_password'):
        return jsonify({'message': 'Current and new passwords are required!'}), 400
    
    db = get_db()
    cursor = db.cursor()
    
    role = current_user['role']
    user_id = current_user['id']
    
    if role == 'admin':
        cursor.execute("SELECT password FROM admins WHERE id = ?", (user_id,))
    elif role == 'coach':
        cursor.execute("SELECT password FROM coaches WHERE id = ?", (user_id,))
    elif role == 'student':
        cursor.execute("SELECT password FROM students WHERE id = ?", (user_id,))
    
    user = cursor.fetchone()
    
    if not user or not check_password_hash(user['password'], data['current_password']):
        return jsonify({'message': 'Current password is incorrect!'}), 401
    
    hashed_password = generate_password_hash(data['new_password'])
    
    if role == 'admin':
        cursor.execute("UPDATE admins SET password = ? WHERE id = ?", (hashed_password, user_id))
    elif role == 'coach':
        cursor.execute("UPDATE coaches SET password = ? WHERE id = ?", (hashed_password, user_id))
    elif role == 'student':
        cursor.execute("UPDATE students SET password = ? WHERE id = ?", (hashed_password, user_id))
    
    db.commit()
    
    return jsonify({'message': 'Password updated successfully!'})

# Serve uploaded files
@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    return send_file(os.path.join(app.config['UPLOAD_FOLDER'], filename))

# Initialize database on startup
@app.before_request
def before_request():
    if not hasattr(app, 'first_request'):
        init_db()
        app.first_request = False  # `app` obyektida saqlaymiz


if __name__ == '__main__':
    # Make app available on local network
    app.run(host='0.0.0.0', port=5000, debug=True)