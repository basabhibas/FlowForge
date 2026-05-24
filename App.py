# app.py
import os
from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from database import get_db, init_db, close_db

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'flowforge-secret-123')

# Register the database teardown so the connection is closed cleanly
# at the end of every request, even if an exception occurred.
app.teardown_appcontext(close_db)

with app.app_context():
    init_db()
    # Ensure a default admin user exists (username: admin / password: admin)
    db = get_db()
    cur = db.execute('SELECT COUNT(*) FROM users').fetchone()
    if cur is None or cur[0] == 0:
        pw_hash = generate_password_hash('admin')
        try:
            db.execute(
                'INSERT INTO users (username, business_name, password_hash) VALUES (?, ?, ?)',
                ('admin', 'FlowForge Admin', pw_hash)
            )
            db.commit()
            app.logger.info('Created default admin user (username: admin)')
        except Exception:
            pass


# ─── HOME ───────────────────────────────────────────
@app.route('/')
def index():
    db = get_db()

    total_products   = db.execute('SELECT COUNT(*) FROM products').fetchone()[0]
    total_vendors    = db.execute('SELECT COUNT(*) FROM vendors').fetchone()[0]
    total_customers  = db.execute('SELECT COUNT(*) FROM customers').fetchone()[0]
    total_orders     = db.execute('SELECT COUNT(*) FROM orders').fetchone()[0]
    pending_orders   = db.execute("SELECT COUNT(*) FROM orders WHERE status = 'pending'").fetchone()[0]
    total_revenue    = db.execute("SELECT COALESCE(SUM(total_amount), 0) FROM orders WHERE status = 'confirmed'").fetchone()[0]
    paid_invoices    = db.execute("SELECT COUNT(*) FROM invoices WHERE status = 'paid'").fetchone()[0]
    pending_invoices = db.execute("SELECT COUNT(*) FROM invoices WHERE status = 'pending'").fetchone()[0]

    # Dynamic low-stock: each product defines its own min_stock threshold
    low_stock = db.execute(
        'SELECT * FROM products WHERE stock_qty <= min_stock'
    ).fetchall()

    monthly = db.execute('''
        SELECT strftime('%Y-%m', created_at) as month,
               SUM(total_amount) as revenue
        FROM orders
        WHERE status = 'confirmed'
        GROUP BY month
        ORDER BY month DESC
        LIMIT 6
    ''').fetchall()
    monthly_labels = [row['month'] for row in reversed(monthly)]
    monthly_data   = [row['revenue'] for row in reversed(monthly)]

    top_products = db.execute('''
        SELECT products.name,
               SUM(order_items.quantity) as total_qty,
               SUM(order_items.quantity * order_items.unit_price) as total_revenue
        FROM order_items
        JOIN products ON order_items.product_id = products.id
        JOIN orders   ON order_items.order_id   = orders.id
        WHERE orders.status = 'confirmed'
        GROUP BY products.id
        ORDER BY total_revenue DESC
        LIMIT 5
    ''').fetchall()
    product_labels = [p['name'] for p in top_products]
    product_data   = [p['total_revenue'] for p in top_products]

    return render_template('index.html',
        total_products=total_products,
        total_vendors=total_vendors,
        total_customers=total_customers,
        total_orders=total_orders,
        pending_orders=pending_orders,
        total_revenue=total_revenue,
        paid_invoices=paid_invoices,
        pending_invoices=pending_invoices,
        low_stock=low_stock,
        monthly_labels=monthly_labels,
        monthly_data=monthly_data,
        top_products=top_products,
        product_labels=product_labels,
        product_data=product_data,
    )



# ─── PRODUCTS ───────────────────────────────────────
@app.route('/products')
def products_list():
    db = get_db()
    products = db.execute('SELECT * FROM products').fetchall()
    return render_template('products/list.html', products=products)


@app.route('/products/add', methods=['GET', 'POST'])
def products_add():
    if request.method == 'POST':
        name           = request.form['name']
        sku            = request.form['sku']
        unit_price     = request.form['unit_price']
        stock_qty      = request.form['stock_qty']
        description    = request.form['description']
        gst_percent    = request.form.get('gst_percent', 0)
        purchase_price = request.form.get('purchase_price', 0)
        min_stock      = request.form.get('min_stock', 10)

        if not name or not sku or not unit_price:
            flash("Name, SKU aur Price zaroori hain!", "danger")
            return redirect(url_for('products_add'))

        try:
            db = get_db()
            db.execute(
                '''INSERT INTO products
                   (name, sku, purchase_price, unit_price, stock_qty, description, gst_percent, min_stock)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                (name, sku, float(purchase_price), float(unit_price),
                 int(stock_qty or 0), description, float(gst_percent), int(min_stock or 10))
            )
            db.commit()
            flash("Product add ho gaya!", "success")
            return redirect(url_for('products_list'))
        except Exception:
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
        name           = request.form['name']
        sku            = request.form['sku']
        unit_price     = request.form['unit_price']
        stock_qty      = request.form['stock_qty']
        description    = request.form['description']
        gst_percent    = request.form.get('gst_percent', 0)
        purchase_price = request.form.get('purchase_price', 0)
        min_stock      = request.form.get('min_stock', 10)

        db.execute(
            '''UPDATE products
               SET name=?, sku=?, purchase_price=?, unit_price=?,
                   stock_qty=?, description=?, gst_percent=?, min_stock=?
               WHERE id=?''',
            (name, sku, float(purchase_price), float(unit_price),
             int(stock_qty or 0), description, float(gst_percent),
             int(min_stock or 10), id)
        )
        db.commit()
        flash("Product update ho gaya!", "success")
        return redirect(url_for('products_list'))

    return render_template('products/form.html', product=product)


@app.route('/products/delete/<int:id>')
def products_delete(id):
    db = get_db()
    db.execute('DELETE FROM products WHERE id = ?', (id,))
    db.commit()
    flash("Product delete ho gaya!", "success")
    return redirect(url_for('products_list'))


# ─── VENDORS ────────────────────────────────────────
@app.route('/vendors')
def vendors_list():
    db = get_db()
    vendors = db.execute('SELECT * FROM vendors').fetchall()
    return render_template('vendors/list.html', vendors=vendors)


@app.route('/vendors/add', methods=['GET', 'POST'])
def vendors_add():
    if request.method == 'POST':
        name    = request.form['name']
        email   = request.form['email']
        phone   = request.form['phone']
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
        name    = request.form['name']
        email   = request.form['email']
        phone   = request.form['phone']
        address = request.form['address']

        db.execute(
            'UPDATE vendors SET name=?, email=?, phone=?, address=? WHERE id=?',
            (name, email, phone, address, id)
        )
        db.commit()
        flash("Vendor update ho gaya!", "success")
        return redirect(url_for('vendors_list'))

    return render_template('vendors/form.html', vendor=vendor)


@app.route('/vendors/delete/<int:id>')
def vendors_delete(id):
    db = get_db()
    db.execute('DELETE FROM vendors WHERE id = ?', (id,))
    db.commit()
    flash("Vendor delete ho gaya!", "success")
    return redirect(url_for('vendors_list'))


# ─── CUSTOMERS ──────────────────────────────────────
@app.route('/customers')
def customers_list():
    db = get_db()
    customers = db.execute('SELECT * FROM customers').fetchall()
    return render_template('customers/list.html', customers=customers)


@app.route('/customers/add', methods=['GET', 'POST'])
def customers_add():
    if request.method == 'POST':
        name    = request.form['name']
        email   = request.form['email']
        phone   = request.form['phone']
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
        name    = request.form['name']
        email   = request.form['email']
        phone   = request.form['phone']
        address = request.form['address']

        db.execute(
            'UPDATE customers SET name=?, email=?, phone=?, address=? WHERE id=?',
            (name, email, phone, address, id)
        )
        db.commit()
        flash("Customer update ho gaya!", "success")
        return redirect(url_for('customers_list'))

    return render_template('customers/form.html', customer=customer)


@app.route('/customers/delete/<int:id>')
def customers_delete(id):
    db = get_db()
    db.execute('DELETE FROM customers WHERE id = ?', (id,))
    db.commit()
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
    return render_template('orders/list.html', orders=orders)


@app.route('/orders/add', methods=['GET', 'POST'])
def orders_add():
    db = get_db()
    if request.method == 'POST':
        customer_id  = request.form['customer_id']
        product_ids  = request.form.getlist('product_id[]')
        quantities   = request.form.getlist('quantity[]')

        if not customer_id:
            flash("Customer select karo!", "danger")
            return redirect(url_for('orders_add'))

        try:
            # ── Transaction: create order + line items atomically ──
            db.execute('BEGIN')

            db.execute(
                'INSERT INTO orders (customer_id, status, total_amount) VALUES (?, ?, ?)',
                (customer_id, 'pending', 0)
            )
            order_id = db.execute('SELECT last_insert_rowid()').fetchone()[0]

            total = 0
            for pid, qty in zip(product_ids, quantities):
                if pid and qty:
                    product = db.execute(
                        'SELECT * FROM products WHERE id = ?', (pid,)
                    ).fetchone()
                    if product:
                        subtotal = product['unit_price'] * int(qty)
                        total   += subtotal
                        db.execute(
                            'INSERT INTO order_items (order_id, product_id, quantity, unit_price) VALUES (?, ?, ?, ?)',
                            (order_id, pid, int(qty), product['unit_price'])
                        )

            db.execute('UPDATE orders SET total_amount = ? WHERE id = ?', (total, order_id))
            db.commit()
            flash("Order create ho gaya!", "success")
            return redirect(url_for('orders_list'))

        except Exception as e:
            db.rollback()
            flash(f"Order create karne mein error aaya: {e}", "danger")
            return redirect(url_for('orders_add'))

    customers = db.execute('SELECT * FROM customers').fetchall()
    products  = db.execute('SELECT * FROM products WHERE stock_qty > 0').fetchall()
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

    items = db.execute(
        'SELECT * FROM order_items WHERE order_id = ?', (id,)
    ).fetchall()

    try:
        # ── Transaction: deduct stock + update order + create invoice ──
        db.execute('BEGIN')

        subtotal   = 0
        gst_amount = 0

        for item in items:
            product = db.execute(
                'SELECT * FROM products WHERE id = ?', (item['product_id'],)
            ).fetchone()

            # Guard: ensure stock doesn't go negative
            if product['stock_qty'] < item['quantity']:
                raise ValueError(
                    f"'{product['name']}' ka stock kam hai! "
                    f"(Available: {product['stock_qty']}, Required: {item['quantity']})"
                )

            db.execute(
                'UPDATE products SET stock_qty = stock_qty - ? WHERE id = ?',
                (item['quantity'], item['product_id'])
            )

            item_subtotal  = item['unit_price'] * item['quantity']
            item_gst       = item_subtotal * (product['gst_percent'] / 100)
            subtotal      += item_subtotal
            gst_amount    += item_gst

        total_amount = subtotal + gst_amount

        db.execute(
            'UPDATE orders SET status = ? WHERE id = ?', ('confirmed', id)
        )

        db.execute('''
            INSERT INTO invoices (order_id, customer_id, status, subtotal, gst_amount, total_amount)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (id, order['customer_id'], 'pending', subtotal, gst_amount, total_amount))

        db.commit()
        flash("Order confirm ho gaya! Stock update ho gaya!", "success")

    except ValueError as ve:
        db.rollback()
        flash(str(ve), "danger")
    except Exception as e:
        db.rollback()
        flash(f"Confirm karne mein error aaya: {e}", "danger")

    return redirect(url_for('orders_detail', id=id))


@app.route('/orders/delete/<int:id>')
def orders_delete(id):
    db = get_db()
    try:
        db.execute('BEGIN')
        db.execute('DELETE FROM order_items WHERE order_id = ?', (id,))
        db.execute('DELETE FROM orders WHERE id = ?', (id,))
        db.commit()
        flash("Order delete ho gaya!", "success")
    except Exception as e:
        db.rollback()
        flash(f"Delete karne mein error aaya: {e}", "danger")
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
    return render_template('purchase_orders/list.html', purchase_orders=purchase_orders)


@app.route('/purchase-orders/add', methods=['GET', 'POST'])
def po_add():
    db = get_db()
    if request.method == 'POST':
        vendor_id       = request.form['vendor_id']
        product_ids     = request.form.getlist('product_id[]')
        quantities      = request.form.getlist('quantity[]')
        purchase_prices = request.form.getlist('purchase_price[]')
        gst_percents    = request.form.getlist('gst_percent[]')

        if not vendor_id:
            flash("Vendor select karo!", "danger")
            return redirect(url_for('po_add'))

        try:
            # ── Transaction: create PO + line items atomically ──
            db.execute('BEGIN')

            db.execute(
                'INSERT INTO purchase_orders (vendor_id, status, total_amount) VALUES (?, ?, ?)',
                (vendor_id, 'pending', 0)
            )
            po_id = db.execute('SELECT last_insert_rowid()').fetchone()[0]

            total = 0
            for pid, qty, price, gst in zip(product_ids, quantities, purchase_prices, gst_percents):
                if pid and qty and price:
                    qty        = int(qty)
                    price      = float(price)
                    gst        = float(gst or 0)
                    gst_amount = price * qty * gst / 100
                    subtotal   = price * qty + gst_amount
                    total     += subtotal
                    db.execute(
                        'INSERT INTO purchase_order_items (po_id, product_id, quantity, unit_price, gst_percent) VALUES (?, ?, ?, ?, ?)',
                        (po_id, pid, qty, price, gst)
                    )

            db.execute('UPDATE purchase_orders SET total_amount = ? WHERE id = ?', (total, po_id))
            db.commit()
            flash("Purchase Order create ho gaya!", "success")
            return redirect(url_for('po_list'))

        except Exception as e:
            db.rollback()
            flash(f"PO create karne mein error aaya: {e}", "danger")
            return redirect(url_for('po_add'))

    vendors  = db.execute('SELECT * FROM vendors').fetchall()
    products = db.execute('SELECT * FROM products').fetchall()
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

    items = db.execute(
        'SELECT * FROM purchase_order_items WHERE po_id = ?', (id,)
    ).fetchall()

    try:
        # ── Transaction: add received stock + update PO status ──
        db.execute('BEGIN')

        for item in items:
            db.execute(
                'UPDATE products SET stock_qty = stock_qty + ? WHERE id = ?',
                (item['quantity'], item['product_id'])
            )

        db.execute(
            'UPDATE purchase_orders SET status = ? WHERE id = ?', ('received', id)
        )
        db.commit()
        flash("Stock receive ho gaya! Inventory update ho gayi!", "success")

    except Exception as e:
        db.rollback()
        flash(f"Stock receive karne mein error aaya: {e}", "danger")

    return redirect(url_for('po_detail', id=id))


@app.route('/purchase-orders/delete/<int:id>')
def po_delete(id):
    db = get_db()
    try:
        db.execute('BEGIN')
        db.execute('DELETE FROM purchase_order_items WHERE po_id = ?', (id,))
        db.execute('DELETE FROM purchase_orders WHERE id = ?', (id,))
        db.commit()
        flash("Purchase Order delete ho gaya!", "success")
    except Exception as e:
        db.rollback()
        flash(f"Delete karne mein error aaya: {e}", "danger")
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
    return render_template('invoices/list.html', invoices=invoices)


@app.route('/invoices/<int:id>')
def invoices_detail(id):
    db = get_db()
    invoice = db.execute('''
        SELECT invoices.*,
               customers.name    as customer_name,
               customers.email   as customer_email,
               customers.phone   as customer_phone,
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
               products.name        as product_name,
               products.gst_percent as gst_percent
        FROM order_items
        JOIN products ON order_items.product_id = products.id
        WHERE order_items.order_id = ?
    ''', (invoice['order_id'],)).fetchall()

    return render_template('invoices/detail.html', invoice=invoice, items=items)


@app.route('/invoices/mark-paid/<int:id>')
def invoices_mark_paid(id):
    db = get_db()
    db.execute('UPDATE invoices SET status = ? WHERE id = ?', ('paid', id))
    db.commit()
    flash("Invoice paid mark ho gaya!", "success")
    return redirect(url_for('invoices_detail', id=id))


@app.route('/invoices/<int:id>/print')
def invoices_print(id):
    db = get_db()
    invoice = db.execute('''
        SELECT invoices.*,
               customers.name    as customer_name,
               customers.email   as customer_email,
               customers.phone   as customer_phone,
               customers.address as customer_address
        FROM invoices
        JOIN customers ON invoices.customer_id = customers.id
        WHERE invoices.id = ?
    ''', (id,)).fetchone()

    items = db.execute('''
        SELECT order_items.*,
               products.name        as product_name,
               products.gst_percent as gst_percent
        FROM order_items
        JOIN products ON order_items.product_id = products.id
        WHERE order_items.order_id = ?
    ''', (invoice['order_id'],)).fetchall()

    company = db.execute('SELECT * FROM settings WHERE id = 1').fetchone()
    return render_template('invoices/print.html', invoice=invoice, items=items, company=company)


# ─── SETTINGS ───────────────────────────────────────
@app.route('/settings', methods=['GET', 'POST'])
def settings():
    db = get_db()
    if request.method == 'POST':
        company_name    = request.form['company_name']
        company_email   = request.form['company_email']
        company_phone   = request.form['company_phone']
        company_address = request.form['company_address']
        gstin           = request.form['gstin']
        invoice_prefix  = request.form['invoice_prefix']

        logo_filename = db.execute(
            'SELECT logo_filename FROM settings WHERE id = 1'
        ).fetchone()['logo_filename']

        if 'logo' in request.files:
            logo = request.files['logo']
            if logo.filename != '':
                ext           = logo.filename.rsplit('.', 1)[1].lower()
                logo_filename = f'company_logo.{ext}'
                logo.save(os.path.join('static', logo_filename))

        db.execute('''
            UPDATE settings
            SET company_name=?, company_email=?, company_phone=?,
                company_address=?, gstin=?, invoice_prefix=?, logo_filename=?
            WHERE id=1
        ''', (company_name, company_email, company_phone,
              company_address, gstin, invoice_prefix, logo_filename))
        db.commit()
        flash("Settings save ho gayi!", "success")
        return redirect(url_for('settings'))

    settings_row = db.execute('SELECT * FROM settings WHERE id = 1').fetchone()
    account_user = None
    if session.get('user_id'):
        account_user = db.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],)).fetchone()
    return render_template('settings.html', settings=settings_row, account_user=account_user)


@app.route('/account', methods=['POST'])
def account_update():
    if not session.get('user_id'):
        flash('Please log in to update your account.', 'danger')
        return redirect(url_for('login'))

    email = request.form.get('username')
    business_name = request.form.get('business_name')
    new_password = request.form.get('new_password')
    confirm_password = request.form.get('confirm_password')

    if not email or not business_name:
        flash('Email and business name are required.', 'danger')
        return redirect(url_for('settings'))

    db = get_db()
    current_user = db.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],)).fetchone()
    if not current_user:
        flash('Account not found.', 'danger')
        return redirect(url_for('login'))

    existing = db.execute('SELECT * FROM users WHERE username = ? AND id != ?', (email, current_user['id'])).fetchone()
    if existing:
        flash('Email already registered', 'danger')
        return redirect(url_for('settings'))

    if new_password:
        if new_password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return redirect(url_for('settings'))
        password_hash = generate_password_hash(new_password)
        db.execute(
            'UPDATE users SET username = ?, business_name = ?, password_hash = ? WHERE id = ?',
            (email, business_name, password_hash, current_user['id'])
        )
    else:
        db.execute(
            'UPDATE users SET username = ?, business_name = ? WHERE id = ?',
            (email, business_name, current_user['id'])
        )

    db.commit()
    session['username'] = email
    session['business_name'] = business_name
    flash('Account updated successfully.', 'success')
    return redirect(url_for('settings'))


@app.route('/account/delete', methods=['POST'])
def account_delete():
    if not session.get('user_id'):
        flash('Please log in to delete your account.', 'danger')
        return redirect(url_for('login'))

    db = get_db()
    db.execute('DELETE FROM users WHERE id = ?', (session['user_id'],))
    db.commit()
    session.clear()
    flash('Your account has been deleted.', 'success')
    return redirect(url_for('index'))


# ─── REPORTS ────────────────────────────────────────
@app.route('/reports')
def reports():
    return redirect(url_for('index'))


# ─── ABOUT ──────────────────────────────────────────
@app.route('/about')
def about():
    tech_stack = [
        "Python 3 + Flask",
        "SQLite database",
        "Jinja2 templates",
        "HTML + CSS",
    ]
    return render_template('about.html', tech_stack=tech_stack)


# ─── AUTH ───────────────────────────────────────────
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if not username or not password:
            flash('Username and password required', 'danger')
            return redirect(url_for('login'))

        db = get_db()
        user = db.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        if user and check_password_hash(user['password_hash'], password):
            session.clear()
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['business_name'] = user['business_name'] or 'FlowForge'
            flash('Logged in successfully', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid credentials', 'danger')
            return redirect(url_for('login'))

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out', 'success')
    return redirect(url_for('index'))


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username')
        business_name = request.form.get('business_name')
        password = request.form.get('password')
        password2 = request.form.get('password2')

        if not username or not password or not business_name:
            flash('Email, business name and password are required', 'danger')
            return redirect(url_for('signup'))

        if password != password2:
            flash('Passwords do not match', 'danger')
            return redirect(url_for('signup'))

        db = get_db()
        existing = db.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        if existing:
            flash('Email already registered', 'danger')
            return redirect(url_for('signup'))

        pw_hash = generate_password_hash(password)
        cursor = db.execute(
            'INSERT INTO users (username, business_name, password_hash) VALUES (?, ?, ?)',
            (username, business_name, pw_hash)
        )
        db.commit()
        user_id = cursor.lastrowid
        session.clear()
        session['user_id'] = user_id
        session['username'] = username
        session['business_name'] = business_name
        flash('Account created and logged in successfully.', 'success')
        return redirect(url_for('index'))

    return render_template('signup.html')


@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        username = request.form.get('username')
        if not username:
            flash('Please enter your username', 'danger')
            return redirect(url_for('forgot_password'))

        db = get_db()
        user = db.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        # In a real app we'd email a reset link. Here we just flash a generic message.
        flash('If an account with that username exists, a password reset link has been sent (simulated).', 'info')
        return redirect(url_for('login'))

    return render_template('forgot_password.html')


if __name__ == '__main__':
    app.run(debug=True)