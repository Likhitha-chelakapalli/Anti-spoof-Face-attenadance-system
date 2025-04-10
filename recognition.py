from  database_management import mark_attendance
from deepface_identificatiom import get_user_id
from text_to_speech import text_to_speech,text_to_speech_direct
from Mail_for_attendance import send_email
import cv2
import dlib
from scipy.spatial import distance as dist
import numpy as np
import mysql.connector as mysql
def recognition():

    def getprofile(id):
        db=mysql.connect(
            host='localhost',
            user='root',
            password='1234',
            database='face'
        )
        cmd="Select * from students where id=%s"%id
        mycursor=db.cursor()
        mycursor.execute(cmd)
        row=mycursor.fetchone()
        db.close()
        return row

    def eye_aspect_ratio(eye):
        """
        Calculate the Eye Aspect Ratio (EAR) to detect blinks.
        """
        A = dist.euclidean(eye[1], eye[5])
        B = dist.euclidean(eye[2], eye[4])
        C = dist.euclidean(eye[0], eye[3])
        return (A + B) / (2.0 * C)


    def is_blurry(image, threshold=1800.0):
        """
        Check if the image is blurry based on Laplacian variance.
        """
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
        return laplacian_var < threshold, laplacian_var


    # Load face detector and facial landmarks predictor
    detector = dlib.get_frontal_face_detector()
    predictor = dlib.shape_predictor("shape_predictor_68_face_landmarks.dat")

    # Landmark indices for left and right eyes
    (lStart, lEnd) = (42, 48)
    (rStart, rEnd) = (36, 42)

    cap = cv2.VideoCapture(0)

    while True:
      try:
        ret, frame = cap.read()
        if not ret:
            break

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = detector(gray)

        for face in faces:
            x, y, w, h = face.left(), face.top(), face.width(), face.height()
            cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2)

            landmarks = predictor(gray, face)
            landmarks = [(landmarks.part(i).x, landmarks.part(i).y) for i in range(68)]

            leftEye = landmarks[lStart:lEnd]
            rightEye = landmarks[rStart:rEnd]

            # Draw rectangles around the eyes
            # leftEyeRect = cv2.boundingRect(np.array(leftEye))
            # rightEyeRect = cv2.boundingRect(np.array(rightEye))
            # cv2.rectangle(frame, (leftEyeRect[0], leftEyeRect[1]),
            #               (leftEyeRect[0] + leftEyeRect[2], leftEyeRect[1] + leftEyeRect[3]), (0, 255, 0), 2)
            # cv2.rectangle(frame, (rightEyeRect[0], rightEyeRect[1]),
            #               (rightEyeRect[0] + rightEyeRect[2], rightEyeRect[1] + rightEyeRect[3]), (0, 255, 0), 2)

            # Calculate EAR
            leftEAR = eye_aspect_ratio(leftEye)
            rightEAR = eye_aspect_ratio(rightEye)
            ear = (leftEAR + rightEAR) / 2.0

            # Check for blink detection
            # blink_detected = ear < 0.20

            # Check for blurriness in the face region
            face_region = frame[y:y + h, x:x + w]
            blurry, variance = is_blurry(face_region)
            # print("Blurr:",blurry)
            # print("variance:",variance)

            cv2.putText(frame, f"Keep Face in Middle ", (25, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 1)

            # Determine real or spoof
            if  blurry and ear<0.20: #blink_detected and not blurry:
                # cv2.putText(frame, "Face Detected", (25, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 1)
                id=get_user_id(face_region)
                if id is not None:

                    profile = getprofile(id)
                    if profile != None:
                        if mark_attendance(id):
                            cv2.putText(frame, "Attendence Marked Successfully", (25,60), cv2.FONT_HERSHEY_COMPLEX, 1, (0,255,0), 1)
                            cv2.putText(frame, str(profile[1]).title(), (x-20, y - 20), cv2.FONT_HERSHEY_COMPLEX, 1, (255, 0, 0), 2)
                            cv2.imshow("Frame", frame)
                            cv2.waitKey(2000)
                            send_email(id,profile[1],profile[2])
                            text_to_speech(profile[1])
                        else:
                            cv2.putText(frame, "Attendence Already Marked", (25,60), cv2.FONT_HERSHEY_COMPLEX, 1, (0,255,0), 1)
                            cv2.putText(frame, str(profile[1]).title(), (x-20, y - 20), cv2.FONT_HERSHEY_COMPLEX, 1, (255, 0, 0), 2)
                            cv2.imshow("Frame", frame)
                            cv2.waitKey(2000)
                            text_to_speech_direct("Attendence Already Marked")
                else:
                    cv2.putText(frame, "Trying to Identify", (x-20, y - 20), cv2.FONT_HERSHEY_COMPLEX, 1, (0, 0, 255), 2)
                    cv2.imshow("Frame", frame)
                    cv2.waitKey(2000)

        # Show the frame
        cv2.imshow("Frame", frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break
      except Exception as e:
        print(f"Error during processing: {e}")
    cap.release()
    cv2.destroyAllWindows()
