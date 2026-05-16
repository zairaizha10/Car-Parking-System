from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import qrcode
import os

app = Flask(__name__)
app.secret_key = 'parking_secret_key'

# -----------------------------------
# Database Configuration
# -----------------------------------

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

db_path = os.path.join(BASE_DIR, 'database', 'parking.db')

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + db_path

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# -----------------------------------
# Database Model
# -----------------------------------

class Vehicle(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    vehicle_no = db.Column(db.String(20), nullable=False)

    vehicle_type = db.Column(db.String(10), nullable=False)

    owner_name = db.Column(db.String(50), nullable=False)

    entry_time = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    exit_time = db.Column(
        db.DateTime,
        nullable=True
    )

    hours = db.Column(
        db.Integer,
        nullable=True
    )

    fee = db.Column(
        db.Integer,
        nullable=True
    )

    status = db.Column(
        db.String(20),
        default='Parked'
    )

    
class User(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    username = db.Column(
        db.String(50),
        unique=True,
        nullable=False
    )

    email = db.Column(
        db.String(100),
        unique=True,
        nullable=False
    )

    password = db.Column(
        db.String(100),
        nullable=False
    )

    is_admin = db.Column(
        db.Boolean,
        default=False
    )

# -----------------------------------
# Home Page
# -----------------------------------

@app.route('/')
def home():

    vehicles = Vehicle.query.all()

    total_slots = 80

    occupied_slots = len(vehicles)

    available_slots = total_slots - occupied_slots

    return render_template(
        'home.html',
        vehicles=vehicles,
        available_slots=available_slots
    )

# -----------------------------------
# Park Vehicle
# -----------------------------------

@app.route('/park_vehicle', methods=['GET', 'POST'])
def park_vehicle():

    if request.method == 'POST':

        vehicle_no = request.form['vehicle_no']
        vehicle_type = request.form['vehicle_type']
        owner_name = request.form['owner_name']
        hours = int(request.form['hours'])

        # Fee Calculation
        if vehicle_type == 'Bike':
            fee = hours * 10

        elif vehicle_type == 'Car':
            fee = hours * 20

        else:
            fee = hours * 40

        # Save Vehicle
        vehicle = Vehicle(
            vehicle_no=vehicle_no,
            vehicle_type=vehicle_type,
            owner_name=owner_name,
            hours=hours,
            fee=fee,
            status='Parked'
        )

        db.session.add(vehicle)
        db.session.commit()

        # -----------------------------
        # QR Code Generation
        # -----------------------------

        qr_data = f"""
Vehicle No: {vehicle.vehicle_no}
Owner: {vehicle.owner_name}
Type: {vehicle.vehicle_type}
Fee: ₹{vehicle.fee}
"""

        qr = qrcode.make(qr_data)

        os.makedirs('static/qr_codes', exist_ok=True)

        qr.save(f"static/qr_codes/{vehicle.id}.png")

        return redirect(url_for('home'))

    return render_template('user/park_vehicle.html')
# -----------------------------------
# Remove Vehicle
# -----------------------------------
@app.route('/exit_vehicle/<int:id>')
def exit_vehicle(id):

    import math

    vehicle = Vehicle.query.get_or_404(id)

    #vehicle.exit_time = datetime.utcnow()
    from datetime import timedelta

    vehicle.exit_time = vehicle.entry_time + timedelta(hours=2)

    duration = vehicle.exit_time - vehicle.entry_time

    # Convert to hours properly
    hours = math.ceil(
        duration.total_seconds() / 3600
    )

    vehicle.hours = hours

    rates = {

        'Bike': 10,

        'Car': 20,

        'Truck': 40
    }

    vehicle.fee = hours * rates.get(
        vehicle.vehicle_type,
        20
    )

    vehicle.status = 'Exited'

    db.session.commit()

    flash(
        f'Parking Fee: ₹{vehicle.fee}'
    )

    return redirect(url_for('home'))

@app.route('/edit_vehicle/<int:id>', methods=['GET', 'POST'])
def edit_vehicle(id):

    if not session.get('is_admin'):

        flash('Admin Access Required')

        return redirect(url_for('home'))

    vehicle = Vehicle.query.get_or_404(id)

    if request.method == 'POST':

        vehicle.vehicle_no = request.form['vehicle_no']

        vehicle.owner_name = request.form['owner_name']

        vehicle.vehicle_type = request.form['vehicle_type']

        db.session.commit()

        flash('Vehicle Updated Successfully')

        return redirect(url_for('view_vehicles'))

    return render_template(
        'admin/edit_vehicle.html',
        vehicle=vehicle
    )

@app.route('/delete_vehicle/<int:id>')
def delete_vehicle(id):

    # Check Admin Access
    if not session.get('is_admin'):

        flash('Admin Access Required')

        return redirect(url_for('home'))

    vehicle = Vehicle.query.get_or_404(id)

    db.session.delete(vehicle)

    db.session.commit()

    flash('Vehicle Deleted Successfully')

    return redirect(url_for('view_vehicles'))

#@app.route('/remove_vehicle/<int:id>')
#def remove_vehicle(id):

    vehicle = Vehicle.query.get_or_404(id)

    db.session.delete(vehicle)

    db.session.commit()

    return redirect(url_for('home'))

# -----------------------------------
# View Vehicles
# -----------------------------------

@app.route('/view_vehicles')
def view_vehicles():

    search = request.args.get('search')

    if search:

        vehicles = Vehicle.query.filter(

            Vehicle.vehicle_no.contains(search) |

            Vehicle.owner_name.contains(search) |

            Vehicle.vehicle_type.contains(search)

        ).all()

    else:

        vehicles = Vehicle.query.all()

    return render_template(

        'admin/view_vehicles.html',

        vehicles=vehicles
    )

# -----------------------------------
# Admin Dashboard
# -----------------------------------


@app.route('/admin_dashboard')
def admin_dashboard():

    vehicles = Vehicle.query.order_by(
        Vehicle.id.desc()
    ).all()

    total_vehicles = Vehicle.query.count()

    total_income = db.session.query(
        db.func.sum(Vehicle.fee)
    ).scalar()

    if total_income is None:
        total_income = 0

    total_slots = 20

    occupied_slots = total_vehicles

    available_slots = total_slots - occupied_slots

    return render_template(
        'admin/dashboard.html',

        vehicles=vehicles,

        total_vehicles=total_vehicles,

        total_income=total_income,

        available_slots=available_slots,

        occupied_slots=occupied_slots
    )

# -----------------------------------
# Login Page
# -----------------------------------

@app.route('/login', methods=['GET', 'POST'])
def login():

    if request.method == 'POST':

        email = request.form['email']

        password = request.form['password']

        user = User.query.filter_by(
            email=email,
            password=password
        ).first()

        if user and user.password == password:

            session['user_id'] = user.id

            session['username'] = user.username

            session['is_admin'] = user.is_admin

            flash('Login Successful')

            return redirect(url_for('home'))

        else:

            flash('Invalid Email or Password')

    return render_template('login.html')
@app.route('/logout')
def logout():

    session.clear()

    flash('Logged Out Successfully')

    return redirect(url_for('login'))

# -----------------------------------
# Register Page
# -----------------------------------

@app.route('/register', methods=['GET', 'POST'])
def register():

    if request.method == 'POST':

        username = request.form['username']

        email = request.form['email']

        password = request.form['password']

        existing_user = User.query.filter_by(
            email=email
        ).first()

        if existing_user:

            flash('Email already exists')

            return redirect(url_for('register'))

        user = User(
            username=username,
            email=email,
            password=password
        )
        existing_user = User.query.filter(
            (User.username == username) |
            (User.email == email)
        ).first()

        if existing_user:

            flash('Username or Email already exists')

            return redirect(url_for('register'))

        db.session.add(user)

        db.session.commit()

        flash('Registration Successful')

        return redirect(url_for('login'))

    return render_template('register.html')

# -----------------------------------
# Error Pages
# -----------------------------------

@app.errorhandler(404)
def not_found(error):

    return render_template('404.html'), 404

@app.errorhandler(500)
def server_error(error):

    return render_template('500.html'), 500

# -----------------------------------
# Main Function
# -----------------------------------

if __name__ == '__main__':

    # Create database folder if not exists
    os.makedirs('database', exist_ok=True)

    with app.app_context():

        db.create_all()

        admin = User.query.filter_by(
            email='admin@gmail.com'
        ).first()

        if not admin:

            admin_user = User(

                username='admin',

                email='admin@gmail.com',

                password='admin123',

                is_admin=True
            )

            db.session.add(admin_user)

            db.session.commit()

    app.run(debug=True)