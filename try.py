import sqlite3

def check_database():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    # Fetch all users
    c.execute("SELECT * FROM users")
    users = c.fetchall()
    
    if users:
        print("User Data:")
        for user in users:
            print(user)
    else:
        print("No users found in the database.")

    conn.close()

if __name__ == "__main__":
    check_database()
