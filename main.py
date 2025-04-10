import smtplib
import base64
from io import BytesIO
import pymysql
import matplotlib.pyplot as plt
from streamlit_autorefresh import st_autorefresh
import time
from streamlit_option_menu import option_menu
import pandas as pd
from PIL import Image
import google.generativeai as ai
from recognition import recognition
import re
from text_to_speech import text_to_speech_direct
from dataset_creation_dlib import dataset_creation
from database_management import delete_images
import speech_recognition as sr
import cv2
import os
import streamlit as st
import tempfile
import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

def get_db_connection():
    return pymysql.connect(
        host="localhost",  # Replace with your host
        user="root",  # Replace with your username
        password="1234",  # Replace with your password
        database="face"  # Replace with your database name
    )


def is_valid_email(email):
    email_regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    return re.match(email_regex, email) is not None

# Initialize session state
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

# Sidebar menu
with st.sidebar:
    selected = option_menu(
        menu_title="Services",
        options=["Home", "Admin", "AI-Chatbot", "View Attendance", "Contact Us"],
        icons=["house-fill", "person-fill-gear", "robot", "book", "envelope"],
        menu_icon="cast",
        default_index=0
    )
# Admin authentication and functionality
if selected == "Admin":
    if not st.session_state.authenticated:
        st.title("👨‍💻 Admin Login")
        # Admin authentication
        username = st.text_input("Username").lower()
        password = st.text_input("Password", type="password")
        login_button = st.button("Login")

        if login_button:
            if username == "admin" and password == "1234":
                st.success("Login successful! Welcome, Admin!")
                st.session_state.authenticated = True  # Set authenticated state
                st.rerun()
            else:
                st.error("Invalid username or password. Please try again.")

    elif st.session_state.authenticated:

        st.title("Admin Dashboard")
        st.header("Choose an action:")
        # Admin functionalities
        admin_action = st.selectbox(
            "Admin Actions", ["Insert Data", "Update Data", "Delete Data", "View All Records"]
        )

        if admin_action == "Insert Data":
            def fetch_student_details(student_id):
                try:
                    connection = get_db_connection()
                    with connection.cursor() as cursor:
                        cursor.execute("SELECT * FROM students WHERE id = %s", (student_id,))
                        return cursor.fetchone()
                except pymysql.MySQLError as e:
                    st.error(f"Database error: {e}")
                    return None
                finally:
                    connection.close()


            # Function to update name
            def update_name(student_id, new_name):
                try:
                    connection = get_db_connection()
                    with connection.cursor() as cursor:
                        cursor.execute("UPDATE students SET name = %s WHERE id = %s", (new_name, student_id))
                        connection.commit()
                        st.success(f"Name updated successfully for ID {student_id}!")
                        time.sleep(1)
                        st.session_state.student_details = None
                        st.rerun()
                except pymysql.MySQLError as e:
                    st.error(f"Database error: {e}")
                finally:
                    connection.close()


            # Function to update email
            def update_email(student_id, new_email):
                try:
                    connection = get_db_connection()
                    with connection.cursor() as cursor:
                        # Check if email already exists
                        cursor.execute("SELECT COUNT(*) AS count FROM students WHERE Email = %s", (new_email,))
                        email_exists = cursor.fetchone()['count'] > 0

                        if email_exists:
                            st.error("This email is already in use. Please use a different email.")
                        else:
                            cursor.execute("UPDATE students SET Email = %s WHERE id = %s", (new_email, student_id))
                            connection.commit()
                            st.success(f"Email updated successfully for ID {student_id}!")
                            time.sleep(1)
                            st.session_state.student_details = None
                            st.rerun()
                except pymysql.MySQLError as e:
                    st.error(f"Database error: {e}")
                finally:
                    connection.close()
            # Database connection setup
            st.subheader("Insert Data")
            with st.form("insert_form"):
                id = st.text_input("ID")
                name = st.text_input("Name")
                email = st.text_input("Email")
                submit_button = st.form_submit_button("Submit")

                if submit_button:
                    # Database checks
                    try:
                        connection = get_db_connection()
                        cursor = connection.cursor()

                        # Check if the ID already exists
                        cursor.execute("SELECT COUNT(*) FROM students WHERE id = %s", (id,))
                        id_exists = cursor.fetchone()[0] > 0

                        # Check if the email already exists
                        cursor.execute("SELECT COUNT(*) FROM students WHERE email = %s", (email,))
                        email_exists = cursor.fetchone()[0] > 0

                        # Validation checks
                        if not id or not name or not email:
                            st.error("All fields are required. Please fill them out.")
                        elif not is_valid_email(email):
                            st.error("Invalid email format. Please enter a valid email address.")
                        elif id_exists:
                            st.error("The ID already exists. Please use a unique ID.")
                        elif email_exists:
                            st.error("The email already exists. Please use a different email address.")
                        else:
                            if dataset_creation(id):
                                # Insert the data into the database
                                cursor.execute(
                                    "INSERT INTO students (id, name, email) VALUES (%s, %s, %s)",
                                    (id, name, email)
                                )
                                connection.commit()
                                st.success(f"Data inserted successfully!\nID: {id}\nName: {name}\nEmail: {email}")
                                text_to_speech_direct(f"Enrollment Successful for ID: {id},Name: {name}")
                            else:
                                st.error("Data insertion failed. Please try again.")
                    except pymysql.MySQLError as e:
                        st.error(f"Database error: {e}")

                    finally:
                        connection.close()


        elif admin_action == "Update Data":

            # import re
            # import pymysql
            # import streamlit as st
            # import time


            # Function to get a database connection
            def get_db_connection():
                return pymysql.connect(
                    host="localhost",
                    user="root",
                    password="1234",
                    database="face",
                    cursorclass=pymysql.cursors.DictCursor  # Ensure results are returned as dictionaries
                )


            # Function to validate email format
            def is_valid_email(email):
                email_regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
                return re.match(email_regex, email) is not None


            # Function to fetch student details
            def fetch_student_details(student_id):
                try:
                    connection = get_db_connection()
                    with connection.cursor() as cursor:
                        cursor.execute("SELECT * FROM students WHERE id = %s", (student_id,))
                        return cursor.fetchone()  # Fetch one row as a dictionary
                except pymysql.MySQLError as e:
                    st.error(f"Database error: {e}")
                    return None
                finally:
                    connection.close()


            # Function to update name
            def update_name(student_id, new_name):
                try:
                    connection = get_db_connection()
                    with connection.cursor() as cursor:
                        cursor.execute("UPDATE students SET name = %s WHERE id = %s", (new_name, student_id))
                        connection.commit()
                        st.success(f"Name updated successfully for ID {student_id}!")
                        text_to_speech_direct("Name updated successfully for ID: " + str(student_id))
                        time.sleep(1)
                        st.session_state.student_details = None
                        st.rerun()  # Refresh the app to clear session state
                except pymysql.MySQLError as e:
                    st.error(f"Database error: {e}")
                finally:
                    connection.close()


            # Function to update email
            def update_email(student_id, new_email):
                try:
                    connection = get_db_connection()
                    with connection.cursor() as cursor:
                        # Check if email already exists
                        cursor.execute("SELECT COUNT(*) AS count FROM students WHERE Email = %s", (new_email,))
                        email_exists = cursor.fetchone()['count'] > 0

                        if email_exists:
                            st.error("This email is already in use. Please use a different email.")
                        else:
                            cursor.execute("UPDATE students SET Email = %s WHERE id = %s", (new_email, student_id))
                            connection.commit()
                            st.success(f"Email updated successfully for ID {student_id}!")
                            text_to_speech_direct("Email updated successfully for ID: " + str(student_id))
                            time.sleep(1)
                            st.session_state.student_details = None
                            st.rerun()  # Refresh the app to clear session state
                except pymysql.MySQLError as e:
                    st.error(f"Database error: {e}")
                finally:
                    connection.close()


            # Main Streamlit Application
            st.subheader("Update Data")

            # Initialize session state for student details
            if "student_details" not in st.session_state:
                st.session_state.student_details = None

            # Step 1: Input ID to fetch details
            id = st.number_input("Enter the Student ID to fetch details", min_value=1, step=1)
            fetch_button = st.button("Fetch Details")

            if fetch_button:
                # Fetch student details and store them in session state
                student_details = fetch_student_details(id)
                if student_details:
                    st.session_state.student_details = student_details
                else:
                    st.error("No student found with the provided ID.")

            # Step 2: Display fetched details if available
            if st.session_state.student_details:
                st.write("Student details:")
                st.dataframe({
                    "ID": [st.session_state.student_details['id']],
                    "Name": [st.session_state.student_details['name']],
                    "Email": [st.session_state.student_details['Email']]
                })

                # Step 3: Choose what to update
                update_field = st.radio("What would you like to update?", ["Name", "Email"])

                if update_field == "Name":
                    new_name = st.text_input("Enter the new name")
                    if st.button("Update Name"):
                        if new_name.strip():
                            update_name(st.session_state.student_details['id'], new_name)
                        else:
                            st.error("Name cannot be empty.")

                elif update_field == "Email":
                    new_email = st.text_input("Enter the new email")
                    if st.button("Update Email"):
                        if not new_email.strip():
                            st.error("Email cannot be empty.")
                        elif not is_valid_email(new_email):
                            st.error("Invalid email format. Please enter a valid email.")
                        else:
                            update_email(st.session_state.student_details['id'], new_email)




        elif admin_action == "Delete Data":
            import pymysql
            import streamlit as st


            # Function to get the database connection
            def get_db_connection():
                return pymysql.connect(
                    host="localhost",
                    user="root",
                    password="1234",
                    database="face",
                    cursorclass=pymysql.cursors.DictCursor  # Ensures results are returned as dictionaries
                )


            # Function to delete student record
            def delete_student(student_id):
                try:
                    connection = get_db_connection()
                    with connection.cursor() as cursor:
                        # Check if student exists
                        cursor.execute("SELECT COUNT(*) FROM students WHERE id = %s", (student_id,))
                        student_exists = cursor.fetchone()['COUNT(*)'] > 0

                        if student_exists:
                            # Delete the student record (this will also delete related attendance records due to ON DELETE CASCADE)
                            cursor.execute("DELETE FROM students WHERE id = %s", (student_id,))
                            connection.commit()
                            return True
                        else:
                            return False
                except pymysql.MySQLError as e:
                    st.error(f"Database error: {e}")
                    return False
                finally:
                    connection.close()


            # Streamlit interface for deleting student record
            def delete_data():
                st.subheader("Delete Student Record")

                # Ask for the student ID
                student_id = st.number_input("Enter the Student ID to delete", min_value=1, step=1)

                # Button to trigger the delete action
                if st.button("Delete Student"):
                    if student_id:
                        if delete_images("dataset_copy/", student_id):
                            success = delete_student(student_id)
                            text_to_speech_direct("Deleted Successfully for id: " + str(student_id))
                            if success:
                                st.success(f"Student with ID {student_id} was successfully deleted.")
                        else:
                            text_to_speech_direct("Data deletion failed for id: " + str(student_id))
                            st.error(f"Data deletion failed for ID {student_id}. Please try again.")
                    else:
                        st.error("Please enter a valid student ID.")


            # Calling the delete_data function to implement the feature
            delete_data()


        elif admin_action == "View All Records":

            # Function to get the database connection
            def get_db_connection():
                return pymysql.connect(
                    host="localhost",
                    user="root",
                    password="1234",
                    database="face",
                    cursorclass=pymysql.cursors.DictCursor  # Ensures results are returned as dictionaries
                )


            # Function to fetch all student records along with attendance details
            def fetch_all_records():
                try:
                    connection = get_db_connection()
                    with connection.cursor() as cursor:
                        # SQL Query to join students and attendance and fetch the necessary details
                        query = """
                        SELECT 
                            s.id, 
                            s.name, 
                            s.Email, 
                            YEAR(a.attendance_date) AS year, 
                            MONTH(a.attendance_date) AS month, 
                            COUNT(a.attendance_date) AS days_present
                        FROM 
                            students s
                        LEFT JOIN 
                            attendance a ON s.id = a.id
                        GROUP BY 
                            s.id, YEAR(a.attendance_date), MONTH(a.attendance_date)
                        ORDER BY 
                            s.id, year, month;
                        """
                        cursor.execute(query)
                        return cursor.fetchall()
                except pymysql.MySQLError as e:
                    st.error(f"Database error: {e}")
                    return []
                finally:
                    connection.close()


            # Streamlit interface to display the records
            def view_all_records():
                st.subheader("View All Student Records with Attendance")

                # Fetch all records
                records = fetch_all_records()

                # If records exist, display them in a table
                if records:
                    st.dataframe(records)  # Display data in tabular format
                else:
                    st.write("No records found.")


            # Calling the view_all_records function to display the records
            view_all_records()

        # Logout button
        logout_button = st.button("Logout")
        if logout_button:
            st.success("Logged out successfully!")
            st.session_state.authenticated = False
            st.rerun()
elif selected == "View Attendance":

    # Initialize session state
    if "attendance_data" not in st.session_state:
        st.session_state.attendance_data = None
    if "student_email" not in st.session_state:
        st.session_state.student_email = None
    if "student_name" not in st.session_state:
        st.session_state.student_name = None


    # Function to connect to MySQL
    def connect_to_mysql(host, user, password, database):
        try:
            connection = pymysql.connect(
                host=host,
                user=user,
                password=password,
                database=database
            )
            return connection
        except pymysql.MySQLError as e:
            st.error(f"❌ Database Connection Error: {e}")
            return None


    # Function to fetch attendance data for a specific student
    def fetch_student_attendance(student_id):
        connection = connect_to_mysql("localhost", user="root", password="1234", database="face")
        if not connection:
            return None

        try:
            query = """
            SELECT 
                s.id AS student_id, 
                s.name AS student_name,
                s.email AS student_email,
                YEAR(a.attendance_date) AS year,
                MONTH(a.attendance_date) AS month,
                COUNT(DISTINCT a.attendance_date) AS days_present
            FROM 
                students s
            LEFT JOIN 
                attendance a ON s.id = a.id
            WHERE 
                s.id = %s
            GROUP BY 
                s.id, s.name, s.email, YEAR(a.attendance_date), MONTH(a.attendance_date)
            ORDER BY 
                year, month;
            """
            with connection.cursor(pymysql.cursors.DictCursor) as cursor:
                cursor.execute(query, (student_id,))
                data = cursor.fetchall()

                if data:
                    filtered_data = [row for row in data if row['days_present'] > 0]

                    if not filtered_data:
                        st.warning(f"⚠️ No suitable attendance data found for Student ID {student_id}.")
                        st.session_state.attendance_data = None
                    else:
                        st.session_state.attendance_data = pd.DataFrame(filtered_data)
                        st.session_state.student_email = filtered_data[0]['student_email']
                        st.session_state.student_name = filtered_data[0]['student_name']
                else:
                    st.error(f"⚠️ Student not found for Student ID {student_id}.")
                    st.session_state.attendance_data = None

        except pymysql.MySQLError as e:
            st.error(f"❌ SQL Query Error: {e}")
            st.session_state.attendance_data = None
        finally:
            connection.close()


    # Function to plot a bar graph
    def plot_attendance_bargraph(df):
        try:
            month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
            plt.figure(figsize=(10, 6))
            plt.bar(df['month'].astype(str), df['days_present'].astype(int), color='skyblue')
            plt.xlabel('Month', fontsize=14)
            plt.ylabel('Days Present', fontsize=14)
            plt.title('Student Attendance Month Wise', fontsize=20)
            plt.xticks(ticks=df['month'].astype(str), labels=[month_names[m - 1] for m in df['month']], rotation=45)
            plt.tight_layout()
            st.pyplot(plt)

            # Attendance message
            if df['days_present'].min() < 1:
                st.markdown("<h3 style='text-align: center; color: red; font-weight: bold;'>Bad Attendance</h3>",
                            unsafe_allow_html=True)
            else:
                st.markdown("<h3 style='text-align: center; color: green; font-weight: bold;'>Good Attendance</h3>",
                            unsafe_allow_html=True)

        except Exception as e:
            st.error(f"❌ Plotting Error: {e}")


    # Function to assign badges
    def assign_badge(days_present, month):
        month_names = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October',
                       'November', 'December']
        month_name = month_names[month - 1]

        if days_present >= 4:
            return "badges/diamond_badge.png", f"Congratulations! Achieved Diamond badge for {month_name} Month"
        elif days_present == 3:
            return "badges/gold_badge.png", f"Congratulations! Achieved Gold badge for {month_name} Month"
        elif days_present == 2:
            return "badges/silver_badge.png", f"Congratulations! Achieved Silver badge for {month_name} Month"
        else:
            return None, None


    # Function to send attendance report via email
    def send_email(to_email, student_name, attendance_data):
        sender_email = ""
        sender_password = ""
        subject = f"Avanthi Attendance Management System"

        # Convert DataFrame to HTML table
        attendance_html = attendance_data.to_html(index=False)

        message = MIMEMultipart()
        message["From"] = sender_email
        message["To"] = to_email
        message["Subject"] = subject

        body = f"""
        <html>
        <body>
            <h2>Attendance Report for {student_name}</h2>
            {attendance_html}
            <p>Thank you!</p>
        </body>
        </html>
        """
        message.attach(MIMEText(body, "html"))

        try:
            server = smtplib.SMTP("smtp.gmail.com", 587)
            server.starttls()
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, to_email, message.as_string())
            server.quit()
            st.success("📧 Email sent successfully!")
            text_to_speech_direct("Attendance report sent successfully")
        except Exception as e:
            st.error(f"❌ Email Sending Error: {e}")


    # Streamlit UI
    st.title("📜 Student Attendance Checker")
    st.write("Enter the student ID to view their attendance by month and visualize it.")

    # Store previous student ID
    if "prev_student_id" not in st.session_state:
        st.session_state.prev_student_id = None

    # Number input for Student ID
    student_id = st.number_input("Enter Student ID", min_value=1, step=1)

    # Clear previous output if student ID changes
    if student_id != st.session_state.prev_student_id:
        st.session_state.attendance_data = None
        st.session_state.student_email = None
        st.session_state.student_name = None
        st.session_state.prev_student_id = student_id  # Update stored student ID

    if st.button("Fetch Attendance Data"):
        with st.spinner("Fetching attendance data..."):
            fetch_student_attendance(student_id)

    if st.session_state.attendance_data is not None:
        st.write(f"### Attendance Data for Student ID {student_id}")
        st.dataframe(st.session_state.attendance_data)

        # Initialize badge_awarded in session state
        st.session_state.badge_awarded = False

        # Store badge images and captions
        badges = []

        # Group by year and month for structured display
        grouped_data = st.session_state.attendance_data.groupby(["year", "month"])

        for (year, month), group in grouped_data:
            days_present = group["days_present"].sum()

            if days_present > 0:  # Check eligibility per month
                badge, caption = assign_badge(days_present, month)
                if badge:
                    badges.append((badge, f"{caption}"))
                    st.session_state.badge_awarded = True

                    # Display badges in a row
        if st.session_state.badge_awarded:
            st.write("### 🎉 Monthly Achievements: 🎊")
            cols = st.columns(len(badges))  # Create dynamic columns
            for col, (badge, caption) in zip(cols, badges):
                with col:
                    st.image(badge, caption=caption, width=120)
        else:
            st.warning("⚠️ No badges available based on attendance. keep up the good work!")
        try:
            plot_attendance_bargraph(st.session_state.attendance_data)
        except Exception as e:
            st.error(f"No proper graph available for this student")
        st.write(" ")
        st.write(" ")
        st.write(" ")
        # Button to send email
        if st.button("Send Attendance Report to Your Email",help="Click here to send the attendance report to your email"):
            if st.session_state.student_email:
                with st.spinner("Sending email..."):
                    send_email(st.session_state.student_email, st.session_state.student_name,
                               st.session_state.attendance_data)
            else:
                st.error("❌ No email found for this student.")





elif selected == "Home":

    # Function to encode an image for the logo
    def encode_logo_to_base64(logo_path):
        with open(logo_path, "rb") as logo_file:
            return base64.b64encode(logo_file.read()).decode()


    # Encode the logo image
    logo_base64 = encode_logo_to_base64("images/logo.jpeg")  # Replace with your logo path

    # Add the title with the logo
    st.markdown(
        f"""
        <div style="display: flex; align-items: center;">
            <img src="data:image/png;base64,{logo_base64}" alt="Logo" style="width: 150px; height: 150px;margin-left: 18px; margin-right: 15px;">
            <h1 style="margin: 0; font-size: 45px;">Avanthi Attendance Management System</h1>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # List of image file paths (ensure the images are in the 'images' folder)
    image_paths = [
        "images/i1.jpg", "images/i5.jpg",
         "images/i3.jpg"
    ]

    # Load images and resize to 1280x720
    images = [Image.open(image_path).resize((1280, 720)) for image_path in image_paths]

    # Set a refresh interval (in milliseconds) to auto-refresh the page
    autorefresh_counter = st_autorefresh(interval=3000)

    # Determine the current image index
    current_image = autorefresh_counter % len(images)


    # Function to encode image to base64
    def image_to_base64(img, format="JPEG"):
        buffer = BytesIO()
        img.save(buffer, format=format)
        buffer.seek(0)
        img_base64 = base64.b64encode(buffer.read()).decode()
        return img_base64


    # Get the base64 string for the current image
    encoded_image = image_to_base64(images[current_image])
    st.subheader("Below are the show case images of the program")
    # Add custom CSS for corner borders
    st.markdown(
        """
        <style>
        .image-container {
            border: 5px solid #4CAF50; /* Green border */
            border-radius: 15px; /* Rounded corners */
            padding: 5px; /* Padding inside the border */
            max-width: 100%; /* Allow full width */
            box-shadow: 0px 4px 6px rgba(0, 0, 0, 0.3); /* Add shadow */
            text-align: center;
            margin-bottom: 20px; /* Add spacing below the image */
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # Display the current image with styled container
    st.markdown(
        f"""
        <div class="image-container">
            <img src="data:image/jpeg;base64,{encoded_image}" style="width: 100%; height: auto;" />
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.subheader("Below video demonstrates the working of the project")
    st.video("web.mp4", format="video/mp4")

    # Add a description
    st.write("")
    st.write("")
    st.write("")
    # Display the project outcomes
    st.markdown(
        """
        <div style="background-color: #f9f9f9; padding: 20px; border-radius: 10px; border: 1px solid #ddd;",width: 100%;>
            <h2 style="color: #4CAF50; text-align: center;">Features of the Project</h2>
            <ul style="line-height: 1.8; font-size: 16px; color: #333;">
                <li><strong>Automated Attendance Tracking:</strong>
                    <ul>
                        <li>A robust and efficient system that automates attendance recording using advanced face recognition technology.</li>
                        <li>Minimizes human error and enhances administrative efficiency.</li>
                    </ul>
                </li>
                <li><strong>AI-Powered Chatbot Integration:</strong>
                    <ul>
                        <li>Real-time user assistance powered by Google Gemini API.</li>
                        <li>Improves user experience and reduces reliance on manual support.</li>
                    </ul>
                </li>
                <li><strong>Admin Email Notification System:</strong>
                    <ul>
                        <li>Seamless issue reporting for administrators via email.</li>
                        <li>Ensures prompt responses and enhances system reliability.</li>
                    </ul>
                </li>
                <li><strong>Real-Time Voice Notifications:</strong>
                    <ul>
                        <li>Delivers immediate feedback to users, improving accessibility.</li>
                        <li>Enables effective operation in dynamic environments.</li>
                    </ul>
                </li>
                <li><strong>Comprehensive Solution:</strong>
                    <ul>
                        <li>Combines advanced AI, machine learning, and deep learning to overcome limitations of traditional methods.</li>
                        <li>Optimized for dynamic and scalable use cases, ensuring reliability and user satisfaction.</li>
                    </ul>
                </li>
            </ul>
        <h3 style="color: #4CAF50;">How It Benefits Users:</h3>
        <ul style="line-height: 1.8; font-size: 16px; color: #333;">
            <li>Automated attendance tracking saves time and reduces errors.</li>
            <li>Real-time voice notifications improve accessibility and provide instant feedback.</li>
            <li>AI-powered chatbot assists users with queries, ensuring a seamless experience.</li>
            <li>An automated email notification is sent to the user after attendance is successfully marked, providing a 
                real-time confirmation and ensuring transparency in the attendance process.</li>
        </ul>
        <h3 style="color: #4CAF50;">How It Benefits Admins:</h3>
        <ul style="line-height: 1.8; font-size: 16px; color: #333;">
            <li>Efficient attendance management reduces administrative workload.</li>
            <li>Admin email notification system ensures timely issue resolution.</li>
            <li>Comprehensive dashboards allow for easy data management and report generation.</li>
        </ul>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.write("")
    st.write("")
    st.write("")
    # Add a centered button
    st.write("")
    st.write("")
    col1, col2, col3 = st.columns(3)
    with col2:
        clicked = st.button("Start Face Recognition System", help="Click to start attendance")
        start_time = 9  # 9 AM
        end_time = 23  # 5 PM
        if clicked:
            current_hour = datetime.datetime.now().hour
            if start_time <= current_hour < end_time:
                st.success("Face Recognition System started successfully!")
                with st.spinner("Recognizing faces..."):
                    recognition()
            else:
                st.error("Recognition can only be opened between 9 AM and 5 PM. Please try again during working hours.")
                time.sleep(2)
    st.write("")
    st.write("")
    st.write("")
    st.write("")
    st.markdown(
        """
        <h4 style="text-align: center;"> About Us</h4>
        Avanthi Attendance Management System is an innovative solution designed to streamline the attendance process using advanced face recognition technology. 
        It ensures accuracy, efficiency, and reliability for educational institutions and organizations.
        """
        , unsafe_allow_html=True)
    st.markdown(
        """
        <footer>
        <hr>
        <div style="text-align: center; font-size: 14px; color: gray;">
            © 2025 Avanthi Attendance Management System. All rights reserved.
            <br>
            For inquiries, contact us at <a href="mailto:" style="text-decoration: none;">support@avanthiams.com</a> or visit our website: <a href="https://aietg.ac.in/" style="text-decoration: none;">www.avanthi.com</a>.
        </div>
        </footer>
        """,
        unsafe_allow_html=True,
    )
elif selected == "AI-Chatbot":
    def recognize_speech():
        recognizer = sr.Recognizer()
        with sr.Microphone() as source:
            # st.write("🎤 Speak something...")
            recognizer.adjust_for_ambient_noise(source)

            try:
                with col1:
                    st.write("🎤 Listening...")
                audio = recognizer.listen(source)  # Capture voice input
                text = recognizer.recognize_google(audio).lower()  # Convert speech to text
                # st.write("🎤 You said:", text)

                # Check for voice command to redirect
                if "contact" in text:
                    st.session_state.menu_option = "Contact"
                    st.rerun()  # Rerun to update navigation
                return text
            except sr.UnknownValueError:
                return False
            except sr.RequestError:
                return False
    # loaded=False
    # with st.spinner("Loading chatbot..."):
    # Configure the Gemini model with your API key
    API_KEY = st.secrets["GOOGLE_API_KEY"]  # Store your API key in .streamlit/secrets.toml
    ai.configure(api_key=API_KEY)

    # Instruction for the Gemini model
    instruction = (
        "You are a friendly and helpful bot specializing in solving issues related to "
        "face recognition-based attendance systems. Provide practical solutions and "
        "explanations for common problems like camera issues, recognition errors, "
        "database integration challenges, and more. Always respond in a kind and helpful tone.\n"
        "1. Provide the answer in bullet form for clarity.\n"
        "2. Do not respond in bold letters, only use normal text.\n"
        "3. Only respond to questions specifically related to face recognition-based attendance systems.\n"
        "4. Summarize lengthy responses into at most 2-3 lines.\n"
    )

    # Start the chat model with the instruction
    model = ai.GenerativeModel(
        model_name="gemini-1.5-flash",
        system_instruction=instruction
    )

    # App title
    st.title("🤖 ChatBot For Attendance Management System")

    # Initialize chat history in the session state
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Input field for user messages
    user_input = st.chat_input("Enter your message")
    voice_query = None
    col1, col2 = st.columns([8, 1])
    with col2:
        if st.button("🎤 Speak"):
            voice_query = recognize_speech()
            if not voice_query:
                # st.error("Speech not recognized. Please try again.")
                with col1:
                    st.error("Please try again with a clear voice command.")
                    time.sleep(2)
                    st.rerun()
            # st.write("📝 You asked:", voice_query)

    # Use voice input if available
    if voice_query and not user_input:
        user_input = voice_query
    if user_input:
        # Display the user's message
        with st.chat_message("user"):
            st.markdown(user_input)
        st.session_state.messages.append({"role": "user", "content": user_input})

        # Check for special commands (bye and admin)
        if user_input.lower() in ["bye", "exit", "quit"]:
            st.session_state.messages.append(
                {"role": "assistant", "content": "Goodbye! The application will now close."})
            st.markdown("Thank you for using the ChatBot. Any questions feel free to ask?")
        elif user_input.lower() in ["admin", "administrator"]:
            st.session_state.messages.append({"role": "assistant", "content": "Admin is available."})
            st.markdown("Communicate with admin at Home Page")
        else:
            with st.spinner("Generating response..."):
                # Generate response using the Gemini model
                with st.chat_message("assistant"):
                    try:
                        # Start a new chat session and send the user's message
                        chat = model.start_chat()
                        response = chat.send_message(user_input).text
                        st.markdown(response)
                    except Exception as e:
                        response = "Sorry, I encountered an error. Please try again later."
                        st.error(f"Error: {str(e)}")  # Log the error

            # Save the assistant's response to the session state
            st.session_state.messages.append({"role": "assistant", "content": response})
            st.rerun()
elif selected == "Contact Us":


    def capture_image():
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as temp_file:
            filename = temp_file.name

        cap = cv2.VideoCapture(0)
        ret, frame = cap.read()
        if ret:
            # Add timestamp to the image
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            font = cv2.FONT_HERSHEY_SIMPLEX
            font_scale = 0.7
            color = (0, 255, 0)  # Green
            thickness = 2
            position = (10, frame.shape[0] - 10)

            cv2.putText(frame, timestamp, position, font, font_scale, color, thickness, cv2.LINE_AA)
            cv2.imwrite(filename, frame)
        cap.release()
        return filename if ret else None


    def send_email_with_attachment(mymail, password, subject, content, id_field):
        try:
            if not subject or not content or not id_field:
                st.error("Fill all fields!")
                return

            image_path = capture_image()
            if not image_path:
                st.error("Failed to capture image.")
                return

            msg = MIMEMultipart()
            msg['From'] = mymail
            msg['To'] = mymail
            msg['Subject'] = subject

            body = f"ID: {id_field}\n\n{content}"
            msg.attach(MIMEText(body, 'plain'))

            with open(image_path, "rb") as attachment:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(attachment.read())
                encoders.encode_base64(part)
                part.add_header('Content-Disposition', f'attachment; filename={os.path.basename(image_path)}')
                msg.attach(part)

            with smtplib.SMTP('smtp.gmail.com', 587) as server:
                server.starttls()
                server.login(mymail, password)
                server.sendmail(mymail, mymail, msg.as_string())

            # st.success("Email sent successfully!")
            os.remove(image_path)  # Delete the temporary image file after sending
            return True
        except Exception as e:
            st.error(f"Failed to send email: {e}")


    # Streamlit GUI
    st.title("👨‍💻 Mail for the Admin")
    st.markdown("Use this form to send an email to the admin.")

    mymail = ""
    password = ""  # Replace with your app password

    subject = st.text_input("Subject", "", placeholder="Enter your subject here...")
    id_field = st.text_input("ID", "", placeholder="Enter proper ID here...")
    content = st.text_area("Content", "", placeholder="Enter your message here...")

    if st.button("Send Email"):
        with st.spinner("Sending email..."):
            if send_email_with_attachment(mymail, password, subject, content, id_field):
                st.success("Email with attachment sent successfully!")