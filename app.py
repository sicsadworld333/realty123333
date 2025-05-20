from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
from datetime import datetime
import uuid
import requests
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

# Папка для изображений
IMAGE_FOLDER = 'static/images'
app.config['IMAGE_FOLDER'] = IMAGE_FOLDER
os.makedirs(IMAGE_FOLDER, exist_ok=True)

def init_db():
    with sqlite3.connect('realty.db') as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                email TEXT NOT NULL UNIQUE,
                password TEXT NOT NULL,
                phone_number TEXT NOT NULL,
                date_added TEXT NOT NULL,
                verification_code TEXT,
                is_verified INTEGER DEFAULT 0,
                reset_code TEXT
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS properties (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                title TEXT NOT NULL,
                description TEXT,
                price REAL NOT NULL,
                location TEXT NOT NULL,
                district TEXT,
                date_added TEXT NOT NULL,
                is_sold INTEGER DEFAULT 0,
                property_type TEXT NOT NULL,
                listing_type TEXT NOT NULL,
                area REAL,
                rooms INTEGER,
                floor INTEGER,
                floors INTEGER,
                year_built INTEGER,
                land_area REAL,
                has_basement INTEGER,
                has_garage INTEGER,
                wall_material TEXT,
                readiness INTEGER,
                has_electricity INTEGER,
                has_gas INTEGER,
                has_water INTEGER,
                has_sewerage INTEGER,
                photo_path TEXT NOT NULL,
                view_count INTEGER DEFAULT 0,
                favorite_count INTEGER DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS favorites (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                property_id INTEGER,
                date_added TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (property_id) REFERENCES properties(id)
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sender_id INTEGER,
                receiver_id INTEGER,
                property_id INTEGER,
                content TEXT NOT NULL,
                date_sent TEXT NOT NULL,
                FOREIGN KEY (sender_id) REFERENCES users(id),
                FOREIGN KEY (receiver_id) REFERENCES users(id),
                FOREIGN KEY (property_id) REFERENCES properties(id)
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                property_id INTEGER,
                transaction_type TEXT NOT NULL,
                date_completed TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (property_id) REFERENCES properties(id)
            )
        ''')
        conn.commit()

# Вызываем init_db при запуске приложения
init_db()

def send_verification_email(email, code):
    api_key = 'a49cefbd4605a38ddb83fa1f9b25dccb'
    url = 'https://api.mailopost.ru/v1/email/messages'
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    data = {
        'from_email': 'svd8312908@gmail.com',
        'to': email,
        'subject': 'Подтверждение регистрации на RealtyApp',
        'text': f'Здравствуйте!\n\nВы зарегистрировались на платформе RealtyApp. Чтобы подтвердить ваш email, используйте следующий код:\n\nКод подтверждения: {code}\n\nЕсли вы не регистрировались, просто проигнорируйте это письмо.\n\nС уважением,\nКоманда RealtyApp'
    }
    try:
        print(f"Отправка email на {email}...")
        response = requests.post(url, headers=headers, json=data)
        response_data = response.json() if response.text else {}
        if response.status_code in (200, 202) or response_data.get('status') == 'queued':
            print(f"Email успешно отправлен на {email} (статус: {response.text})")
        else:
            raise Exception(f"Не удалось отправить email: {response.text}")
    except requests.exceptions.RequestException as e:
        print(f"Сетевая ошибка: {e}")
        raise Exception(f"Не удалось отправить email из-за сетевой ошибки: {e}")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        phone_number = request.form['phone_number']
        if not phone_number.startswith('+375'):
            flash('Номер телефона должен начинаться с +375!', 'danger')
            return redirect(url_for('register'))
        date_added = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        with sqlite3.connect('realty.db') as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT email FROM users WHERE email = ?', (email,))
            if cursor.fetchone():
                flash('Этот email уже зарегистрирован!', 'danger')
                return redirect(url_for('register'))
            verification_code = str(uuid.uuid4())
            cursor.execute('INSERT INTO users (username, email, password, phone_number, date_added, verification_code, is_verified) VALUES (?, ?, ?, ?, ?, ?, ?)', 
                          (username, email, password, phone_number, date_added, verification_code, 0))
            conn.commit()
        # send_verification_email(email, verification_code)
        flash('Код подтверждения отправлен на ваш email! (или проверьте вручную, если email не работает)', 'info')
        session['email_to_verify'] = email
        return redirect(url_for('verify_code'))
    return render_template('register.html')

@app.route('/verify_code', methods=['GET', 'POST'])
def verify_code():
    if 'email_to_verify' not in session:
        flash('Сначала зарегистрируйтесь!', 'danger')
        return redirect(url_for('register'))
    if request.method == 'POST':
        code = request.form['code']
        email = session['email_to_verify']
        with sqlite3.connect('realty.db') as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT verification_code FROM users WHERE email = ?', (email,))
            result = cursor.fetchone()
            if result and result[0] == code:
                cursor.execute('UPDATE users SET is_verified = 1, verification_code = NULL WHERE email = ?', (email,))
                conn.commit()
                session.pop('email_to_verify', None)
                flash('Регистрация успешно завершена! Теперь вы можете войти.', 'success')
                return redirect(url_for('login'))
            else:
                flash('Неверный код подтверждения!', 'danger')
                return redirect(url_for('verify_code'))
    return render_template('verify_code.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        if not email or not password:
            flash('Пожалуйста, введите email и пароль!', 'danger')
            return redirect(url_for('login'))
        with sqlite3.connect('realty.db') as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM users WHERE email = ? AND password = ?', (email, password))
            user = cursor.fetchone()
            if user:
                if user[6] == 0:  # Проверяем is_verified
                    flash('Сначала подтвердите email!', 'danger')
                    session['email_to_verify'] = email
                    return redirect(url_for('verify_code'))
                session['user_id'] = user[0]
                flash('Вход выполнен!', 'success')
                return redirect(url_for('account', tab='dashboard'))
            else:
                flash('Неверный email или пароль!', 'danger')
                return redirect(url_for('login'))
    return render_template('login.html')

@app.route('/account/<tab>')
def account(tab):
    if 'user_id' not in session:
        flash('Пожалуйста, войдите!', 'danger')
        return redirect(url_for('login'))
    
    with sqlite3.connect('realty.db') as conn:
        cursor = conn.cursor()
        # Данные для вкладки "Мои объявления"
        cursor.execute('SELECT * FROM properties WHERE user_id = ? AND is_sold = 0', (session['user_id'],))
        properties = cursor.fetchall()
        
        # Данные для вкладки "Избранное"
        cursor.execute('SELECT p.* FROM properties p JOIN favorites f ON p.id = f.property_id WHERE f.user_id = ? AND p.is_sold = 0', (session['user_id'],))
        favorites = cursor.fetchall()
        
        # Данные для вкладки "Профиль"
        cursor.execute('SELECT username, email, phone_number, date_added FROM users WHERE id = ?', (session['user_id'],))
        user = cursor.fetchone()
        
        # История сделок
        cursor.execute('SELECT t.*, p.title FROM transactions t JOIN properties p ON t.property_id = p.id WHERE t.user_id = ?', (session['user_id'],))
        transactions = cursor.fetchall()
        
        # Данные для мессенджера
        cursor.execute('SELECT DISTINCT u.id, u.username FROM messages m JOIN users u ON u.id = m.sender_id WHERE m.receiver_id = ?', (session['user_id'],))
        contacts = cursor.fetchall()
        messages = []
        selected_contact = request.args.get('contact_id')
        if selected_contact:
            cursor.execute('''
                SELECT m.*, s.username AS sender_name, r.username AS receiver_name 
                FROM messages m 
                JOIN users s ON s.id = m.sender_id 
                JOIN users r ON r.id = m.receiver_id 
                WHERE (m.sender_id = ? AND m.receiver_id = ?) OR (m.sender_id = ? AND m.receiver_id = ?) 
                ORDER BY m.date_sent
            ''', (session['user_id'], selected_contact, selected_contact, session['user_id']))
            messages = cursor.fetchall()
    
    return render_template('account.html', 
                         active_tab=tab, 
                         properties=properties, 
                         favorites=favorites, 
                         user=user, 
                         transactions=transactions,
                         contacts=contacts,
                         messages=messages,
                         selected_contact=selected_contact)

@app.route('/add_listing/<listing_type>', methods=['GET', 'POST'])
def add_listing(listing_type):
    if 'user_id' not in session:
        return render_template('login_prompt.html')
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        price = request.form['price']
        location = request.form['location']
        district = request.form['district']
        date_added = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        property_type = request.form['property_type']
        area = request.form['area']
        rooms = request.form.get('rooms')
        floor = request.form.get('floor')
        floors = request.form.get('floors')
        year_built = request.form.get('year_built')
        land_area = request.form.get('land_area')
        has_basement = 1 if request.form.get('has_basement') else 0
        has_garage = 1 if request.form.get('has_garage') else 0
        wall_material = request.form.get('wall_material')
        readiness = request.form.get('readiness')
        has_electricity = 1 if request.form.get('has_electricity') else 0
        has_gas = 1 if request.form.get('has_gas') else 0
        has_water = 1 if request.form.get('has_water') else 0
        has_sewerage = 1 if request.form.get('has_sewerage') else 0
        
        if 'photo' not in request.files or not request.files['photo'].filename:
            flash('Фото обязательно для загрузки!', 'danger')
            return redirect(url_for('add_listing', listing_type=listing_type))
        
        file = request.files['photo']
        filename = f"{uuid.uuid4()}_{file.filename}"
        file.save(os.path.join(app.config['IMAGE_FOLDER'], filename))
        photo_path = f"images/{filename}"
        
        with sqlite3.connect('realty.db') as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO properties (
                    user_id, title, description, price, location, district, date_added, property_type, listing_type,
                    area, rooms, floor, floors, year_built, land_area, has_basement, has_garage, wall_material,
                    readiness, has_electricity, has_gas, has_water, has_sewerage, photo_path
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                session['user_id'], title, description, price, location, district, date_added, property_type, listing_type,
                area, rooms, floor, floors, year_built, land_area, has_basement, has_garage, wall_material,
                readiness, has_electricity, has_gas, has_water, has_sewerage, photo_path
            ))
            conn.commit()
        flash(f'Объявление ({listing_type}) добавлено!', 'success')
        return redirect(url_for('account', tab='dashboard'))
    return render_template('add_listing.html', listing_type=listing_type)

@app.route('/edit_property/<int:property_id>', methods=['GET', 'POST'])
def edit_property(property_id):
    if 'user_id' not in session:
        flash('Пожалуйста, войдите!', 'danger')
        return redirect(url_for('login'))
    with sqlite3.connect('realty.db') as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM properties WHERE id = ? AND user_id = ?', (property_id, session['user_id']))
        property = cursor.fetchone()
        if not property:
            flash('Объявление не найдено или вы не являетесь его владельцем!', 'danger')
            return redirect(url_for('account', tab='dashboard'))
        
        if request.method == 'POST':
            title = request.form['title']
            description = request.form['description']
            price = request.form['price']
            location = request.form['location']
            district = request.form['district']
            property_type = request.form['property_type']
            area = request.form['area']
            rooms = request.form.get('rooms')
            floor = request.form.get('floor')
            floors = request.form.get('floors')
            year_built = request.form.get('year_built')
            land_area = request.form.get('land_area')
            has_basement = 1 if request.form.get('has_basement') else 0
            has_garage = 1 if request.form.get('has_garage') else 0
            wall_material = request.form.get('wall_material')
            readiness = request.form.get('readiness')
            has_electricity = 1 if request.form.get('has_electricity') else 0
            has_gas = 1 if request.form.get('has_gas') else 0
            has_water = 1 if request.form.get('has_water') else 0
            has_sewerage = 1 if request.form.get('has_sewerage') else 0
            
            photo_path = property[24]  # Сохраняем старое фото, если новое не загружено
            if 'photo' in request.files and request.files['photo'].filename:
                file = request.files['photo']
                filename = f"{uuid.uuid4()}_{file.filename}"
                file.save(os.path.join(app.config['IMAGE_FOLDER'], filename))
                photo_path = f"images/{filename}"
            
            cursor.execute('''
                UPDATE properties SET
                    title = ?, description = ?, price = ?, location = ?, district = ?, 
                    property_type = ?, area = ?, rooms = ?, floor = ?, floors = ?, 
                    year_built = ?, land_area = ?, has_basement = ?, has_garage = ?, 
                    wall_material = ?, readiness = ?, has_electricity = ?, has_gas = ?, 
                    has_water = ?, has_sewerage = ?, photo_path = ?
                WHERE id = ? AND user_id = ?
            ''', (
                title, description, price, location, district, property_type, area, 
                rooms, floor, floors, year_built, land_area, has_basement, has_garage, 
                wall_material, readiness, has_electricity, has_gas, has_water, has_sewerage, 
                photo_path, property_id, session['user_id']
            ))
            conn.commit()
            flash('Объявление обновлено!', 'success')
            return redirect(url_for('account', tab='dashboard'))
    
    return render_template('edit_property.html', property=property)

@app.route('/sell', methods=['GET', 'POST'])
def sell():
    if 'user_id' not in session:
        return render_template('login_prompt.html')
    return redirect(url_for('add_listing', listing_type='sale'))

@app.route('/rent_property', methods=['GET', 'POST'])
def rent_property():
    if 'user_id' not in session:
        return render_template('login_prompt.html')
    return redirect(url_for('add_listing', listing_type='rent'))

@app.route('/buy')
def buy():
    return redirect(url_for('catalog', listing_type='sale'))

@app.route('/catalog')
def catalog():
    listing_type = request.args.get('listing_type', 'all')
    property_type = request.args.get('property_type', 'all')
    rooms = request.args.get('rooms', 'all')
    district = request.args.get('district', 'all')
    price_max = request.args.get('price_max', None)
    area_max = request.args.get('area_max', None)
    land_area_max = request.args.get('land_area_max', None)
    has_basement = request.args.get('has_basement', 'all')
    has_garage = request.args.get('has_garage', 'all')
    has_electricity = request.args.get('has_electricity', 'all')
    has_gas = request.args.get('has_gas', 'all')
    has_water = request.args.get('has_water', 'all')
    has_sewerage = request.args.get('has_sewerage', 'all')

    query = 'SELECT * FROM properties WHERE is_sold = 0'
    params = []

    if listing_type != 'all':
        query += ' AND listing_type = ?'
        params.append(listing_type)
    if property_type != 'all':
        query += ' AND property_type = ?'
        params.append(property_type)
    if rooms != 'all':
        query += ' AND rooms = ?'
        params.append(int(rooms))
    if district != 'all':
        query += ' AND district = ?'
        params.append(district)
    if price_max:
        query += ' AND price <= ?'
        params.append(float(price_max))
    if area_max:
        query += ' AND area <= ?'
        params.append(float(area_max))
    if land_area_max:
        query += ' AND land_area <= ?'
        params.append(float(land_area_max))
    if has_basement != 'all':
        query += ' AND has_basement = ?'
        params.append(1 if has_basement == 'yes' else 0)
    if has_garage != 'all':
        query += ' AND has_garage = ?'
        params.append(1 if has_garage == 'yes' else 0)
    if has_electricity != 'all':
        query += ' AND has_electricity = ?'
        params.append(1 if has_electricity == 'yes' else 0)
    if has_gas != 'all':
        query += ' AND has_gas = ?'
        params.append(1 if has_gas == 'yes' else 0)
    if has_water != 'all':
        query += ' AND has_water = ?'
        params.append(1 if has_water == 'yes' else 0)
    if has_sewerage != 'all':
        query += ' AND has_sewerage = ?'
        params.append(1 if has_sewerage == 'yes' else 0)

    with sqlite3.connect('realty.db') as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        properties = cursor.fetchall()
        favorite_ids = []
        if 'user_id' in session:
            cursor.execute('SELECT property_id FROM favorites WHERE user_id = ?', (session['user_id'],))
            favorite_ids = [row[0] for row in cursor.fetchall()]

    return render_template('catalog.html', properties=properties, listing_type=listing_type, favorite_ids=favorite_ids)

@app.route('/property/<int:property_id>')
def property_detail(property_id):
    with sqlite3.connect('realty.db') as conn:
        cursor = conn.cursor()
        # Увеличиваем счётчик просмотров
        cursor.execute('UPDATE properties SET view_count = view_count + 1 WHERE id = ?', (property_id,))
        cursor.execute('SELECT * FROM properties WHERE id = ?', (property_id,))
        property = cursor.fetchone()
        if not property:
            flash('Объект не найден!', 'danger')
            return redirect(url_for('catalog'))
        # Информация о владельце
        cursor.execute('SELECT username, phone_number, date_added FROM users WHERE id = ?', (property[1],))
        owner = cursor.fetchone()
        # Обновляем favorite_count
        cursor.execute('SELECT COUNT(*) FROM favorites WHERE property_id = ?', (property_id,))
        favorite_count = cursor.fetchone()[0]
        cursor.execute('UPDATE properties SET favorite_count = ? WHERE id = ?', (favorite_count, property_id))
        conn.commit()
    
    is_owner = 'user_id' in session and session['user_id'] == property[1]
    return render_template('property_detail.html', property=property, owner=owner, is_owner=is_owner)

@app.route('/send_message/<int:property_id>', methods=['POST'])
def send_message(property_id):
    if 'user_id' not in session:
        flash('Пожалуйста, войдите!', 'danger')
        return redirect(url_for('login'))
    with sqlite3.connect('realty.db') as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT user_id FROM properties WHERE id = ?', (property_id,))
        property = cursor.fetchone()
        if not property:
            flash('Объявление не найдено!', 'danger')
            return redirect(url_for('catalog'))
        receiver_id = property[0]
        if receiver_id == session['user_id']:
            flash('Вы не можете отправить сообщение самому себе!', 'danger')
            return redirect(url_for('property_detail', property_id=property_id))
        content = request.form['message']
        date_sent = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute('INSERT INTO messages (sender_id, receiver_id, property_id, content, date_sent) VALUES (?, ?, ?, ?, ?)',
                      (session['user_id'], receiver_id, property_id, content, date_sent))
        conn.commit()
    flash('Сообщение отправлено!', 'success')
    return redirect(url_for('account', tab='messenger', contact_id=receiver_id))

@app.route('/evaluation', methods=['GET', 'POST'])
def evaluation():
    if 'user_id' not in session:
        return render_template('login_prompt.html')
    if request.method == 'POST':
        property_type = request.form['property_type']
        area = request.form['area']
        location = request.form['location']
        contact_info = request.form['contact_info']
        date_requested = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        with sqlite3.connect('realty.db') as conn:
            cursor = conn.cursor()
            cursor.execute('INSERT INTO evaluations (user_id, property_type, area, location, contact_info, date_requested) VALUES (?, ?, ?, ?, ?, ?)',
                          (session['user_id'], property_type, area, location, contact_info, date_requested))
            conn.commit()
        flash('Заявка на оценку отправлена! Специалист свяжется с вами.', 'success')
        return redirect(url_for('account', tab='dashboard'))
    return render_template('evaluation.html')

@app.route('/change_password', methods=['GET', 'POST'])
def change_password():
    if 'user_id' not in session:
        flash('Пожалуйста, войдите!', 'danger')
        return redirect(url_for('login'))
    if request.method == 'POST':
        old_password = request.form['old_password']
        new_password = request.form['new_password']
        confirm_password = request.form['confirm_password']
        if new_password != confirm_password:
            flash('Новые пароли не совпадают!', 'danger')
            return redirect(url_for('change_password'))
        with sqlite3.connect('realty.db') as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT password FROM users WHERE id = ?', (session['user_id'],))
            current_password = cursor.fetchone()
            if current_password and current_password[0] == old_password:
                cursor.execute('UPDATE users SET password = ? WHERE id = ?', (new_password, session['user_id']))
                conn.commit()
                flash('Пароль успешно изменён!', 'success')
                return redirect(url_for('account', tab='dashboard'))
            else:
                flash('Старый пароль неверен!', 'danger')
                return redirect(url_for('change_password'))
    return render_template('change_password.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('Вы вышли из системы!', 'success')
    return redirect(url_for('login'))

@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form['email']
        with sqlite3.connect('realty.db') as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
            user = cursor.fetchone()
            if user:
                reset_code = str(uuid.uuid4())
                cursor.execute('UPDATE users SET reset_code = ? WHERE email = ?', (reset_code, email))
                conn.commit()
                send_verification_email(email, reset_code)
                flash('Код для сброса пароля отправлен на ваш email!', 'info')
                session['email_to_reset'] = email
                return redirect(url_for('reset_password'))
            else:
                flash('Email не найден!', 'danger')
                return redirect(url_for('forgot_password'))
    return render_template('forgot_password.html')

@app.route('/reset_password', methods=['GET', 'POST'])
def reset_password():
    if 'email_to_reset' not in session:
        flash('Сначала запросите код восстановления!', 'danger')
        return redirect(url_for('forgot_password'))
    if request.method == 'POST':
        code = request.form['code']
        new_password = request.form['new_password']
        email = session['email_to_reset']
        with sqlite3.connect('realty.db') as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT reset_code FROM users WHERE email = ?', (email,))
            result = cursor.fetchone()
            if result and result[0] == code:
                cursor.execute('UPDATE users SET password = ?, reset_code = NULL WHERE email = ?', (new_password, email))
                conn.commit()
                session.pop('email_to_reset', None)
                flash('Пароль успешно изменён! Теперь вы можете войти.', 'success')
                return redirect(url_for('login'))
            else:
                flash('Неверный код!', 'danger')
                return redirect(url_for('reset_password'))
    return render_template('reset_password.html')

@app.route('/toggle_favorite/<int:property_id>', methods=['POST'])
def toggle_favorite(property_id):
    if 'user_id' not in session:
        flash('Пожалуйста, войдите!', 'danger')
        return redirect(url_for('login'))
    with sqlite3.connect('realty.db') as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT id FROM favorites WHERE user_id = ? AND property_id = ?', (session['user_id'], property_id))
        existing = cursor.fetchone()
        if existing:
            cursor.execute('DELETE FROM favorites WHERE user_id = ? AND property_id = ?', (session['user_id'], property_id))
            flash('Удалено из избранного!', 'success')
        else:
            cursor.execute('INSERT INTO favorites (user_id, property_id, date_added) VALUES (?, ?, ?)',
                          (session['user_id'], property_id, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
            flash('Добавлено в избранное!', 'success')
        conn.commit()
    return redirect(request.referrer or url_for('catalog'))

@app.route('/delete_property/<int:property_id>', methods=['POST'])
def delete_property(property_id):
    if 'user_id' not in session:
        flash('Пожалуйста, войдите!', 'danger')
        return redirect(url_for('login'))
    with sqlite3.connect('realty.db') as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT user_id FROM properties WHERE id = ?', (property_id,))
        prop = cursor.fetchone()
        if prop and prop[0] == session['user_id']:
            cursor.execute('DELETE FROM properties WHERE id = ?', (property_id,))
            conn.commit()
            flash('Объявление удалено!', 'success')
        else:
            flash('Ошибка удаления! Объявление не найдено или вы не являетесь его владельцем.', 'danger')
    return redirect(url_for('account', tab='dashboard'))

@app.route('/delete_account', methods=['POST'])
def delete_account():
    if 'user_id' not in session:
        flash('Пожалуйста, войдите!', 'danger')
        return redirect(url_for('login'))
    with sqlite3.connect('realty.db') as conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM properties WHERE user_id = ?', (session['user_id'],))
        cursor.execute('DELETE FROM users WHERE id = ?', (session['user_id'],))
        conn.commit()
    session.pop('user_id', None)
    flash('Аккаунт удалён!', 'success')
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)