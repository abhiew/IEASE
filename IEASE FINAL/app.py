from flask import Flask, render_template, Response, jsonify, request, redirect, url_for, flash
import cv2
import numpy as np
from mediapipe.python.solutions import hands, drawing_utils
import google.generativeai as genai
from dotenv import load_dotenv
import os
from PIL import Image
import base64
from io import BytesIO
import pandas as pd
from arranger import check_format, arrange, assign_faculties

load_dotenv()

app = Flask(__name__)
app.secret_key = "supersecretkey"  # Required for flashing messages

# Global variables for Air Canvas
canvas = None

# Global variables for Exam Management
rooms_details = []
student_details = []
faculty_list = []

# Ensure the "data" folder exists
if not os.path.exists("data"):
    os.makedirs("data")

# Air Canvas Class
class AirCanvas:
    def __init__(self):
        # Initialize webcam
        self.cap = cv2.VideoCapture(0)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 950)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 550)

        # Get the actual frame size from the webcam
        self.frame_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.frame_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        # Initialize canvas with the same dimensions as the webcam frame
        self.imgCanvas = np.zeros((self.frame_height, self.frame_width, 3), dtype=np.uint8)

        # Initialize MediaPipe Hands
        self.mphands = hands.Hands(max_num_hands=1, min_detection_confidence=0.75)

        # Initialize drawing variables
        self.p1, self.p2 = 0, 0  # Previous points for drawing
        self.fingers = []  # To track finger states
        self.drawing_mode = "free"  # Current drawing mode
        self.color = (255, 0, 255)  # Default drawing color (magenta)

    def identify_fingers(self):
        self.fingers = []
        if self.landmark_list:
            for id in [4, 8, 12, 16, 20]:  # Thumb, Index, Middle, Ring, Pinky
                if id != 4:  # For fingers other than thumb
                    if self.landmark_list[id][2] < self.landmark_list[id - 2][2]:
                        self.fingers.append(1)  # Finger is open
                    else:
                        self.fingers.append(0)  # Finger is closed
                else:  # For thumb
                    if self.landmark_list[id][1] < self.landmark_list[id - 2][1]:
                        self.fingers.append(1)  # Thumb is open
                    else:
                        self.fingers.append(0)  # Thumb is closed

    def handle_drawing(self):
        if sum(self.fingers) == 1 and self.fingers[1] == 1:  # Index finger up (freehand)
            cx, cy = self.landmark_list[8][1], self.landmark_list[8][2]  # Index finger tip
            if self.p1 == 0 and self.p2 == 0:
                self.p1, self.p2 = cx, cy
            cv2.line(self.imgCanvas, (self.p1, self.p2), (cx, cy), self.color, 5)
            self.p1, self.p2 = cx, cy

        elif sum(self.fingers) == 2 and self.fingers[1] == self.fingers[2] == 1:  # Stop freehand drawing
            self.p1, self.p2 = 0, 0  # Reset previous points to stop drawing

        elif sum(self.fingers) == 3 and self.fingers[1] == self.fingers[2] == self.fingers[3] == 1:  # Square
            cx1, cy1 = self.landmark_list[8][1], self.landmark_list[8][2]  # Index finger
            cx2, cy2 = self.landmark_list[12][1], self.landmark_list[12][2]  # Middle finger
            cv2.rectangle(self.imgCanvas, (cx1, cy1), (cx2, cy2), self.color, 5)

        elif sum(self.fingers) == 4 and self.fingers[1] == self.fingers[2] == self.fingers[3] == self.fingers[4] == 1:  # Circle
            cx, cy = self.landmark_list[8][1], self.landmark_list[8][2]  # Index finger
            radius = int(np.hypot(self.landmark_list[8][1] - self.landmark_list[12][1],
                                  self.landmark_list[8][2] - self.landmark_list[12][2]))
            cv2.circle(self.imgCanvas, (cx, cy), radius, self.color, 5)

        elif sum(self.fingers) == 0:  # Closed fist (erase)
            cx, cy = self.landmark_list[8][1], self.landmark_list[8][2]
            cv2.circle(self.imgCanvas, (cx, cy), 20, (0, 0, 0), -1)  # Erase with black circle

    def generate_frames(self):
        while True:
            success, img = self.cap.read()
            if not success:
                print("Failed to read frame from webcam")  # Debugging
                break

            # Flip the image horizontally for a mirror effect
            img = cv2.flip(img, 1)

            # Resize imgCanvas to match the webcam frame size
            if self.imgCanvas.shape[:2] != img.shape[:2]:
                self.imgCanvas = cv2.resize(self.imgCanvas, (img.shape[1], img.shape[0]))

            # Convert BGR to RGB for MediaPipe
            self.imgRGB = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

            # Process hand landmarks
            result = self.mphands.process(self.imgRGB)
            self.landmark_list = []

            if result.multi_hand_landmarks:
                for hand_lms in result.multi_hand_landmarks:
                    drawing_utils.draw_landmarks(img, hand_lms, hands.HAND_CONNECTIONS)
                    for id, lm in enumerate(hand_lms.landmark):
                        h, w, c = img.shape
                        cx, cy = int(lm.x * w), int(lm.y * h)
                        self.landmark_list.append([id, cx, cy])

                self.identify_fingers()
                self.handle_drawing()

            # Blend canvas with webcam feed
            img = cv2.addWeighted(img, 0.7, self.imgCanvas, 1, 0)

            # Encode the frame as JPEG
            ret, buffer = cv2.imencode('.jpg', img)
            if not ret:
                print("Failed to encode frame")  # Debugging
                continue

            # Yield the frame as bytes
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')

    def analyze_image_with_genai(self):
        try:
            # Convert canvas to RGB and PIL image
            imgCanvas = cv2.cvtColor(self.imgCanvas, cv2.COLOR_BGR2RGB)
            imgCanvas = Image.fromarray(imgCanvas)

            # Encode image as base64
            buffered = BytesIO()
            imgCanvas.save(buffered, format="PNG")
            img_base64 = base64.b64encode(buffered.getvalue()).decode("utf-8")

            # Configure Generative AI
            genai.configure(api_key=os.getenv('GEMINI_API_KEY'))  # Use the correct environment variable
            model = genai.GenerativeModel('gemini-pro')  # Use 'gemini-pro' for text-based analysis

            # Generate content
            prompt = f"Analyze the image (encoded as base64) and provide the following:\n" \
                     f"* The mathematical equation / question represented in the image.\n" \
                     f"* The solution to the equation / question.\n" \
                     f"* A short and sweet explanation of the steps taken to arrive at the solution.\n" \
                     f"Image (base64): {img_base64}"
            response = model.generate_content(prompt)

            print("Analysis successful")  # Debugging
            return response.text
        except Exception as e:
            print(f"Error in Generative AI analysis: {e}")  # Debugging
            return "Analysis failed"

# Routes for Air Canvas
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/air_canvas')
def air_canvas():
    return render_template('air_canvas.html')

@app.route('/video_feed')
def video_feed():
    global canvas
    if canvas is None:
        canvas = AirCanvas()  # Initialize the canvas if it doesn't exist
    return Response(canvas.generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/check_analysis')
def check_analysis():
    global canvas
    if canvas is None:
        canvas = AirCanvas()  # Initialize the canvas if it doesn't exist
    analysis_result = canvas.analyze_image_with_genai()
    return jsonify({"analysis": analysis_result})

@app.route('/set_mode')
def set_mode():
    global canvas
    if canvas is None:
        canvas = AirCanvas()  # Initialize the canvas if it doesn't exist
    mode = request.args.get('mode')
    canvas.drawing_mode = mode
    return jsonify({"status": "success", "mode": mode})

@app.route('/reset_canvas')
def reset_canvas():
    global canvas
    if canvas is None:
        canvas = AirCanvas()  # Initialize the canvas if it doesn't exist
    canvas.imgCanvas = np.zeros((canvas.frame_height, canvas.frame_width, 3), dtype=np.uint8)
    return jsonify({"status": "success"})

# Routes for Exam Management
@app.route('/exam_management')
def exam_management():
    return render_template('exam_management.html')

@app.route('/add_room', methods=['POST'])
def add_room():
    if request.method == 'POST':
        room_no = request.form.get("room_no")
        benches = request.form.get("benches")
        rows = request.form.get("rows")
        columns = request.form.get("columns")

        # Validate room details
        if not all([room_no, benches, rows, columns]):
            flash("All fields are required!", "error")
        else:
            try:
                room = {
                    "room_no": room_no,  # Room number as a string
                    "benches": int(benches),
                    "rows": int(rows),
                    "columns": int(columns),
                }

                # Check if the room number already exists
                for rd in rooms_details:
                    if rd["room_no"] == room["room_no"]:
                        flash("This room number already exists!", "error")
                        return redirect(url_for('exam_management'))

                rooms_details.append(room)
                flash("Room added successfully!", "success")

            except ValueError:
                flash("Invalid input for benches, rows, or columns!", "error")

    return redirect(url_for('exam_management'))

@app.route('/add_student_file', methods=['POST'])
def add_student_file():
    if request.method == 'POST':
        file = request.files["student_csv_file"]
        if file.filename == "":
            flash("No file selected!", "error")
        else:
            file_path = os.path.join("data", file.filename)
            file.save(file_path)

            # Validate the CSV file
            message = check_format(file_path)
            if message != "correct":
                flash(message, "error")
            else:
                temp_df = pd.read_csv(file_path)
                dep = temp_df["roll number"][0][:2]

                # Check if the department already exists
                if any(sd["roll number"][0][:2] == dep for sd in student_details):
                    flash(f"{dep}'s CSV already added!", "error")
                else:
                    student_details.append(temp_df)
                    flash(f"Student file {file.filename} added successfully!", "success")

    return redirect(url_for('exam_management'))

@app.route('/add_faculty_file', methods=['POST'])
def add_faculty_file():
    if request.method == 'POST':
        file = request.files["faculty_csv_file"]
        if file.filename == "":
            flash("No file selected!", "error")
        else:
            file_path = os.path.join("data", file.filename)
            file.save(file_path)

            # Read the faculty CSV file
            faculty_df = pd.read_csv(file_path)
            if "name" not in faculty_df.columns:
                flash("Faculty CSV must contain a 'name' column!", "error")
            else:
                global faculty_list
                faculty_list = faculty_df["name"].tolist()
                flash(f"Faculty file {file.filename} added successfully!", "success")

    return redirect(url_for('exam_management'))

@app.route('/generate_arrangement')
def generate_arrangement():
    # Generate the seating arrangement
    if not rooms_details or not student_details:
        flash("Please add rooms and student details first!", "error")
        return redirect(url_for('exam_management'))

    if not faculty_list:
        flash("Please upload the faculty list!", "error")
        return redirect(url_for('exam_management'))

    rooms_details.sort(key=lambda r: r["room_no"])
    arrangement = arrange(student_details, rooms_details)

    if not arrangement:
        flash("Insufficient benches for all students!", "error")
        return redirect(url_for('exam_management'))

    # Assign faculties to rooms
    faculties_assigned = assign_faculties(arrangement, faculty_list)

    # Pass the arrangement, faculties, and enumerate function to the template
    return render_template(
        "result.html",
        arrangement=arrangement,
        rooms_details=rooms_details,
        faculties_assigned=faculties_assigned,
        enumerate=enumerate  # Pass the enumerate function
    )

@app.route('/clear_data')
def clear_data():
    global rooms_details, student_details, faculty_list
    rooms_details = []  # Clear room details
    student_details = []  # Clear student details
    faculty_list = []  # Clear faculty list
    flash("All data cleared successfully!", "success")
    return redirect(url_for('exam_management'))

if __name__ == '__main__':
    app.run(debug=True)