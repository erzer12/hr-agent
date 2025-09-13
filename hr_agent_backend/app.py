"""
HR AI Agent Backend - Flask API Server
Handles resume processing and interview scheduling requests
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import tempfile
import logging
from optimized_agents import HRAgentCrew
from werkzeug.utils import secure_filename

# Initialize Flask app
app = Flask(__name__)
CORS(app, origins=["http://localhost:5173", "http://localhost:3000"])

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize HR Agent Crew
hr_crew = HRAgentCrew()

# Configuration
UPLOAD_FOLDER = tempfile.mkdtemp()
ALLOWED_EXTENSIONS = {'pdf'}
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "message": "HR AI Agent API is running"})

@app.route('/api/process', methods=['POST'])
def process_resumes():
    """
    Process uploaded resumes against job description
    
    Expected form data:
    - job_description: Text content of the job description
    - resumes: List of PDF files
    
    Returns:
    - JSON array of ranked candidate objects
    """
    try:
        # Validate request
        if 'job_description' not in request.form:
            return jsonify({"error": "Job description is required"}), 400
        
        if 'resumes' not in request.files:
            return jsonify({"error": "No resume files uploaded"}), 400
        
        job_description = request.form['job_description']
        uploaded_files = request.files.getlist('resumes')
        
        if not job_description.strip():
            return jsonify({"error": "Job description cannot be empty"}), 400
        
        if not uploaded_files or len(uploaded_files) == 0:
            return jsonify({"error": "At least one resume file is required"}), 400
        
        # Save uploaded files
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
        
        # Process resumes using AI agents
        result = hr_crew.process_resumes(job_description, saved_files)
        
        # Clean up uploaded files
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

@app.route('/api/schedule', methods=['POST'])
def schedule_interviews():
    """
    Schedule interviews for selected candidates
    
    Expected JSON payload:
    {
        "candidates": [
            {"name": "John Doe", "email": "john@example.com", "phone": "123-456-7890"},
            ...
        ]
    }
    
    Returns:
    - Success message with scheduling details
    """
    try:
        data = request.get_json()
        
        if not data or 'candidates' not in data:
            return jsonify({"error": "Candidates list is required"}), 400
        
        candidates = data['candidates']
        
        if not candidates or len(candidates) == 0:
            return jsonify({"error": "At least one candidate is required"}), 400
        
        # Validate candidate data
        for candidate in candidates:
            if not isinstance(candidate, dict) or 'name' not in candidate or 'email' not in candidate:
                return jsonify({"error": "Each candidate must have name and email"}), 400
        
        logger.info(f"Scheduling interviews for {len(candidates)} candidates")
        
        # Schedule interviews using AI agents
        result = hr_crew.schedule_interviews(candidates)
        
        logger.info("Successfully scheduled interviews and sent confirmation emails")
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error scheduling interviews: {str(e)}")
        return jsonify({"error": "Internal server error occurred while scheduling interviews"}), 500

@app.errorhandler(413)
def too_large(e):
    """Handle file too large error"""
    return jsonify({"error": "File too large. Maximum size is 16MB per file."}), 413

@app.errorhandler(404)
def not_found(e):
    """Handle not found error"""
    return jsonify({"error": "Endpoint not found"}), 404

@app.errorhandler(500)
def internal_error(e):
    """Handle internal server error"""
    return jsonify({"error": "Internal server error"}), 500

if __name__ == '__main__':
    # Ensure upload directory exists
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    # Validate required environment variables
    required_vars = ['LLM_API_KEY', 'GOOGLE_CALENDAR_CREDENTIALS_PATH']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        logger.error(f"Missing required environment variables: {missing_vars}")
        print(f"Error: Missing required environment variables: {missing_vars}")
        print("Please check your .env file and ensure all required variables are set.")
        exit(1)
    
    logger.info("Starting HR AI Agent API server...")
    app.run(debug=True, host='0.0.0.0', port=5000)