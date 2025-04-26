from flask import Flask, render_template, request, redirect,url_for,flash, session
import sqlite3
import random
import os

app = Flask(__name__)
app.secret_key = "secret_key_for_session"  # Required for session management
# Initialize the SQLite database (if it doesn't exist)
def visit_db():
    conn = sqlite3.connect('visitor_count.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS visitors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            count INTEGER
        )
    ''')
    # Initialize count if it's the first time
    cursor.execute('SELECT count FROM visitors WHERE id = 1')
    result = cursor.fetchone()
    if not result:
        cursor.execute('INSERT INTO visitors (count) VALUES (0)')
    conn.commit()
    conn.close()

# Function to increment and retrieve visitor count
def get_visitor_count():
    conn = sqlite3.connect('visitor_count.db')
    cursor = conn.cursor()
    cursor.execute('SELECT count FROM visitors WHERE id = 1')
    count = cursor.fetchone()[0]
    cursor.execute('UPDATE visitors SET count = count + 1 WHERE id = 1')
    conn.commit()
    conn.close()
    return count
# Initialize DB
def init_db():
    conn = sqlite3.connect('votes.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS actors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            votes INTEGER DEFAULT 0
        )
    ''')
    conn.commit()
    conn.close()

# Seed Actors (Run only once)
def seed_actors():
    conn = sqlite3.connect('votes.db')
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM actors")
    if c.fetchone()[0] == 0:
        sample_actors = ['Vijay', 'Ajith', 'Suriya', 'Dhanush', 'Vikram']
        for actor in sample_actors:
            c.execute("INSERT INTO actors (name, votes) VALUES (?, 0)", (actor,))
    conn.commit()
    conn.close()
IMAGE_FOLDER = 'static/images/'

VOTE_FILE = 'votes.txt'  # Store votes in a text file
# Admin credentials
ADMIN_USERNAME = 'admin'
ADMIN_PASSWORD = 'password'  # Change this to something more secure in production!

# Helper function to read votes from the file
def get_votes():
    votes = {}
    if os.path.exists(VOTE_FILE):
        with open(VOTE_FILE, 'r') as file:
            for line in file:
                actor = line.strip()
                if actor:
                    if actor in votes:
                        votes[actor] += 1
                    else:
                        votes[actor] = 1
    return votes

@app.route('/')
def home():
    # Get all image files with .jpg, .jpeg, and .png extensions
    images = [f for f in os.listdir(IMAGE_FOLDER) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
    
    # Select two random images
    selected = random.sample(images, 2)

    actors = []
    for image in selected:
        name = os.path.splitext(image)[0]  # Get the name without the file extension
        actors.append({
            'name': name,
            'image': image
        })

    return render_template('index.html', actors=actors)

@app.route('/vote/<actor_name>', methods=['POST'])
def vote(actor_name):
    # Store the vote in the text file
    with open(VOTE_FILE, 'a') as file:
        file.write(f"{actor_name}\n")
    return redirect('/')
@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if 'admin' not in session:
        return redirect(url_for('login'))  # Redirect to login page if not logged in

    votes = get_votes()
    images = sorted(os.listdir(IMAGE_FOLDER))

    if request.method == 'POST':
        action = request.form.get('action')
        actor_name = request.form.get('actor_name')

        if action == 'delete':
            # Delete image file and associated vote
            for ext in ['.jpg', '.jpeg', '.png']:
                image_path = os.path.join(IMAGE_FOLDER, actor_name + ext)
                if os.path.exists(image_path):
                    os.remove(image_path)
                    break
            flash(f"Actor {actor_name} deleted successfully!", "success")
            return redirect(url_for('admin'))

        if action == 'edit':
            new_name = request.form.get('new_name')
            # Rename the image file
            for ext in ['.jpg', '.jpeg', '.png']:
                old_path = os.path.join(IMAGE_FOLDER, actor_name + ext)
                if os.path.exists(old_path):
                    new_path = os.path.join(IMAGE_FOLDER, new_name + ext)
                    os.rename(old_path, new_path)
                    flash(f"Actor {actor_name} renamed to {new_name} successfully!", "success")
                    break
            return redirect(url_for('admin'))

        if action == 'replace_image':
            new_image = request.files.get('new_image')
            if new_image:
                new_image_filename = actor_name + os.path.splitext(new_image.filename)[1]
                new_image.save(os.path.join(IMAGE_FOLDER, new_image_filename))
                flash(f"Actor {actor_name} image replaced successfully!", "success")
            return redirect(url_for('admin'))

    return render_template('admin.html', votes=votes, images=images)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['admin'] = True
            return redirect(url_for('admin'))
        else:
            flash('Invalid credentials. Please try again.', 'danger')

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('admin', None)  # Logout by removing the session
    return redirect(url_for('login'))

if __name__ == '__main__':
    visit_db()
    app.run(debug=True)
