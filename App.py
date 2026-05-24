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
    
    # Stats
    total_products = db.execute('SELECT COUNT(*) FROM products').fetchone()[0]
    total_vendors = db.execute('SELECT COUNT(*) FROM vendors').fetchone()[0]
    total_customers = db.execute('SELECT COUNT(*) FROM customers').fetchone()[0]
    
    # Low stock products (stock 10 se kam)
    low_stock = db.execute(
        'SELECT * FROM products WHERE stock_qty <=10'
    ).fetchall()
    
    db.close()
    
    return render_template('index.html',
        total_products=total_products,
        total_vendors=total_vendors,
        total_customers=total_customers,
        low_stock=low_stock
    )

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
        gst_percent = request.form.get('gst_percent', 0)
        purchase_price = request.form.get('purchase_price', 0)

        if not name or not sku or not unit_price:
            flash("Name, SKU aur Price zaroori hain!", "danger")
            return redirect(url_for('products_add'))

        try:
            db = get_db()
            db.execute(
                 'INSERT INTO products (name, sku, unit_price, stock_qty, description, gst_percent) VALUES (?, ?, ?, ?, ?, ?)',
                (name, sku, float(unit_price), int(stock_qty or 0), description, float(gst_percent))
            )
            db.commit()
            db.close()
            flash("Product add ho gaya!", "success")
            return redirect(url_for('products_list'))
        except Exception as e:
            flash("Error: SKU already exist karta hai ya kuch galat hua!", "danger")
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
        gst_percent = request.form.get('gst_percent', 0)
        purchase_price = request.form.get('purchase_price', 0)

        db.execute(
            'UPDATE products SET name=?, sku=?, purchase_price=?, unit_price=?, stock_qty=?, description=?, gst_percent=? WHERE id=?',
            (name, sku, float(purchase_price), float(unit_price), int(stock_qty or 0), description, float(gst_percent), id)
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

# ─── VENDORS ────────────────────────────────────────
@app.route('/vendors')
def vendors_list():
    db = get_db()
    vendors = db.execute('SELECT * FROM vendors').fetchall()
    db.close()
    return render_template('vendors/list.html', vendors=vendors)

@app.route('/vendors/add', methods=['GET', 'POST'])
def vendors_add():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        phone = request.form['phone']
        address = request.form['address']

        if not name:
            flash("Vendor name zaroori hai!", "danger")
            return redirect(url_for('vendors_add'))

        db = get_db()
        db.execute(
            'INSERT INTO vendors (name, email, phone, address) VALUES (?, ?, ?, ?)',
            (name, email, phone, address)
        )
        db.commit()
        db.close()
        flash("Vendor add ho gaya!", "success")
        return redirect(url_for('vendors_list'))

    return render_template('vendors/form.html', vendor=None)

@app.route('/vendors/edit/<int:id>', methods=['GET', 'POST'])
def vendors_edit(id):
    db = get_db()
    vendor = db.execute('SELECT * FROM vendors WHERE id = ?', (id,)).fetchone()

    if not vendor:
        flash("Vendor nahi mila!", "danger")
        return redirect(url_for('vendors_list'))

    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        phone = request.form['phone']
        address = request.form['address']

        db.execute(
            'UPDATE vendors SET name=?, email=?, phone=?, address=? WHERE id=?',
            (name, email, phone, address, id)
        )
        db.commit()
        db.close()
        flash("Vendor update ho gaya!", "success")
        return redirect(url_for('vendors_list'))

    db.close()
    return render_template('vendors/form.html', vendor=vendor)

@app.route('/vendors/delete/<int:id>')
def vendors_delete(id):
    db = get_db()
    db.execute('DELETE FROM vendors WHERE id = ?', (id,))
    db.commit()
    db.close()
    flash("Vendor delete ho gaya!", "success")
    return redirect(url_for('vendors_list'))

# ─── CUSTOMERS ──────────────────────────────────────
@app.route('/customers')
def customers_list():
    db = get_db()
    customers = db.execute('SELECT * FROM customers').fetchall()
    db.close()
    return render_template('customers/list.html', customers=customers)

@app.route('/customers/add', methods=['GET', 'POST'])
def customers_add():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        phone = request.form['phone']
        address = request.form['address']

        if not name:
            flash("Customer name zaroori hai!", "danger")
            return redirect(url_for('customers_add'))

        db = get_db()
        db.execute(
            'INSERT INTO customers (name, email, phone, address) VALUES (?, ?, ?, ?)',
            (name, email, phone, address)
        )
        db.commit()
        db.close()
        flash("Customer add ho gaya!", "success")
        return redirect(url_for('customers_list'))

    return render_template('customers/form.html', customer=None)

@app.route('/customers/edit/<int:id>', methods=['GET', 'POST'])
def customers_edit(id):
    db = get_db()
    customer = db.execute('SELECT * FROM customers WHERE id = ?', (id,)).fetchone()

    if not customer:
        flash("Customer nahi mila!", "danger")
        return redirect(url_for('customers_list'))

    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        phone = request.form['phone']
        address = request.form['address']

        db.execute(
            'UPDATE customers SET name=?, email=?, phone=?, address=? WHERE id=?',
            (name, email, phone, address, id)
        )
        db.commit()
        db.close()
        flash("Customer update ho gaya!", "success")
        return redirect(url_for('customers_list'))

    db.close()
    return render_template('customers/form.html', customer=customer)

@app.route('/customers/delete/<int:id>')
def customers_delete(id):
    db = get_db()
    db.execute('DELETE FROM customers WHERE id = ?', (id,))
    db.commit()
    db.close()
    flash("Customer delete ho gaya!", "success")
    return redirect(url_for('customers_list'))

# ─── ORDERS ─────────────────────────────────────────
@app.route('/orders')
def orders_list():
    db = get_db()
    orders = db.execute('''
        SELECT orders.*, customers.name as customer_name
        FROM orders
        JOIN customers ON orders.customer_id = customers.id
        ORDER BY orders.created_at DESC
    ''').fetchall()
    db.close()
    return render_template('orders/list.html', orders=orders)

@app.route('/orders/add', methods=['GET', 'POST'])
def orders_add():
    db = get_db()
    if request.method == 'POST':
        customer_id = request.form['customer_id']
        product_ids = request.form.getlist('product_id[]')
        quantities = request.form.getlist('quantity[]')

        if not customer_id:
            flash("Customer select karo!", "danger")
            return redirect(url_for('orders_add'))

        # Order banao
        db.execute(
            'INSERT INTO orders (customer_id, status, total_amount) VALUES (?, ?, ?)',
            (customer_id, 'pending', 0)
        )
        db.commit()
        order_id = db.execute('SELECT last_insert_rowid()').fetchone()[0]

        # Order items add karo
        total = 0
        for pid, qty in zip(product_ids, quantities):
            if pid and qty:
                product = db.execute(
                    'SELECT * FROM products WHERE id = ?', (pid,)
                ).fetchone()
                if product:
                    subtotal = product['unit_price'] * int(qty)
                    total += subtotal
                    db.execute(
                        'INSERT INTO order_items (order_id, product_id, quantity, unit_price) VALUES (?, ?, ?, ?)',
                        (order_id, pid, int(qty), product['unit_price'])
                    )

        # Total update karo
        db.execute('UPDATE orders SET total_amount = ? WHERE id = ?', (total, order_id))
        db.commit()
        db.close()

        flash("Order create ho gaya!", "success")
        return redirect(url_for('orders_list'))

    customers = db.execute('SELECT * FROM customers').fetchall()
    products = db.execute('SELECT * FROM products WHERE stock_qty > 0').fetchall()
    db.close()
    return render_template('orders/form.html', customers=customers, products=products)

@app.route('/orders/<int:id>')
def orders_detail(id):
    db = get_db()
    order = db.execute('''
        SELECT orders.*, customers.name as customer_name
        FROM orders
        JOIN customers ON orders.customer_id = customers.id
        WHERE orders.id = ?
    ''', (id,)).fetchone()

    if not order:
        flash("Order nahi mila!", "danger")
        return redirect(url_for('orders_list'))

    items = db.execute('''
        SELECT order_items.*, products.name as product_name
        FROM order_items
        JOIN products ON order_items.product_id = products.id
        WHERE order_items.order_id = ?
    ''', (id,)).fetchall()
    db.close()
    return render_template('orders/detail.html', order=order, items=items)

@app.route('/orders/confirm/<int:id>')
def orders_confirm(id):
    db = get_db()
    order = db.execute('SELECT * FROM orders WHERE id = ?', (id,)).fetchone()

    if not order:
        flash("Order nahi mila!", "danger")
        return redirect(url_for('orders_list'))

    if order['status'] != 'pending':
        flash("Yeh order already confirm ho chuka hai!", "warning")
        return redirect(url_for('orders_detail', id=id))

    # Stock deduct karo
    items = db.execute(
        'SELECT * FROM order_items WHERE order_id = ?', (id,)
    ).fetchall()

    for item in items:
        db.execute(
            'UPDATE products SET stock_qty = stock_qty - ? WHERE id = ?',
            (item['quantity'], item['product_id'])
        )

    # Order status update karo
    db.execute(
        'UPDATE orders SET status = ? WHERE id = ?',
        ('confirmed', id)
    )

    # Invoice automatically generate karo
    order = db.execute('SELECT * FROM orders WHERE id = ?', (id,)).fetchone()
    
    # Subtotal aur GST calculate karo
    subtotal = 0
    gst_amount = 0
    for item in items:
        product = db.execute('SELECT * FROM products WHERE id = ?', (item['product_id'],)).fetchone()
        item_subtotal = item['unit_price'] * item['quantity']
        item_gst = item_subtotal * (product['gst_percent'] / 100)
        subtotal += item_subtotal
        gst_amount += item_gst

    total_amount = subtotal + gst_amount

    # Invoice banao
    db.execute('''
        INSERT INTO invoices (order_id, customer_id, status, subtotal, gst_amount, total_amount)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (id, order['customer_id'], 'pending', subtotal, gst_amount, total_amount))
    
    db.commit()
    db.close()

    flash("Order confirm ho gaya! Stock update ho gaya!", "success")
    return redirect(url_for('orders_detail', id=id))

@app.route('/orders/delete/<int:id>')
def orders_delete(id):
    db = get_db()
    db.execute('DELETE FROM order_items WHERE order_id = ?', (id,))
    db.execute('DELETE FROM orders WHERE id = ?', (id,))
    db.commit()
    db.close()
    flash("Order delete ho gaya!", "success")
    return redirect(url_for('orders_list'))

# ─── PURCHASE ORDERS ────────────────────────────────
@app.route('/purchase-orders')
def po_list():
    db = get_db()
    purchase_orders = db.execute('''
        SELECT purchase_orders.*, vendors.name as vendor_name
        FROM purchase_orders
        JOIN vendors ON purchase_orders.vendor_id = vendors.id
        ORDER BY purchase_orders.created_at DESC
    ''').fetchall()
    db.close()
    return render_template('purchase_orders/list.html', purchase_orders=purchase_orders)

@app.route('/purchase-orders/add', methods=['GET', 'POST'])
def po_add():
    db = get_db()
    if request.method == 'POST':
        vendor_id = request.form['vendor_id']
        product_ids = request.form.getlist('product_id[]')
        quantities = request.form.getlist('quantity[]')
        purchase_prices = request.form.getlist('purchase_price[]')
        gst_percents = request.form.getlist('gst_percent[]')

        if not vendor_id:
            flash("Vendor select karo!", "danger")
            return redirect(url_for('po_add'))

        # PO banao
        db.execute(
            'INSERT INTO purchase_orders (vendor_id, status, total_amount) VALUES (?, ?, ?)',
            (vendor_id, 'pending', 0)
        )
        db.commit()
        po_id = db.execute('SELECT last_insert_rowid()').fetchone()[0]

        # PO items add karo
        total = 0
        for pid, qty, price, gst in zip(product_ids, quantities, purchase_prices, gst_percents):
            if pid and qty and price:
                qty = int(qty)
                price = float(price)
                gst = float(gst or 0)
                gst_amount = price * qty * gst / 100
                subtotal = price * qty + gst_amount
                total += subtotal
                db.execute(
                    'INSERT INTO purchase_order_items (po_id, product_id, quantity, unit_price, gst_percent) VALUES (?, ?, ?, ?, ?)',
                    (po_id, pid, qty, price, gst)
                )

        # Total update karo
        db.execute('UPDATE purchase_orders SET total_amount = ? WHERE id = ?', (total, po_id))
        db.commit()
        db.close()

        flash("Purchase Order create ho gaya!", "success")
        return redirect(url_for('po_list'))

    vendors = db.execute('SELECT * FROM vendors').fetchall()
    products = db.execute('SELECT * FROM products').fetchall()
    db.close()
    return render_template('purchase_orders/form.html', vendors=vendors, products=products)

@app.route('/purchase-orders/<int:id>')
def po_detail(id):
    db = get_db()
    po = db.execute('''
        SELECT purchase_orders.*, vendors.name as vendor_name
        FROM purchase_orders
        JOIN vendors ON purchase_orders.vendor_id = vendors.id
        WHERE purchase_orders.id = ?
    ''', (id,)).fetchone()

    if not po:
        flash("Purchase Order nahi mila!", "danger")
        return redirect(url_for('po_list'))

    items = db.execute('''
        SELECT purchase_order_items.*, products.name as product_name
        FROM purchase_order_items
        JOIN products ON purchase_order_items.product_id = products.id
        WHERE purchase_order_items.po_id = ?
    ''', (id,)).fetchall()
    db.close()
    return render_template('purchase_orders/detail.html', po=po, items=items)

@app.route('/purchase-orders/receive/<int:id>')
def po_receive(id):
    db = get_db()
    po = db.execute('SELECT * FROM purchase_orders WHERE id = ?', (id,)).fetchone()

    if not po:
        flash("Purchase Order nahi mila!", "danger")
        return redirect(url_for('po_list'))

    if po['status'] != 'pending':
        flash("Yeh PO already receive ho chuka hai!", "warning")
        return redirect(url_for('po_detail', id=id))

    # Stock update karo
    items = db.execute(
        'SELECT * FROM purchase_order_items WHERE po_id = ?', (id,)
    ).fetchall()

    for item in items:
        db.execute(
            'UPDATE products SET stock_qty = stock_qty + ? WHERE id = ?',
            (item['quantity'], item['product_id'])
        )

    # PO status update karo
    db.execute(
        'UPDATE purchase_orders SET status = ? WHERE id = ?',
        ('received', id)
    )
    db.commit()
    db.close()

    flash("Stock receive ho gaya! Inventory update ho gayi!", "success")
    return redirect(url_for('po_detail', id=id))

@app.route('/purchase-orders/delete/<int:id>')
def po_delete(id):
    db = get_db()
    db.execute('DELETE FROM purchase_order_items WHERE po_id = ?', (id,))
    db.execute('DELETE FROM purchase_orders WHERE id = ?', (id,))
    db.commit()
    db.close()
    flash("Purchase Order delete ho gaya!", "success")
    return redirect(url_for('po_list'))

# ─── INVOICES ───────────────────────────────────────
@app.route('/invoices')
def invoices_list():
    db = get_db()
    invoices = db.execute('''
        SELECT invoices.*, customers.name as customer_name
        FROM invoices
        JOIN customers ON invoices.customer_id = customers.id
        ORDER BY invoices.created_at DESC
    ''').fetchall()
    db.close()
    return render_template('invoices/list.html', invoices=invoices)

@app.route('/invoices/<int:id>')
def invoices_detail(id):
    db = get_db()
    invoice = db.execute('''
        SELECT invoices.*, 
               customers.name as customer_name,
               customers.email as customer_email,
               customers.phone as customer_phone,
               customers.address as customer_address
        FROM invoices
        JOIN customers ON invoices.customer_id = customers.id
        WHERE invoices.id = ?
    ''', (id,)).fetchone()

    if not invoice:
        flash("Invoice nahi mila!", "danger")
        return redirect(url_for('invoices_list'))

    items = db.execute('''
        SELECT order_items.*, 
               products.name as product_name,
               products.gst_percent as gst_percent
        FROM order_items
        JOIN products ON order_items.product_id = products.id
        WHERE order_items.order_id = ?
    ''', (invoice['order_id'],)).fetchall()
    db.close()
    return render_template('invoices/detail.html', invoice=invoice, items=items)

@app.route('/invoices/mark-paid/<int:id>')
def invoices_mark_paid(id):
    db = get_db()
    db.execute('UPDATE invoices SET status = ? WHERE id = ?', ('paid', id))
    db.commit()
    db.close()
    flash("Invoice paid mark ho gaya!", "success")
    return redirect(url_for('invoices_detail', id=id))

@app.route('/invoices/<int:id>/print')
def invoices_print(id):
    db = get_db()
    invoice = db.execute('''
        SELECT invoices.*,
               customers.name as customer_name,
               customers.email as customer_email,
               customers.phone as customer_phone,
               customers.address as customer_address
        FROM invoices
        JOIN customers ON invoices.customer_id = customers.id
        WHERE invoices.id = ?
    ''', (id,)).fetchone()

    items = db.execute('''
        SELECT order_items.*,
               products.name as product_name,
               products.gst_percent as gst_percent
        FROM order_items
        JOIN products ON order_items.product_id = products.id
        WHERE order_items.order_id = ?
    ''', (invoice['order_id'],)).fetchall()

    company = db.execute('SELECT * FROM settings WHERE id = 1').fetchone()
    db.close()
    return render_template('invoices/print.html', invoice=invoice, items=items, company=company)


# ─── SETTINGS ───────────────────────────────────────
@app.route('/settings', methods=['GET', 'POST'])
def settings():
    db = get_db()
    if request.method == 'POST':
        company_name = request.form['company_name']
        company_email = request.form['company_email']
        company_phone = request.form['company_phone']
        company_address = request.form['company_address']
        gstin = request.form['gstin']
        invoice_prefix = request.form['invoice_prefix']

        # Logo upload handle karo
        logo_filename = db.execute('SELECT logo_filename FROM settings WHERE id = 1').fetchone()['logo_filename']
        
        if 'logo' in request.files:
            logo = request.files['logo']
            if logo.filename != '':
                import os
                logo_filename = 'company_logo.' + logo.filename.rsplit('.', 1)[1].lower()
                logo.save(os.path.join('static', logo_filename))

        db.execute('''
            UPDATE settings SET 
                company_name=?, company_email=?, company_phone=?,
                company_address=?, gstin=?, invoice_prefix=?, logo_filename=?
            WHERE id=1
        ''', (company_name, company_email, company_phone,
              company_address, gstin, invoice_prefix, logo_filename))
        db.commit()
        db.close()
        flash("Settings save ho gayi!", "success")
        return redirect(url_for('settings'))

    settings = db.execute('SELECT * FROM settings WHERE id = 1').fetchone()
    db.close()
    return render_template('settings.html', settings=settings)


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