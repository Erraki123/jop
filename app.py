from flask import Flask, render_template, request, redirect, url_for, flash, session
import mysql.connector
from mysql.connector import Error
from werkzeug.security import generate_password_hash, check_password_hash
import os
from werkzeug.utils import secure_filename


from flask_mail import Mail, Message


app = Flask(__name__)

# إعدادات البريد الإلكتروني
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = 'raki39174@gmail.com'  # أدخل بريدك الإلكتروني هنا
app.config['MAIL_PASSWORD'] = 'ajoa wryp boxv rxvc'  # أدخل كلمة مرور البريد الإلكتروني
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
app.config['MAIL_DEFAULT_SENDER'] = 'raki39174@gmail.com'  # تحديد المرسل الافتراضي

mail = Mail(app)


# Secret key for session management
app.secret_key = os.urandom(24)

app.config['IMAGE_UPLOAD_FOLDER'] = 'static/uploads'  # Dossier pour les images
app.config['CV_UPLOAD_FOLDER'] = 'uploads'  # Dossier pour les CVs (PDF)
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf'}


# Check if a file has an allowed extension
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Database connection
def get_db_connection():
    try:
        return mysql.connector.connect(
            host='localhost',
            user='root',
            password='',
            database='job_portal'
        )
    except Error as e:
        print(f"Database connection error: {e}")
        return None

# Routes

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/job-seeker.html', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        if not email or not password:
            flash('يرجى إدخال البريد الإلكتروني وكلمة المرور.', 'warning')
            return render_template('login.html')

        conn = get_db_connection()
        if conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute('SELECT * FROM users WHERE email = %s', (email,))
            user = cursor.fetchone()
            conn.close()

            if user and check_password_hash(user['password'], password):
                # تحديث الجلسة بمعلومات المستخدم الجديد
                session['user_id'] = user['id']
                session['email'] = user['email']
                session['first_name'] = user['first_name']
                session['last_name'] = user['last_name']
                session['photo'] = user['photo']
                session['description'] = user.get('description', '')
                session['phone'] = user.get('phone', '')  # إضافة رقم الهاتف للجلسة
                flash('تم تسجيل الدخول بنجاح!', 'success')
                return redirect(url_for('portfolio'))
            else:
                flash('بيانات تسجيل الدخول غير صحيحة.', 'danger')
        else:
            flash('خطأ في الاتصال بقاعدة البيانات.', 'danger')

    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        email = request.form.get('email')
        password = request.form.get('password')
        phone = request.form.get('phone')  # Récupérer le téléphone

        if not (first_name and last_name and email and password and phone):
            flash('يرجى ملء جميع الحقول.', 'warning')
            return render_template('register.html')

        hashed_password = generate_password_hash(password)

        conn = get_db_connection()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute('''INSERT INTO users (first_name, last_name, email, password, phone) 
                                VALUES (%s, %s, %s, %s, %s)''', 
                               (first_name, last_name, email, hashed_password, phone))
                conn.commit()
                flash('تم إنشاء الحساب بنجاح! يمكنك الآن تسجيل الدخول.', 'success')
                return redirect(url_for('login'))
            except mysql.connector.IntegrityError:
                flash('البريد الإلكتروني مستخدم بالفعل.', 'danger')
            finally:
                conn.close()
        else:
            flash('خطأ في الاتصال بقاعدة البيانات.', 'danger')

    return render_template('register.html')


