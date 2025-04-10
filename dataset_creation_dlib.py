import pymysql as mysql
import dlib
import cv2
def dataset_creation(id_user):

    # Connect to the database
    try:
        conn = mysql.connect(
            host="localhost",
            user="root",
            password="1234",
            database="face"
        )
        cursor = conn.cursor()
    except mysql.Error as err:
        print(f"Error: {err}")
        exit()

    # Create tables if they do not exist
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS students (
        id INT PRIMARY KEY,
        name VARCHAR(255) NOT NULL,
        Email VARCHAR(255) NOT NULL UNIQUE
    )""")

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS attendance (
        student_id INT NOT NULL,
        timestamp DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        attendance_date DATE NOT NULL DEFAULT (CURRENT_DATE),
        UNIQUE(student_id, attendance_date),
        FOREIGN KEY (student_id) REFERENCES students (id) ON DELETE CASCADE
    )""")
    conn.commit()
    conn.close()

    # Load face detector and facial landmarks predictor
    detector = dlib.get_frontal_face_detector()
    cap = cv2.VideoCapture(0)
    sampleNumber=0
    try:
        while True:
            # Capture a frame from the video
            ret, frame = cap.read()
            if not ret:
                print("Error accessing the camera.")
                break

            # Convert the frame to grayscale
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

            # Detect faces in the frame
            faces = detector(gray)

            for face in faces:
                x, y, w, h = face.left(), face.top(), face.width(), face.height()

                # Draw a rectangle around the detected face
                cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2)

                # Display instructions based on the sample count
                if sampleNumber < 6:
                    cv2.putText(frame, "Keep your face close", (20, 20), cv2.FONT_HERSHEY_COMPLEX, 1, (0, 255, 0), 2)
                elif 6 <= sampleNumber <= 12:
                    cv2.putText(frame, "Move left", (20, 20), cv2.FONT_HERSHEY_COMPLEX, 1, (0, 255, 0), 2)
                elif sampleNumber > 12:
                    cv2.putText(frame, "Move right", (20, 20), cv2.FONT_HERSHEY_COMPLEX, 1, (0, 255, 0), 2)

                # Save the grayscale face image
                sampleNumber += 1
                cv2.imwrite(f"dataset/User.{id_user}.{sampleNumber}.jpg", gray[y:y + h, x:x + w])


            # Stop capturing after 20 samples
            if sampleNumber > 20:
                print("Sample collection complete.")
                break

            # Display the video frame with annotations
            cv2.imshow("frame", frame)
            cv2.waitKey(100)
            # Exit on pressing 'q'
            if cv2.waitKey(1) & 0xFF == ord('q'):
                if sampleNumber < 21:
                    return False
                break
    except Exception as e:
        return False

    # Release the camera and close all windows
    cap.release()
    cv2.destroyAllWindows()
    return True
