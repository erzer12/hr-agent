"""
HR AI Agent Backend - Flask API Server
Handles resume processing and interview scheduling requests
"""

from flask import Flask, request, jsonify, Response
from flask_cors import CORS
import os
import tempfile
import logging
import requests
import time
import ssl
from typing import Callable, Any
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


def allowed_file(filename: str) -> bool:
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def error_response(message: str, code: int = 400) -> Response:
    logger.error(message)
    return jsonify({"error": message}), code

def save_uploaded_files(files) -> list:
    saved_files = []
    for file in files:
        if file and file.filename and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            saved_files.append(filepath)
            logger.info(f"Saved resume: {filename}")
    return saved_files

# ---------------------------
# Retry helper for upstream network/SSL issues
# ---------------------------
def call_with_retries(
    fn: Callable[..., Any],
    *args,
    retries: int = 3,
    backoff_factor: float = 1.0,
    allowed_exceptions=(ssl.SSLError, requests.exceptions.RequestException, OSError),
    **kwargs
) -> Any:
    """
    Call fn(*args, **kwargs) and retry on certain transient exceptions (SSL/socket/http).
    Exponential backoff: backoff_factor * (2 ** attempt)
    """
    attempt = 0
    while True:
        try:
            return fn(*args, **kwargs)
        except allowed_exceptions as e:
            attempt += 1
            if attempt > retries:
                logger.exception("Max retries reached for network/SSL error")
                raise
            sleep_for = backoff_factor * (2 ** (attempt - 1))
            logger.warning(
                f"Transient network/SSL error: {e!r}. Retrying {attempt}/{retries} after {sleep_for}s..."
            )
            time.sleep(sleep_for)
        except Exception:
            # Non-network error -> re-raise immediately
            raise

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
            return error_response("Job description is required")
        if 'resumes' not in request.files:
            return error_response("No resume files uploaded")

        job_description = request.form['job_description']
        uploaded_files = request.files.getlist('resumes')
        if not job_description.strip():
            return error_response("Job description cannot be empty")

        saved_files = save_uploaded_files(uploaded_files)
        if not saved_files:
            return error_response("No valid PDF files found")

        logger.info(f"Processing {len(saved_files)} resumes against job description")

        # resume processing usually doesn't involve calendar calls, but protect anyway
        result = call_with_retries(hr_crew.process_resumes, job_description, saved_files)
        return jsonify(result)
    except ssl.SSLError as e:
        logger.exception("SSL error while processing resumes")
        return error_response("Upstream SSL/network error while processing resumes", 502)
    except requests.exceptions.RequestException as e:
        logger.exception("Network error while processing resumes")
        return error_response("Upstream network error while processing resumes", 502)
    except Exception as e:
        logger.exception("Error processing resumes")
        return error_response(f"Internal server error: {str(e)}", 500)
    finally:
        # cleanup
        for file in locals().get('saved_files', []):
            try:
                os.remove(file)
                logger.info(f"Deleted temp file: {file}")
            except Exception as cleanup_err:
                logger.warning(f"Failed to delete temp file {file}: {cleanup_err}")

@app.route('/api/draft_email', methods=['POST'])
def draft_email() -> Response:
    try:
        data = request.get_json()
        if not data or 'candidate' not in data or 'interview_details' not in data:
            return error_response("Candidate and interview_details are required")

        draft = call_with_retries(hr_crew.draft_email, data['candidate'], data['interview_details'])
        return jsonify({"draft": draft})
    except ssl.SSLError:
        logger.exception("SSL error while drafting email")
        return error_response("Upstream SSL/network error while drafting email", 502)
    except Exception as e:
        logger.exception("Error drafting email")
        return error_response("Internal server error occurred while drafting email", 500)

@app.route('/api/calendar', methods=['GET'])
def get_calendar() -> Response:
    try:
        calendar_url = call_with_retries(hr_crew.get_calendar_url)
        if not calendar_url:
            return error_response("Could not fetch calendar URL", 500)
        return jsonify({"calendar_url": calendar_url})
    except ssl.SSLError as e:
        logger.exception("SSL error while fetching calendar URL")
        return error_response("Google Calendar API SSL error. Check network/proxy/VPN.", 502)
    except requests.exceptions.RequestException as re:
        logger.error(f"Google Calendar API network error: {str(re)}")
        return error_response("Google Calendar API unreachable. Check internet connection.", 502)
    except Exception as e:
        logger.exception("Error getting calendar URL")
        return error_response("Internal server error occurred while getting calendar URL", 500)

@app.route('/api/availability', methods=['GET'])
def get_availability() -> Response:
    try:
        # Protect the call to get_available_slots with retries/backoff for transient SSL errors.
        slots = call_with_retries(hr_crew.get_available_slots)
        return jsonify(slots)
    except ssl.SSLError as e:
        logger.exception("SSL error while getting availability")
        return error_response("Google Calendar API SSL error while fetching availability", 502)
    except requests.exceptions.RequestException as re:
        logger.error(f"Google Calendar API network error: {str(re)}")
        return error_response("Google Calendar API unreachable. Check internet connection.", 502)
    except Exception as e:
        logger.exception("Error getting availability")
        return error_response("Internal server error occurred while getting availability", 500)

@app.route('/api/schedule', methods=['POST'])
def schedule_interview() -> Response:
    try:
        data = request.get_json()
        if not data or 'candidate' not in data or 'start_time' not in data or 'end_time' not in data:
            return error_response("Candidate, start_time and end_time are required")
        candidate = data['candidate']
        if not isinstance(candidate, dict) or 'name' not in candidate or 'email' not in candidate:
            return error_response("Candidate must have name and email")
        logger.info(f"Scheduling interview for {candidate['name']} at {data['start_time']}")

        result = call_with_retries(hr_crew.schedule_interview, candidate, data['start_time'], data['end_time'])
        return jsonify(result)
    except ssl.SSLError:
        logger.exception("SSL error while scheduling interview")
        return error_response("Google Calendar API SSL error while scheduling interview", 502)
    except Exception as e:
        logger.exception("Error scheduling interview")
        return error_response("Internal server error occurred while scheduling interview", 500)

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

    # Initialize HR agent (protect initialization)
    try:
        hr_crew = HRAgentCrew()
    except Exception as e:
        logger.exception("Failed to initialize HRAgentCrew")
        print("Error: Failed to initialize HRAgentCrew. See logs for details.")
        exit(1)

    # Validate env vars - REMOVED 'GOOGLE_CALENDAR_CREDENTIALS_PATH'
    required_vars = ['GOOGLE_API_KEY']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        logger.error(f"Missing required environment variables: {missing_vars}")
        print(f"Error: Missing required environment variables: {missing_vars}")
        exit(1)

    # Quick connectivity check (optional) - use short timeout and catch SSL errors
    try:
        requests.get("https://www.googleapis.com", timeout=10)
        logger.info("Google API reachable ✅")
    except requests.exceptions.SSLError as e:
        logger.warning(f"Google API SSL warning: {e}")
    except Exception as e:
        logger.warning(f"Google API not reachable: {e}")

    logger.info("Starting HR AI Agent API server...")
    # Note: in production, use a proper WSGI server like gunicorn/uvicorn
    app.run(debug=True, host='0.0.0.0', port=5000)
