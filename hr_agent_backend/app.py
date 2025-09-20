"""
HR AI Agent Backend - Flask API Server
Handles resume processing and interview scheduling requests
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import tempfile
import logging
import requests
from optimized_agents import HRAgentCrew
from werkzeug.utils import secure_filename

# Initialize Flask app
app = Flask(__name__)
CORS(app, origins=["http://localhost:5173", "http://localhost:3000", "http://localhost:5174"])

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
UPLOAD_FOLDER = tempfile.mkdtemp()
ALLOWED_EXTENSIONS = {'pdf'}
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# ---------------------------
# ROUTES
# ---------------------------

@app.route('/')
def root():
    """Root endpoint for quick checks"""
    return jsonify({"status": "running", "message": "HR AI Agent Backend active"})

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "message": "HR AI Agent API is running"})

@app.route('/api/process', methods=['POST'])
def process_resumes():
    try:
        if 'job_description' not in request.form:
            return jsonify({"error": "Job description is required"}), 400

        if 'resumes' not in request.files:
            return jsonify({"error": "No resume files uploaded"}), 400

        job_description = request.form['job_description']
        uploaded_files = request.files.getlist('resumes')

        if not job_description.strip():
            return jsonify({"error": "Job description cannot be empty"}), 400

        saved_files = []
        for file in uploaded_files:
            if file and file.filename and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
                saved_files.append(filepath)
                logger.info(f"Saved resume: {filename}")

        if not saved_files:
            return jsonify({"error": "No valid PDF files found"}), 400

        logger.info(f"Processing {len(saved_files)} resumes against job description")

        result = hr_crew.process_resumes(job_description, saved_files)

        # cleanup
        for filepath in saved_files:
            try:
                os.remove(filepath)
            except OSError:
                logger.warning(f"Could not remove file: {filepath}")

        logger.info(f"Successfully processed {len(result['candidates'])} candidates")
        return jsonify(result)

    except Exception as e:
        logger.error(f"Error processing resumes: {str(e)}")
        return jsonify({"error": "Internal server error occurred while processing resumes"}), 500

@app.route('/api/draft_email', methods=['POST'])
def draft_email():
    try:
        data = request.get_json()
        if not data or 'candidate' not in data or 'interview_details' not in data:
            return jsonify({"error": "Candidate and interview_details are required"}), 400

        draft = hr_crew.draft_email(data['candidate'], data['interview_details'])
        return jsonify({"draft": draft})

    except Exception as e:
        logger.error(f"Error drafting email: {str(e)}")
        return jsonify({"error": "Internal server error occurred while drafting email"}), 500

@app.route('/api/calendar', methods=['GET'])
def get_calendar():
    try:
        calendar_url = hr_crew.get_calendar_url()
        if not calendar_url:
            return jsonify({"error": "Could not fetch calendar URL"}), 500
        return jsonify({"calendar_url": calendar_url})
    except requests.exceptions.RequestException as re:
        logger.error(f"Google Calendar API network error: {str(re)}")
        return jsonify({"error": "Google Calendar API unreachable. Check internet connection."}), 502
    except Exception as e:
        logger.error(f"Error getting calendar URL: {str(e)}")
        return jsonify({"error": "Internal server error occurred while getting calendar URL"}), 500

@app.route('/api/availability', methods=['GET'])
def get_availability():
    try:
        slots = hr_crew.get_available_slots()
        return jsonify(slots)
    except requests.exceptions.RequestException as re:
        logger.error(f"Google Calendar API network error: {str(re)}")
        return jsonify({"error": "Google Calendar API unreachable. Check internet connection."}), 502
    except Exception as e:
        logger.error(f"Error getting availability: {str(e)}")
        return jsonify({"error": "Internal server error occurred while getting availability"}), 500

@app.route('/api/schedule', methods=['POST'])
def schedule_interview():
    try:
        data = request.get_json()
        if not data or 'candidate' not in data or 'start_time' not in data or 'end_time' not in data:
            return jsonify({"error": "Candidate, start_time and end_time are required"}), 400

        candidate = data['candidate']
        if not isinstance(candidate, dict) or 'name' not in candidate or 'email' not in candidate:
            return jsonify({"error": "Candidate must have name and email"}), 400

        logger.info(f"Scheduling interview for {candidate['name']} at {data['start_time']}")
        result = hr_crew.schedule_interview(candidate, data['start_time'], data['end_time'])
        return jsonify(result)

    except Exception as e:
        logger.error(f"Error scheduling interview: {str(e)}")
        return jsonify({"error": "Internal server error occurred while scheduling interview"}), 500

# ---------------------------
# ERROR HANDLERS
# ---------------------------

@app.errorhandler(413)
def too_large(e):
    return jsonify({"error": "File too large. Maximum size is 16MB per file."}), 413

@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Endpoint not found"}), 404

@app.errorhandler(500)
def internal_error(e):
    return jsonify({"error": "Internal server error"}), 500

# ---------------------------
# MAIN
# ---------------------------
if __name__ == '__main__':
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)

    from dotenv import load_dotenv
    load_dotenv()

    # Initialize HR agent
    hr_crew = HRAgentCrew()

    # Validate env vars - REMOVED 'GOOGLE_CALENDAR_CREDENTIALS_PATH'
    required_vars = ['GOOGLE_API_KEY']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        logger.error(f"Missing required environment variables: {missing_vars}")
        print(f"Error: Missing required environment variables: {missing_vars}")
        exit(1)

    # Quick connectivity check (optional)
    try:
        requests.get("https://www.googleapis.com", timeout=5)
        logger.info("Google API reachable ✅")
    except Exception as e:
        logger.warning(f"Google API not reachable: {e}")

    logger.info("Starting HR AI Agent API server...")
    app.run(debug=True, host='0.0.0.0', port=5000)
