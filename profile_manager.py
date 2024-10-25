import sqlite3


def create_profile(username, name="", bio="", profile_pic=""):
    conn = sqlite3.connect('profiles.db')
    cursor = conn.cursor()
    
    # Create table if it doesn't exist
    cursor.execute('''CREATE TABLE IF NOT EXISTS profiles 
                      (username TEXT PRIMARY KEY, name TEXT, bio TEXT, profile_pic TEXT)''')

    # Insert the new profile data
    cursor.execute('INSERT INTO profiles (username, name, bio, profile_pic) VALUES (?, ?, ?, ?)',
                   (username, name, bio, profile_pic))
    
    conn.commit()
    conn.close()

# Retrieve a user profile by username
def get_profile(username):
    conn = sqlite3.connect('profiles.db')
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM profiles WHERE username=?', (username,))
    profile = cursor.fetchone()
    
    conn.close()
    return profile

# Update a user's profile details
def update_profile(username, name, bio, profile_pic):
    conn = sqlite3.connect('profiles.db')
    cursor = conn.cursor()

    cursor.execute('UPDATE profiles SET name=?, bio=?, profile_pic=? WHERE username=?', 
                   (name, bio, profile_pic, username))

    conn.commit()
    conn.close()
