from flask import Flask, render_template, request, redirect, url_for, flash, session
import mysql.connector
from mysql.connector import Error
from werkzeug.security import generate_password_hash, check_password_hash
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)

# Secret key for session management
app.secret_key = os.urandom(24)

# Upload folder configuration
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf'}
app.config['UPLOAD_FOLDER'] = 'uploads'  # مسار نسبي لحفظ الملفات



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


@app.route('/portfolio')
def portfolio():
    if 'user_id' not in session:
        flash('يرجى تسجيل الدخول أولاً.', 'warning')
        return redirect(url_for('login'))

    print(session)  # طباعة محتويات الجلسة لمراجعتها
    return render_template('portfolio.html', user=session)

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'user_id' not in session:
        flash('يرجى تسجيل الدخول.', 'warning')
        return redirect(url_for('login'))

    conn = get_db_connection()
    if conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute('SELECT * FROM users WHERE id = %s', (session['user_id'],))
        user = cursor.fetchone()

        if request.method == 'POST':
            first_name = request.form.get('first_name')
            last_name = request.form.get('last_name')
            email = request.form.get('email')
            phone = request.form.get('phone')  # Récupérer le téléphone
            description = request.form.get('description', '')  # Récupérer la description
            photo = request.files.get('photo')

            photo_filename = user['photo']
            if photo and allowed_file(photo.filename):
                photo_filename = secure_filename(photo.filename)
                photo.save(os.path.join(app.config['UPLOAD_FOLDER'], photo_filename))

            try:
                cursor.execute('''UPDATE users 
                                  SET first_name = %s, last_name = %s, email = %s, phone = %s, description = %s, photo = %s 
                                  WHERE id = %s''', 
                               (first_name, last_name, email, phone, description, photo_filename, session['user_id']))
                conn.commit()

                # Mettre à jour la session avec les nouvelles informations
                session['first_name'] = first_name
                session['last_name'] = last_name
                session['email'] = email
                session['phone'] = phone  # Mettre à jour le téléphone dans la session
                session['photo'] = photo_filename
                session['description'] = description
                flash('تم تحديث البيانات بنجاح!', 'success')

                return redirect(url_for('portfolio'))

            except Error as e:
                flash(f'خطأ أثناء تحديث البيانات: {e}', 'danger')

        conn.close()
        return render_template('dashboard.html', user=user)
    else:
        flash('خطأ في الاتصال بقاعدة البيانات.', 'danger')
        return redirect(url_for('login'))



@app.route('/login-jobs', methods=['GET', 'POST'])
def login_employer():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM employers WHERE email = %s", (email,))
        employer = cursor.fetchone()
        conn.close()

        if employer and check_password_hash(employer['password'], password):
            session['employer_id'] = employer['id']
            session['company_name'] = employer['company_name']
            flash('تم تسجيل الدخول بنجاح!', 'success')
            return redirect(url_for('employer_dashboard'))
        else:
            flash('بيانات تسجيل الدخول غير صحيحة.', 'danger')

    return render_template('login-jobs.html')
@app.route('/login-jobs')
def login_jobs():
    return render_template('login-jobs.html')

@app.route('/register-employer', methods=['GET', 'POST'])
def register_employer():
    if request.method == 'POST':
        company_name = request.form.get('company_name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        address = request.form.get('address')
        description = request.form.get('description')
        password = request.form.get('password')

        hashed_password = generate_password_hash(password)

        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO employers (company_name, email, phone, address, description, password)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (company_name, email, phone, address, description, hashed_password))
            conn.commit()
            flash('تم إنشاء الحساب بنجاح! يمكنك الآن تسجيل الدخول.', 'success')
            return redirect(url_for('login_employer'))
        except mysql.connector.IntegrityError:
            flash('البريد الإلكتروني مستخدم بالفعل.', 'danger')
        finally:
            conn.close()

    return render_template('register-employer.html')
@app.route('/employer-dashboard')
def employer_dashboard():
    if 'employer_id' not in session:
        flash('يرجى تسجيل الدخول أولاً.', 'warning')
        return redirect(url_for('login_employer'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # جلب الوظائف التي نشرها صاحب العمل
    cursor.execute("SELECT * FROM jobs WHERE employer_id = %s", (session['employer_id'],))
    jobs = cursor.fetchall()

    # جلب طلبات التوظيف
    cursor.execute("""
        SELECT applications.*, users.first_name AS user_name, jobs.job_title
        FROM applications
        JOIN users ON applications.user_id = users.id
        JOIN jobs ON applications.job_id = jobs.id
        WHERE jobs.employer_id = %s
    """, (session['employer_id'],))
    applications = cursor.fetchall()

    conn.close()
    return render_template('employer-dashboard.html', company_name=session['company_name'], jobs=jobs, applications=applications)


@app.route('/add-job', methods=['POST'])
def add_job():
    if 'employer_id' not in session:
        flash('يرجى تسجيل الدخول أولاً.', 'warning')
        return redirect(url_for('login_employer'))

    job_title = request.form.get('job_title')
    job_description = request.form.get('job_description')
    location = request.form.get('location')
    salary = request.form.get('salary')

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO jobs (employer_id, job_title, job_description, location, salary)
        VALUES (%s, %s, %s, %s, %s)
    """, (session['employer_id'], job_title, job_description, location, salary))
    conn.commit()
    conn.close()

    flash('تمت إضافة الوظيفة بنجاح!', 'success')
    return redirect(url_for('employer_dashboard'))


@app.route('/delete-job/<int:job_id>')
def delete_job(job_id):
    if 'employer_id' not in session:
        flash('يرجى تسجيل الدخول أولاً.', 'warning')
        return redirect(url_for('login_employer'))

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM jobs WHERE id = %s AND employer_id = %s", (job_id, session['employer_id']))
    conn.commit()
    conn.close()

    flash('تم حذف الوظيفة بنجاح!', 'danger')
    return redirect(url_for('employer_dashboard'))

@app.route('/edit-job/<int:job_id>', methods=['GET', 'POST'])
def edit_job(job_id):
    if 'employer_id' not in session:
        flash('يرجى تسجيل الدخول أولاً.', 'warning')
        return redirect(url_for('login_employer'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Handle GET request to show job details in the form
    if request.method == 'GET':
        cursor.execute("SELECT * FROM jobs WHERE id = %s AND employer_id = %s", (job_id, session['employer_id']))
        job = cursor.fetchone()
        if job:
            return render_template('edit-job.html', job=job)
        else:
            flash('الوظيفة غير موجودة.', 'danger')
            return redirect(url_for('employer_dashboard'))

    # Handle POST request to update the job
    if request.method == 'POST':
        job_title = request.form.get('job_title')
        job_description = request.form.get('job_description')
        location = request.form.get('location')
        salary = request.form.get('salary')

        cursor.execute("""
            UPDATE jobs SET job_title = %s, job_description = %s, location = %s, salary = %s
            WHERE id = %s AND employer_id = %s
        """, (job_title, job_description, location, salary, job_id, session['employer_id']))
        conn.commit()
        conn.close()

        flash('تم تحديث الوظيفة بنجاح!', 'success')
        return redirect(url_for('employer_dashboard'))
@app.route('/view-jobs', methods=['GET'])
def view_jobs():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT * FROM jobs')
    jobs = cursor.fetchall()
    conn.close()

    return render_template('view-jobs.html', jobs=jobs)
@app.route('/logout')
def logout():
    session.clear()
    flash('تم تسجيل الخروج بنجاح.', 'info')
    return redirect(url_for('login'))
@app.route('/apply-job/<int:job_id>', methods=['GET', 'POST'])
def apply_job(job_id):
    if 'user_id' not in session:
        flash('يرجى تسجيل الدخول أولاً.', 'warning')
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if request.method == 'POST':
        cover_letter = request.form.get('cover_letter')
        resume = request.files.get('resume')

        if not cover_letter or not resume:
            flash('يرجى إدخال رسالة التغطية ورفع السيرة الذاتية.', 'danger')
            return redirect(url_for('apply_job', job_id=job_id))

        if resume and allowed_file(resume.filename):
            resume_filename = secure_filename(resume.filename)
            resume_path = os.path.join(app.config['UPLOAD_FOLDER'], resume_filename)
            resume.save(resume_path)

            try:
                # حفظ البيانات في قاعدة البيانات
                cursor.execute("""
                    INSERT INTO applications (job_id, user_id, cover_letter, resume)
                    VALUES (%s, %s, %s, %s)
                """, (job_id, session['user_id'], cover_letter, resume_filename))
                conn.commit()

                # إشعار صاحب العمل
                cursor.execute("""
                    SELECT employers.email FROM employers 
                    JOIN jobs ON employers.id = jobs.employer_id
                    WHERE jobs.id = %s
                """, (job_id,))
                employer = cursor.fetchone()

                if employer:
                    employer_email = employer['email']
                    flash('تم تقديم طلبك بنجاح! سيتم إشعار الشركة.', 'success')
                    # هنا يمكنك إرسال بريد إلكتروني لصاحب العمل إذا كنت تستخدم `Flask-Mail`
                
                return redirect(url_for('view_jobs'))

            except Error as e:
                flash(f'حدث خطأ أثناء تقديم الطلب: {e}', 'danger')

        else:
            flash('يرجى رفع ملف PDF فقط.', 'danger')

    conn.close()
    return render_template('apply-job.html', job_id=job_id)

@app.route('/view-applications/<int:job_id>')
def view_applications(job_id):
    if 'employer_id' not in session:
        flash('يرجى تسجيل الدخول أولاً.', 'warning')
        return redirect(url_for('login_employer'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('''
        SELECT applications.*, users.first_name, users.last_name, users.email 
        FROM applications 
        JOIN users ON applications.user_id = users.id 
        WHERE job_id = %s
    ''', (job_id,))
    applications = cursor.fetchall()
    conn.close()

    return render_template('view-applications.html', applications=applications)
if __name__ == '__main__':
    app.run(debug=True)
