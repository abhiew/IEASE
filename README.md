# IEASE - Interactive Education And Seamless Exam Management

## Overview

IEASE (Interactive Education And Seamless Exam Management) is a comprehensive web application designed to enhance the educational experience by providing interactive tools for learning and efficient management of exam-related tasks. The project integrates two main features: **Air Canvas** for interactive learning and **Exam Management** for seamless exam organization.

## Features

### 1. **Air Canvas**
   - **Interactive Drawing**: Users can draw in the air using hand gestures captured via a webcam. The system recognizes hand movements and translates them into drawings on a virtual canvas.
   - **Gesture Recognition**: The application uses MediaPipe's hand tracking to detect and interpret hand gestures, allowing users to draw shapes like circles, squares, and freehand lines.
   - **Real-Time Feedback**: The canvas updates in real-time, providing immediate visual feedback as users draw.
   - **AI-Powered Analysis**: The drawn content can be analyzed using Google's Generative AI (Gemini) to provide solutions and explanations for mathematical equations or questions drawn on the canvas.
   - **Customizable Drawing Modes**: Users can switch between different drawing modes (e.g., freehand, shapes) and reset the canvas as needed.

### 2. **Exam Management**
   - **Room Management**: Administrators can add exam rooms with details such as room number, number of benches, rows, and columns.
   - **Student Data Upload**: Student details can be uploaded via CSV files, which are validated to ensure correct formatting and department consistency.
   - **Faculty Assignment**: Faculty members can be assigned to exam rooms based on the number of students in each room. The system automatically assigns faculties, ensuring proper supervision.
   - **Seating Arrangement Generation**: The system generates a seating arrangement for students across multiple rooms, ensuring optimal utilization of space and resources.
   - **Data Clearing**: Administrators can clear all uploaded data (rooms, students, and faculties) to start fresh.

## Technologies Used

- **Frontend**: HTML, CSS, JavaScript
- **Backend**: Python (Flask)
- **Computer Vision**: OpenCV, MediaPipe
- **AI Integration**: Google Generative AI (Gemini)
- **Data Handling**: Pandas
- **Environment Management**: Python-dotenv

## Installation

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/your-repo/IEASE.git
   cd IEASE
   ```

2. **Set Up a Virtual Environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Set Up Environment Variables**:
   - Create a `.env` file in the root directory.
   - Add your Google Generative AI API key:
     ```plaintext
     GEMINI_API_KEY=your_api_key_here
     ```

5. **Run the Application**:
   ```bash
   python app.py
   ```
   The application will be available at `http://127.0.0.1:5000`.

## Usage

### Air Canvas
- Access the Air Canvas feature by navigating to the **Air Canvas** section from the homepage.
- Use your hand gestures to draw on the virtual canvas.
- Press `Enter` to analyze the drawing using AI or press `R` to reset the canvas.

### Exam Management
- Navigate to the **Exam Management** section from the homepage.
- Add room details, upload student and faculty CSV files, and generate seating arrangements.
- The system will automatically assign faculties and display the seating arrangement for each room.

## File Structure

- **app.py**: Main Flask application file containing routes and logic for Air Canvas and Exam Management.
- **arranger.py**: Contains functions for validating CSV files, generating seating arrangements, and assigning faculties.
- **templates/**: Contains HTML templates for the web pages.
- **static/**: Contains CSS files and images used in the frontend.
- **data/**: Directory for storing uploaded CSV files.
- **requirements.txt**: Lists all Python dependencies required for the project.

## CSV File Formats

### Student CSV File
- **Required Columns**: `roll number`, `name`
- **Example**:
  ```csv
  roll number,name
  CE01,ABHINAND
  CE02,ADAM
  ```

### Faculty CSV File
- **Required Columns**: `name`
- **Example**:
  ```csv
  name
  Dr. Smith
  Dr. Johnson
  ```

## Contributing

Contributions are welcome! Please fork the repository and submit a pull request with your changes.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Acknowledgments

- **MediaPipe**: For hand tracking and gesture recognition.
- **Google Generative AI**: For providing AI-powered analysis of drawn content.
- **Flask**: For building the web application.

---

**IEASE** is designed to make education more interactive and exam management more efficient. Whether you're a student, teacher, or administrator, IEASE provides the tools you need to succeed.