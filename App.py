# app.py
from flask import Flask, render_template, request, redirect, url_for, flash
from database import get_db, init_db

app = Flask(__name__)
app.secret_key = 'flowforge-secret-123'

with app.app_context():
    init_db()

# ─── HOME ───────────────────────────────────────────
@app.route('/')
def index():
    db = get_db()
    notes = db.execute('SELECT * FROM notes').fetchall()
    db.close()
    return render_template('index.html', builder="Abhi", notes=notes)

# ─── NOTES ──────────────────────────────────────────
@app.route('/notes/add', methods=['GET', 'POST'])
def add_note():
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']

        if not title or not content:
            flash("Title aur content dono bharo!", "danger")
            return redirect(url_for('add_note'))

        db = get_db()
        db.execute('INSERT INTO notes (title, content) VALUES (?, ?)',
                   (title, content))
        db.commit()
        db.close()

        flash("Note save ho gaya!", "success")
        return redirect(url_for('index'))

    return render_template('add_note.html')

# ─── PRODUCTS ───────────────────────────────────────
@app.route('/products')
def products_list():
    db = get_db()
    products = db.execute('SELECT * FROM products').fetchall()
    db.close()
    return render_template('products/list.html', products=products)

@app.route('/products/add', methods=['GET', 'POST'])
def products_add():
    if request.method == 'POST':
        name = request.form['name']
        sku = request.form['sku']
        unit_price = request.form['unit_price']
        stock_qty = request.form['stock_qty']
        description = request.form['description']

        if not name or not sku or not unit_price:
            flash("Name, SKU aur Price zaroori hain!", "danger")
            return redirect(url_for('products_add'))

        try:
            db = get_db()
            db.execute(
                'INSERT INTO products (name, sku, unit_price, stock_qty, description) VALUES (?, ?, ?, ?, ?)',
                (name, sku, float(unit_price), int(stock_qty or 0), description)
            )
            db.commit()
            db.close()
            flash("Product add ho gaya!", "success")
            return redirect(url_for('products_list'))
        except Exception as e:
            flash(f"Error: SKU already exist karta hai ya kuch galat hua!", "danger")
            return redirect(url_for('products_add'))

    return render_template('products/form.html', product=None)

@app.route('/products/edit/<int:id>', methods=['GET', 'POST'])
def products_edit(id):
    db = get_db()
    product = db.execute('SELECT * FROM products WHERE id = ?', (id,)).fetchone()

    if not product:
        flash("Product nahi mila!", "danger")
        return redirect(url_for('products_list'))

    if request.method == 'POST':
        name = request.form['name']
        sku = request.form['sku']
        unit_price = request.form['unit_price']
        stock_qty = request.form['stock_qty']
        description = request.form['description']

        db.execute(
            'UPDATE products SET name=?, sku=?, unit_price=?, stock_qty=?, description=? WHERE id=?',
            (name, sku, float(unit_price), int(stock_qty or 0), description, id)
        )
        db.commit()
        db.close()
        flash("Product update ho gaya!", "success")
        return redirect(url_for('products_list'))

    db.close()
    return render_template('products/form.html', product=product)

@app.route('/products/delete/<int:id>')
def products_delete(id):
    db = get_db()
    db.execute('DELETE FROM products WHERE id = ?', (id,))
    db.commit()
    db.close()
    flash("Product delete ho gaya!", "success")
    return redirect(url_for('products_list'))

# ─── ABOUT ──────────────────────────────────────────
@app.route('/about')
def about():
    tech_stack = [
        "Python 3 + Flask",
        "SQLite database",
        "Jinja2 templates",
        "HTML + CSS"
    ]
    return render_template('about.html', tech_stack=tech_stack)

if __name__ == '__main__':
    app.run(debug=True)