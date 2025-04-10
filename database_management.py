import pymysql as mysql
from datetime import datetime, date
import os
from text_to_speech import text_to_speech_direct
import re
def is_valid_gmail(email):
    gmail_regex = r'^[a-zA-Z0-9._%+-]+@gmail\.com$'
    return bool(re.match(gmail_regex, email))

def mark_attendance(student_id):
    try:
        conn = mysql.connect(
            host="localhost",
            user="root",
            password="1234",
            database="face"
        )
        cursor = conn.cursor()
        today_date = date.today()
        cursor.execute("""
            SELECT * FROM attendance 
            WHERE id = %s AND DATE(timestamp) = %s
        """, (student_id, today_date))
        if cursor.fetchone() is None:
            timestamp = datetime.now()
            cursor.execute("""
                INSERT INTO attendance (id, timestamp) 
                VALUES (%s, %s)
            """, (student_id, timestamp))
            conn.commit()
            conn.close()
            return True
    except mysql.Error as err:
        print(f"Error: {err}")
        return False
    conn.close()

def delete_images(directory, user_id):
    """
    Deletes image files named as 'user.id.sample' in the specified directory.
    The 'sample' part ranges from 1 to 21.

    Args:
        directory (str): Path to the directory containing the images.
        user_id (str): User ID to match in the file name.
    """
    for i in range(1, 22):  # Sample ranges from 1 to 21
        filename = f"User.{user_id}.{i}.jpg"  # Change extension if necessary (e.g., .png)
        file_path = os.path.join(directory, filename)

        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                print(f"Deleted: {file_path}")
            else:
                print(f"File not found: {file_path}")
                return False
        except Exception as e:
            print(f"Error deleting file {file_path}: {e}")
            return False
    return True