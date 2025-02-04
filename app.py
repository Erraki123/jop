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


@app.route('/portfolio', methods=['GET', 'POST'])
def portfolio():
    if 'user_id' not in session:
        flash('يرجى تسجيل الدخول أولاً.', 'warning')
        return redirect(url_for('login'))

    print(session)  # طباعة محتويات الجلسة لمراجعتها
    if request.method == 'POST':
        # Handle the POST logic here (e.g. saving data)
        flash('تم إرسال البيانات بنجاح.', 'success')
        return redirect(url_for('portfolio'))

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
            phone = request.form.get('phone')
            description = request.form.get('description', '')
            photo = request.files.get('photo')
            is_published = request.form.get('is_published') == 'on'  # تحقق مما إذا كان المستخدم قد حدد النشر

            photo_filename = user['photo']
            if photo and allowed_file(photo.filename):
                photo_filename = secure_filename(photo.filename)
                photo.save(os.path.join(app.config['IMAGE_UPLOAD_FOLDER'], photo_filename))

            try:
                cursor.execute('''UPDATE users 
                                  SET first_name = %s, last_name = %s, email = %s, phone = %s, description = %s, 
                                      photo = %s, is_published = %s
                                  WHERE id = %s''', 
                               (first_name, last_name, email, phone, description, photo_filename, is_published, session['user_id']))
                conn.commit()

                # تحديث البيانات في الجلسة
                session['first_name'] = first_name
                session['last_name'] = last_name
                session['email'] = email
                session['phone'] = phone
                session['photo'] = photo_filename
                session['description'] = description
                session['is_published'] = is_published
                flash('تم تحديث البيانات بنجاح!', 'success')

                return redirect(url_for('portfolio'))

            except Error as e:
                flash(f'خطأ أثناء تحديث البيانات: {e}', 'danger')

        conn.close()  # إغلاق الاتصال بقاعدة البيانات بعد استخدامه
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
@app.route('/employer-dashboard', methods=['GET', 'POST'])
def employer_dashboard():
    if 'employer_id' not in session:
        flash('يرجى تسجيل الدخول أولاً.', 'warning')
        return redirect(url_for('login_employer'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Récupération des critères de recherche
    job_title = request.args.get('job_title', '')
    job_description = request.args.get('job_description', '')
    location = request.args.get('location', '')

    # Requête SQL avec des filtres si des critères sont fournis
    query = "SELECT * FROM jobs WHERE employer_id = %s"
    filters = [session['employer_id']]

    if job_title:
        query += " AND job_title LIKE %s"
        filters.append(f"%{job_title}%")
    if job_description:
        query += " AND job_description LIKE %s"
        filters.append(f"%{job_description}%")
    if location:
        query += " AND location LIKE %s"
        filters.append(f"%{location}%")

    cursor.execute(query, tuple(filters))
    jobs = cursor.fetchall()

    # Récupération des demandes d'emploi
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

    # Supprimer les candidatures associées avant de supprimer l'offre
    cursor.execute("DELETE FROM applications WHERE job_id = %s", (job_id,))
    conn.commit()

    # Supprimer l'offre d'emploi
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
            resume_path = os.path.join(app.config['CV_UPLOAD_FOLDER'], resume_filename)
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
from flask import flash, redirect, url_for, render_template
@app.route('/handle-application/<int:application_id>/<string:action>', methods=['POST'])
def handle_application(application_id, action):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Obtenir les détails de la candidature avec l'email de l'utilisateur et job_id
        cursor.execute("""
            SELECT a.*, u.email, a.job_id
            FROM applications a
            JOIN users u ON a.user_id = u.id
            WHERE a.id = %s
        """, (application_id,))
        application = cursor.fetchone()

        if application:
            job_id = application['job_id']  # Sauvegarder le job_id avant toute action

            if action == 'accept':
                # Mettre à jour le statut à "Accepté"
                cursor.execute("""
                    UPDATE applications
                    SET status = 'Accepté'
                    WHERE id = %s
                """, (application_id,))
                conn.commit()

                # Envoyer un email de confirmation
                user_email = application['email']
                subject = "Mise à jour sur votre candidature"
                body = "Félicitations ! Votre candidature a été acceptée."

                msg = Message(subject, recipients=[user_email])
                msg.body = body
                try:
                    mail.send(msg)
                    flash(f"L'email a été envoyé à {user_email} avec succès", 'success')
                except Exception as e:
                    flash(f"Erreur d'envoi de l'email: {str(e)}", 'error')

            elif action == 'delete':
                # Supprimer la candidature
                cursor.execute("""
                    DELETE FROM applications
                    WHERE id = %s
                """, (application_id,))
                conn.commit()

                flash("La candidature a été supprimée", 'success')

            cursor.close()
            conn.close()

            # Utilisation de url_for pour générer correctement l'URL
            return redirect(url_for('view_applications', job_id=job_id))

        else:
            flash("La candidature n'a pas été trouvée.", 'error')
            return redirect(url_for('view_applications', job_id=job_id))

    except mysql.connector.Error as err:
        print(f"Error: {err}")
        flash("Erreur dans la base de données", 'error')
        return redirect(url_for('view_applications', job_id=job_id))

    except Exception as e:
        print(f"Error: {e}")
        flash("Erreur inattendue", 'error')
        return redirect(url_for('view_applications', job_id=job_id))

@app.route('/view-applications/<int:job_id>')
def view_applications(job_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Récupérer toutes les candidatures pour un job spécifique
        cursor.execute("""
            SELECT a.*, u.email
            FROM applications a
            JOIN users u ON a.user_id = u.id
            WHERE a.job_id = %s
        """, (job_id,))
        applications = cursor.fetchall()

        cursor.close()
        conn.close()

        return render_template('view-applications.html', applications=applications, job_id=job_id)

    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return "Erreur dans la base de données", 500
@app.route('/search-jobs', methods=['GET'])
def search_jobs():
    search_query = request.args.get('q', '')

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT * FROM jobs
        WHERE job_title LIKE %s OR job_description LIKE %s
    """, ('%' + search_query + '%', '%' + search_query + '%'))

    jobs = cursor.fetchall()
    
    cursor.close()
    conn.close()

    return render_template('search-results.html', jobs=jobs, search_query=search_query)
@app.route('/publish-profile', methods=['POST'])
def publish_profile():
    # التأكد من أن المستخدم مسجل دخوله
    if 'user_id' not in session:
        flash('يرجى تسجيل الدخول أولاً.', 'warning')
        return redirect(url_for('login'))

    user_id = session['user_id']

    # الاتصال بقاعدة البيانات
    conn = get_db_connection()
    if conn is None:
        flash('حدث خطأ في الاتصال بقاعدة البيانات.', 'danger')
        return redirect(url_for('dashboard'))

    # تحديث حالة النشر في قاعدة البيانات
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET is_published = TRUE WHERE id = %s", (user_id,))
    conn.commit()

    cursor.close()
    conn.close()

    flash('تم نشر بروفايلك بنجاح!', 'success')
    return redirect(url_for('portfolio'))  # العودة إلى لوحة التحكم
@app.route('/view-profiles', methods=['GET'])
def view_profiles():
    # السماح لأصحاب العمل بمشاهدة الملفات الشخصية أيضًا
    if 'user_id' not in session and 'employer_id' not in session:
        flash('يرجى تسجيل الدخول.', 'warning')
        return redirect(url_for('login'))

    search_query = request.args.get('search', '')  # الحصول على الاستعلام من GET
    
    # الاتصال بقاعدة البيانات
    conn = get_db_connection()
    if conn is None:
        flash('حدث خطأ في الاتصال بقاعدة البيانات.', 'danger')
        return redirect(url_for('dashboard'))

    cursor = conn.cursor(dictionary=True)

    # تعديل الاستعلام ليشمل البحث
    if search_query:
        # البحث عن المستخدمين بناءً على الاسم أو الوصف
        cursor.execute("SELECT * FROM users WHERE (first_name LIKE %s OR last_name LIKE %s OR description LIKE %s) AND is_published = TRUE", 
                       ('%' + search_query + '%', '%' + search_query + '%', '%' + search_query + '%'))
    else:
        # إذا لم يكن هناك استعلام بحث، إظهار جميع المستخدمين
        cursor.execute("SELECT * FROM users WHERE is_published = TRUE")
    
    users = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template('view_profiles.html', users=users, search_query=search_query)
@app.route('/delete-application/<int:application_id>', methods=['POST'])
def delete_application(application_id):
    try:
        # الاتصال بقاعدة البيانات
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # حذف الطلب من قاعدة البيانات
        cursor.execute("""
            DELETE FROM applications WHERE id = %s
        """, (application_id,))
        conn.commit()

        cursor.close()
        conn.close()

        flash("تم حذف الطلب بنجاح", 'success')
        return redirect(url_for('view_applications'))

    except mysql.connector.Error as err:
        print(f"Error: {err}")
        flash("حدث خطأ في قاعدة البيانات أثناء الحذف", 'error')
        return redirect(url_for('view_applications'))
    except Exception as e:
        print(f"Error: {e}")
        flash("حدث خطأ غير متوقع", 'error')
        return redirect(url_for('view_applications'))
@app.route('/about')
def about():
    return render_template('about.html')
@app.route('/view-profile/<int:user_id>', methods=['GET'])
def view_profile_detail(user_id):
    # التأكد من أن المستخدم مسجل دخوله
    if 'user_id' not in session and 'employer_id' not in session:
        flash('يرجى تسجيل الدخول.', 'warning')
        return redirect(url_for('login'))
    
    # الاتصال بقاعدة البيانات
    conn = get_db_connection()
    if conn is None:
        flash('حدث خطأ في الاتصال بقاعدة البيانات.', 'danger')
        return redirect(url_for('dashboard'))

    cursor = conn.cursor(dictionary=True)

    # الحصول على تفاصيل المستخدم
    cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
    user = cursor.fetchone()

    cursor.close()
    conn.close()

    if user:
        return render_template('profile_detail.html', user=user)
    else:
        flash('المستخدم غير موجود.', 'danger')
        return redirect(url_for('dashboard'))


@app.route('/contact')
def contact():
    return render_template('contact.html')
if __name__ == '__main__':
    app.run(debug=True)

