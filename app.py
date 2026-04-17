from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
import sqlite3
import os
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = os.urandom(24)
UPLOAD_FOLDER = 'static/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Initialize Database
def init_db():
    with sqlite3.connect('database.db') as conn:
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    full_name TEXT NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    dob TEXT NOT NULL,
                    phone TEXT UNIQUE NOT NULL,
                    password TEXT NOT NULL)
                ''')
        
        c.execute('''CREATE TABLE IF NOT EXISTS posts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    author TEXT NOT NULL,
                    image TEXT, 
                    content TEXT NOT NULL)
                ''')
        conn.commit()

init_db()

@app.route('/')
def index():
    with sqlite3.connect('database.db') as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM posts ORDER BY id DESC")
        posts = c.fetchall()
    return render_template('index.html', posts=posts)

@app.route('/home')
def home():
    if 'user_id' in session:
        return render_template('dashboard.html', user=session['user_name'])
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        full_name = request.form['full_name']
        email = request.form['email']
        dob = request.form['dob']
        phone = request.form['phone']
        password = generate_password_hash(request.form['password'])

        try:
            with sqlite3.connect('database.db') as conn:
                c = conn.cursor()
                c.execute("INSERT INTO users (full_name, email, dob, phone, password) VALUES (?, ?, ?, ?, ?)",
                          (full_name, email, dob, phone, password))
                conn.commit()
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Email or Phone already exists!', 'danger')
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        with sqlite3.connect('database.db') as conn:
            c = conn.cursor()
            c.execute("SELECT id, full_name, password FROM users WHERE email=?", (email,))
            user = c.fetchone()
        
        if user and check_password_hash(user[2], password):
            session['user_id'] = user[0]
            session['user_name'] = user[1]
            flash('Login successful!', 'success')
            return redirect(url_for('home'))
        else:
            flash('Invalid credentials!', 'danger')
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        flash('Please login first!', 'danger')
        return redirect(url_for('login'))
    return render_template('dashboard.html', user=session['user_name'])

@app.route('/newpost', methods=['GET', 'POST'])
def new_post():
    if 'user_id' not in session:
        flash('Please login first!', 'danger')
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        author = session['user_name']
        image = None
        
        if 'image' in request.files:
            file = request.files['image']
            if file.filename:
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                image = filename
        
        with sqlite3.connect('database.db') as conn:
            c = conn.cursor()
            c.execute("INSERT INTO posts (title, author, image, content) VALUES (?, ?, ?, ?)", 
                      (title, author, image, content))
            conn.commit()
        
        flash('Post created successfully!', 'success')
        return redirect(url_for('view_posts'))
    
    return render_template('new_post.html')

@app.route('/viewposts', methods=['GET', 'POST'])
def view_posts():
    if 'user_id' not in session:
        flash('Please login first!', 'danger')
        return redirect(url_for('login'))
    
    search_query = request.form.get('search', '')
    
    with sqlite3.connect('database.db') as conn:
        c = conn.cursor()
        if search_query:
            c.execute("SELECT * FROM posts WHERE title LIKE ?", ('%' + search_query + '%',))
        else:
            c.execute("SELECT * FROM posts")
        posts = c.fetchall()
    
    return render_template('view_posts.html', posts=posts, search_query=search_query)

@app.route('/deletepost/<int:post_id>', methods=['POST'])
def delete_post(post_id):
    if 'user_id' not in session:
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 403
    
    with sqlite3.connect('database.db') as conn:
        c = conn.cursor()
        c.execute("DELETE FROM posts WHERE id=?", (post_id,))
        conn.commit()
    
    flash('Post deleted successfully!', 'success')
    return jsonify({'status': 'success', 'message': 'Post deleted successfully'})

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully!', 'success')
    return redirect(url_for('login'))


@app.route('/post/<int:post_id>')
def view_post(post_id):
    with sqlite3.connect('database.db') as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM posts WHERE id=?", (post_id,))
        post = c.fetchone()
    
    if post is None:
        flash('Post not found!', 'danger')
        return redirect(url_for('index'))
    
    return render_template('post_detail.html', post=post)


if __name__ == '__main__':
    app.run(debug=True)