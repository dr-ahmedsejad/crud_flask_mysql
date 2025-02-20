import os

from flask import Flask, request, jsonify, render_template, redirect, url_for
from flask_mysqldb import MySQL
from flask_cors import CORS
from werkzeug.utils import secure_filename

app = Flask(__name__)
CORS(app)  # Autorise toutes les origines

# Configuration de la base de données
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'flask_crud'

mysql = MySQL(app)

# Configuration pour le téléchargement des fichiers
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Route : Liste des items avec jointure sur la table des catégories
@app.route('/')
def index():
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT items.id, items.name, items.description, items.image_path, items.category_id, categories.nom AS category_nom
        FROM items, categories
        where items.category_id = categories.id
    """)
    items = cur.fetchall()
    cur.close()
    return render_template('index.html', items=items)

# Route : Créer un nouvel item
@app.route('/create', methods=['GET', 'POST'])
def create():
    # Récupérer toutes les catégories pour le formulaire
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM categories")
    categories = cur.fetchall()
    cur.close()

    if request.method == 'POST':
        nom = request.form['name']
        description = request.form['description']
        category_id = request.form['category_id']  # Valeur de la catégorie sélectionnée
        file = request.files['image']

        image_path = None
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            image_path = f"{UPLOAD_FOLDER}/{filename}"

        cur = mysql.connection.cursor()
        cur.execute("""
            INSERT INTO items (name, description, image_path, category_id) 
            VALUES (%s, %s, %s, %s)
        """, (nom, description, image_path, category_id))
        mysql.connection.commit()
        cur.close()
        return redirect(url_for('index'))

    return render_template('create.html', categories=categories)

# Route : Mettre à jour un item existant
@app.route('/update/<int:id>', methods=['GET', 'POST'])
def update(id):
    cur = mysql.connection.cursor()
    # Récupérer toutes les catégories pour le formulaire
    cur.execute("SELECT * FROM categories")
    categories = cur.fetchall()

    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        category_id = request.form['category_id']
        file = request.files['image']

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            image_path = f"{UPLOAD_FOLDER}/{filename}"
            cur.execute("""
                UPDATE items 
                SET name = %s, description = %s, image_path = %s, category_id = %s 
                WHERE id = %s
            """, (name, description, image_path, category_id, id))
        else:
            cur.execute("""
                UPDATE items 
                SET name = %s, description = %s, category_id = %s 
                WHERE id = %s
            """, (name, description, category_id, id))

        mysql.connection.commit()
        cur.close()
        return redirect(url_for('index'))

    cur.execute("SELECT id, name, description, image_path, category_id FROM items WHERE id = %s", (id,))
    item = cur.fetchone()
    cur.close()

    return render_template('update.html', item=item, categories=categories)

# Route : Supprimer un item
@app.route('/delete/<int:id>', methods=['POST'])
def delete(id):
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM items WHERE id = %s", (id,))
    mysql.connection.commit()
    cur.close()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000,debug=True)
