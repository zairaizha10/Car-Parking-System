import sqlite3

# Connect Database
connection = sqlite3.connect('database/parking.db')

# Create Cursor
cursor = connection.cursor()

# -----------------------------------
# Create Vehicle Table
# -----------------------------------

cursor.execute('''

CREATE TABLE IF NOT EXISTS vehicle (

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    vehicle_no TEXT NOT NULL,

    vehicle_type TEXT NOT NULL,

    owner_name TEXT NOT NULL,

    entry_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    hours INTEGER NOT NULL,

    fee INTEGER NOT NULL

)

''')

# -----------------------------------
# Create Admin Table
# -----------------------------------

cursor.execute('''

CREATE TABLE IF NOT EXISTS admin (

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    username TEXT NOT NULL,

    password TEXT NOT NULL

)

''')

# -----------------------------------
# Insert Default Admin
# -----------------------------------

cursor.execute('''

INSERT INTO admin (username, password)

VALUES (?, ?)

''', ('admin', 'admin123'))

# Save Changes
connection.commit()

# Close Connection
connection.close()

print("Database Created Successfully!")