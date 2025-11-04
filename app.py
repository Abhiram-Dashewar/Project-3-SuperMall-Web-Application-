from flask import Flask, render_template, redirect, request, url_for, g, session, flash, jsonify
import sqlite3

app = Flask(__name__)
app.secret_key = "supersecretkey"
DATABASE = 'mall.db'

def get_db():
    db = getattr(g, "_database", None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_db(exception):
    db = getattr(g, "_database", None)
    if db is not None:
        db.close()

def init_db():
    db = get_db()
    db.executescript("""
    CREATE TABLE IF NOT EXISTS shops (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        category TEXT,
        floor TEXT,
        contact TEXT,
        description TEXT
    );
    CREATE TABLE IF NOT EXISTS categories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE
    );
    CREATE TABLE IF NOT EXISTS floors (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE
    );
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        price REAL,
        category TEXT,
        shop TEXT,
        description TEXT,
        stock INTEGER,
        image TEXT
    );
    CREATE TABLE IF NOT EXISTS offers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        discount INTEGER,
        description TEXT,
        start TEXT,
        end TEXT
    );
    """)

    # Insert demo data
    try:
        # Insert categories
        categories = ['Electronics', 'Clothing & Fashion', 'Food & Beverages', 'Handicrafts', 'Home & Kitchen', 'Beauty & Personal Care', 'Sports & Outdoors']
        for cat in categories:
            db.execute('INSERT OR IGNORE INTO categories (name) VALUES (?)', (cat,))

        # Insert floors
        floors = ['Ground Floor', 'First Floor', 'Second Floor', 'Third Floor']
        for fl in floors:
            db.execute('INSERT OR IGNORE INTO floors (name) VALUES (?)', (fl,))

        # Insert demo shops
        shops_data = [
            ('Gigabite', 'Electronics', 'Ground Floor', '9490018370', 'Custom PC builds and gaming accessories'),
            ('Fashion Hub', 'Clothing & Fashion', 'First Floor', '9876543210', 'Latest fashion trends and accessories')
        ]
        for shop in shops_data:
            db.execute('INSERT OR IGNORE INTO shops (name, category, floor, contact, description) VALUES (?, ?, ?, ?, ?)', shop)

        # Insert demo products
        products_data = [
            ('Gaming Mouse', 25.99, 'Electronics', 'Gigabite', 'High-precision gaming mouse with RGB lighting', 50, 'https://example.com/mouse.jpg'),
            ('Wireless Keyboard', 45.50, 'Electronics', 'Gigabite', 'Mechanical wireless keyboard with backlit keys', 30, 'https://example.com/keyboard.jpg'),
            ('Cotton T-Shirt', 15.99, 'Clothing & Fashion', 'Fashion Hub', 'Comfortable 100% cotton t-shirt in various colors', 100, 'https://example.com/tshirt.jpg'),
            ('Denim Jeans', 79.99, 'Clothing & Fashion', 'Fashion Hub', 'Classic blue denim jeans with perfect fit', 75, 'https://example.com/jeans.jpg'),
            ('Coffee Beans', 12.99, 'Food & Beverages', 'Food Court', 'Premium arabica coffee beans, freshly roasted', 200, 'https://example.com/coffee.jpg'),
            ('Organic Honey', 8.50, 'Food & Beverages', 'Food Court', 'Pure organic honey from local beekeepers', 150, 'https://example.com/honey.jpg'),
            ('Handmade Pottery', 35.00, 'Handicrafts', 'Craft Corner', 'Beautiful handmade ceramic pottery set', 25, 'https://example.com/pottery.jpg'),
            ('Wooden Jewelry Box', 28.99, 'Handicrafts', 'Craft Corner', 'Elegant wooden jewelry box with intricate carvings', 40, 'https://example.com/jewelrybox.jpg')
        ]
        for product in products_data:
            db.execute('INSERT OR IGNORE INTO products (name, price, category, shop, description, stock, image) VALUES (?, ?, ?, ?, ?, ?, ?)', product)

        # Insert demo offers
        offers_data = [
            ('Summer Sale', 20, 'Get 20% off on all summer clothing items', '2025-06-01', '2025-08-31'),
            ('Electronics Week', 15, 'Special discount on all electronics this week', '2025-10-20', '2025-10-27'),
            ('Diwali Festival', 25, 'Festival offer on handicrafts and home decor', '2025-11-01', '2025-11-15')
        ]
        for offer in offers_data:
            db.execute('INSERT OR IGNORE INTO offers (title, discount, description, start, end) VALUES (?, ?, ?, ?, ?)', offer)

        db.commit()
    except Exception as e:
        print(f"Error inserting demo data: {e}")
        db.rollback()


@app.route("/")
def home():
    return render_template("home.html")

@app.route('/login', methods=['POST'])
def login():
    email = request.form['email']
    password = request.form['password']

    if email == 'admin@supermall.com' and password == "password123":
        session['admin'] = True
        flash('Login successful!', 'success')
        return redirect(url_for('admin'))
    else:
        flash('Invalid credentials!', 'error')
        return redirect(url_for('home'))
    
@app.route('/admin')
def admin():
    if not session.get('admin'):
        flash('Please login first!', 'error')
        return redirect(url_for('home'))

    # Fetch data for dashboard
    db = get_db()
    shops = db.execute('SELECT * FROM shops').fetchall()
    products = db.execute('SELECT * FROM products').fetchall()
    offers = db.execute('SELECT * FROM offers').fetchall()
    categories = db.execute('SELECT * FROM categories').fetchall()
    floors = db.execute('SELECT * FROM floors').fetchall()

    return render_template('admin.html',
                         shops=shops,
                         products=products,
                         offers=offers,
                         categories=categories,
                         floors=floors,
                         total_shops=len(shops),
                         total_products=len(products),
                         total_offers=len(offers))


# CRUD Routes for Admin

@app.route('/addshop', methods=['POST'])
def addshop():
    if not session.get('admin'):
        return redirect(url_for('home'))

    print("Form data received:", request.form)

    name = request.form['shopName']
    category = request.form['shopCategory']
    floor = request.form['shopFloor']
    contact = request.form['shopContact']
    description = request.form['shopDescription']

    db = get_db()
    db.execute('INSERT INTO shops (name, category, floor, contact, description) VALUES (?, ?, ?, ?, ?)',
               (name, category, floor, contact, description))
    db.commit()

    flash('Shop added successfully!', 'success')
    return redirect(url_for('admin'))

@app.route('/addproduct', methods=['POST'])
def addproduct():
    if not session.get('admin'):
        return redirect(url_for('home'))

    name = request.form['productName']
    price = request.form['productPrice']
    category = request.form['productCategory']
    shop = request.form['productShop']
    description = request.form['productDescription']
    stock = request.form.get('productStock', 1)
    image = request.form.get('productImage', '')

    db = get_db()
    db.execute('INSERT INTO products (name, price, category, shop, description, stock, image) VALUES (?, ?, ?, ?, ?, ?, ?)',
               (name, price, category, shop, description, stock, image))
    db.commit()

    flash('Product added successfully!', 'success')
    return redirect(url_for('admin'))

@app.route('/addoffer', methods=['POST'])
def addoffer():
    if not session.get('admin'):
        return redirect(url_for('home'))

    title = request.form['offerTitle']
    discount = request.form['offerDiscount']
    description = request.form['offerDescription']
    start = request.form['offerStart']
    end = request.form['offerEnd']

    db = get_db()
    db.execute('INSERT INTO offers (title, discount, description, start, end) VALUES (?, ?, ?, ?, ?)',
               (title, discount, description, start, end))
    db.commit()

    flash('Offer added successfully!', 'success')
    return redirect(url_for('admin'))

@app.route('/addcategory', methods=['POST'])
def addcategory():
    if not session.get('admin'):
        return redirect(url_for('home'))

    name = request.form['newCategory']

    db = get_db()
    try:
        db.execute('INSERT INTO categories (name) VALUES (?)', (name,))
        db.commit()
        flash('Category added successfully!', 'success')
    except sqlite3.IntegrityError:
        flash('Category already exists!', 'error')

    return redirect(url_for('admin'))

@app.route('/addfloor', methods=['POST'])
def addfloor():
    if not session.get('admin'):
        return redirect(url_for('home'))

    name = request.form['newFloor']

    db = get_db()
    try:
        db.execute('INSERT INTO floors (name) VALUES (?)', (name,))
        db.commit()
        flash('Floor added successfully!', 'success')
    except sqlite3.IntegrityError:
        flash('Floor already exists!', 'error')

    return redirect(url_for('admin'))

# Delete Routes

@app.route('/delete_shop/<int:shop_id>')
def delete_shop(shop_id):
    if not session.get('admin'):
        return redirect(url_for('home'))

    db = get_db()
    db.execute('DELETE FROM shops WHERE id = ?', (shop_id,))
    db.commit()

    flash('Shop deleted successfully!', 'success')
    return redirect(url_for('admin'))

@app.route('/delete_product/<int:product_id>')
def delete_product(product_id):
    if not session.get('admin'):
        return redirect(url_for('home'))

    db = get_db()
    db.execute('DELETE FROM products WHERE id = ?', (product_id,))
    db.commit()

    flash('Product deleted successfully!', 'success')
    return redirect(url_for('admin'))

@app.route('/delete_offer/<int:offer_id>')
def delete_offer(offer_id):
    if not session.get('admin'):
        return redirect(url_for('home'))

    db = get_db()
    db.execute('DELETE FROM offers WHERE id = ?', (offer_id,))
    db.commit()

    flash('Offer deleted successfully!', 'success')
    return redirect(url_for('admin'))

@app.route('/delete_category/<path:category_name>')
def delete_category(category_name):
    if not session.get('admin'):
        return redirect(url_for('home'))

    db = get_db()
    db.execute('DELETE FROM categories WHERE name = ?', (category_name,))
    db.commit()

    flash('Category deleted successfully!', 'success')
    return redirect(url_for('admin'))

@app.route('/delete_floor/<path:floor_name>')
def delete_floor(floor_name):
    if not session.get('admin'):
        return redirect(url_for('home'))

    db = get_db()
    db.execute('DELETE FROM floors WHERE name = ?', (floor_name,))
    db.commit()

    flash('Floor deleted successfully!', 'success')
    return redirect(url_for('admin'))

# API Routes for User Side

@app.route('/api/products')
def get_products():
    category = request.args.get('category')
    floor = request.args.get('floor')
    shop = request.args.get('shop')
    price_range = request.args.get('price')

    db = get_db()
    query = 'SELECT * FROM products WHERE 1=1'
    params = []

    if category and category != 'all':
        query += ' AND category = ?'
        params.append(category)

    if floor and floor != 'all':
        # Get shops on this floor
        shops_on_floor = db.execute('SELECT name FROM shops WHERE floor = ?', (floor,)).fetchall()
        shop_names = [s['name'] for s in shops_on_floor]
        if shop_names:
            query += ' AND shop IN ({})'.format(','.join('?' * len(shop_names)))
            params.extend(shop_names)

    if shop and shop != 'all':
        query += ' AND shop = ?'
        params.append(shop)

    if price_range and price_range != 'all':
        if price_range == '0-25':
            query += ' AND price <= 25'
        elif price_range == '25-50':
            query += ' AND price BETWEEN 25 AND 50'
        elif price_range == '50-100':
            query += ' AND price BETWEEN 50 AND 100'
        elif price_range == '100+':
            query += ' AND price > 100'

    products = db.execute(query, params).fetchall()
    return jsonify([dict(product) for product in products])

@app.route('/api/filters')
def get_filters():
    db = get_db()
    categories = db.execute('SELECT DISTINCT category FROM shops').fetchall()
    floors = db.execute('SELECT * FROM floors').fetchall()
    shops = db.execute('SELECT name FROM shops').fetchall()

    return jsonify({
        'categories': [c['category'] for c in categories],
        'floors': [f['name'] for f in floors],
        'shops': [s['name'] for s in shops]
    })

if(__name__) == '__main__':
    with app.app_context():
        init_db()
    app.run(debug=True)
