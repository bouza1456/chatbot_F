from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from Chat_Inter_optimisé1 import startChat, getquestion
from werkzeug.security import generate_password_hash, check_password_hash
import mysql.connector

app = Flask(__name__)
app.secret_key = 'chatbot chatbot chatbot'  # Nécessaire pour utiliser les sessions

# Connexion à la base de données MySQL
db_config = {
    'user': 'root',
    'password': 'root',
    'host': 'localhost',
    'database': 'telecom_assistant',
}

conn = mysql.connector.connect(**db_config)
cursor = conn.cursor()

@app.after_request
def add_header(response):
    response.cache_control.no_cache = True
    response.cache_control.no_store = True
    response.cache_control.must_revalidate = True
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

# Fonction pour détecter la langue du navigateur
def detect_language():
    supported_languages = ['en', 'fr', 'ar']
    browser_language = request.headers.get('Accept-Language')
    if browser_language:
        languages = browser_language.split(',')
        for lang in languages:
            lang_code = lang.split(';')[0]
            if lang_code[:2] in supported_languages:
                return lang_code[:2]
    return 'en'

@app.route('/')
def home():
    language = detect_language()
    return render_template(f'auth_{language}.html')


@app.route('/authenticate', methods=['POST'])
def authenticate():
    phone_number = request.form['phone_number']
    password = request.form['password']

    cursor.execute('SELECT id, password FROM users WHERE phone_number = %s', (phone_number,))
    user = cursor.fetchone()

    language = detect_language()
    if user and check_password_hash(user[1], password):
        session['user_id'] = user[0]
        return redirect(url_for('hello_world'))
    else:
        if language == 'fr':
            error = "Numéro de téléphone ou mot de passe incorrect"
        elif language == 'ar':
            error = "رقم الهاتف أو كلمة المرور غير صحيحة"
        else:  # Default to English
            error = "Incorrect phone number or password"
        
        return render_template(f'auth_{language}.html', error=error)

@app.route('/register', methods=['POST'])
def register():
    phone_number = request.form['phone_number']
    password = request.form['password']

    hashed_password = generate_password_hash(password)

    cursor.execute('INSERT INTO users (phone_number, password) VALUES (%s, %s)', (phone_number, hashed_password))
    conn.commit()

    cursor.execute('SELECT id FROM users WHERE phone_number = %s', (phone_number,))
    user = cursor.fetchone()
    session['user_id'] = user[0]

    return redirect(url_for('hello_world'))

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('home'))

@app.route('/chatbot')
def hello_world():
    if 'user_id' not in session:
        return redirect(url_for('home'))
    language = detect_language()
    return render_template(f"index_{language}.html")

@app.route('/predict', methods=['POST'])
def Predict():
    if 'user_id' not in session:
        return redirect(url_for('home'))
    res = getquestion()
    response = jsonify({'result': res})
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response

@app.route('/chat', methods=['POST'])
def Chat():
    if 'user_id' not in session:
        return redirect(url_for('home'))
    data = request.get_json()
    msg = data.get('text', '')
    language = detect_language()
    res = startChat(msg)
    response = jsonify({'result': res, "user": msg})
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response

if __name__ == '__main__':
    app.run()

# Ajouter la gestion des utilisateurs dans la base de données
def create_users_table():
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            phone_number VARCHAR(20) NOT NULL UNIQUE,
            password VARCHAR(255) NOT NULL
        )
    ''')
    conn.commit()

# Appelez cette fonction pour s'assurer que la table est créée
create_users_table()
