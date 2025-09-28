# HR AI Agent - Autonomous Resume Screening & Interview Scheduling

A complete full-stack web application that automates the initial hiring process through AI-powered resume screening, candidate ranking, and automated interview scheduling with email notifications.

## 🚀 Project Overview

This application streamlines HR workflows by:
- **Autonomously screening** uploaded resumes against job descriptions
- **Ranking candidates** based on qualification match scores (1-10 scale)
- **Scheduling interviews** automatically via Google Calendar integration
- **Sending personalized confirmation emails** to selected candidates

The system uses Google Gemini API for efficient resume parsing and analysis, with optimized token usage for cost-effective operation.

## 🛠️ Tech Stack
Frontend: React, Vite, Tailwind CSS
Backend: Flask, Python
APIs and Services: Gemini API, Google Calendar API, Gmail API (via SMTP)

## 🏗️ System Architecture

The application is composed of a React frontend and a Flask backend. The backend is where the core AI agent logic resides.

```
┌─────────────────┐    HTTP/JSON    ┌─────────────────┐   Gemini API ┌─────────────────┐
│   React Frontend│ ──────────────► │  Flask Backend  │ ──────────► │ Resume Parser   │
│                 │                 │                 │             │                 │
│ • Job Input     │                 │ • /api/process  │             │ • ResumeScreener│
│ • File Upload   │                 │ • /api/schedule │             │ • InterviewSched│
│ • Candidate UI  │                 │                 │             │ • Score & Rank  │
└─────────────────┘                 └─────────────────┘             └─────────────────┘
                                           │                               │
                                           ▼                               ▼
                                    ┌─────────────────┐            ┌─────────────────┐
                                    │ External APIs   │            │ Custom Tools    │
                                    │                 │            │                 │
                                    │ • Gemini API    │            │ • PDF Extractor │
                                    │ • Google Cal    │            │ • Calendar Tool │
                                    │ • SMTP/Email    │            │ • Email Sender  │
                                    └─────────────────┘            └─────────────────┘
```

### Frontend

The frontend is a single-page application built with React and Vite. It provides a user interface for:
- Entering a job description.
- Uploading resumes (in PDF format).
- Viewing a ranked list of candidates.
- Selecting candidates for interviews.

### Backend

The backend is a Flask application that exposes a REST API for the frontend. It's responsible for:
- Processing the job description and resumes.
- Calling the Google Gemini API to analyze and rank candidates.
- Scheduling interviews using the Google Calendar API.
- Sending email notifications.

### Agent Architecture and Flow

The core of the application is the AI agent system in the backend. The agent is designed to be modular and extensible. The main components are:

1.  **`app.py`**: The main entry point for the Flask application. It defines the API endpoints and orchestrates the overall workflow.
2.  **`agents.py`**: This file contains the core agent logic. The `ResumeScreenerAgent` is responsible for taking the job description and resumes, and then using the `gemini_parser` to analyze and rank the candidates.
3.  **`gemini_parser.py`**: This module interacts directly with the Google Gemini API. It's responsible for constructing the prompts, sending them to the API, and parsing the JSON responses. It's optimized for token efficiency by using truncated inputs and structured prompts.
4.  **`tools.py`**: This file contains a collection of tools that the agent can use. These tools are simple Python functions that perform specific tasks, such as:
    - `pdf_text_extractor`: Extracts text from PDF files.
    - `GoogleCalendarTool`: A tool for finding available slots and creating events in Google Calendar.
    - `send_email`: A tool for sending emails.

The agent flow is as follows:

1.  The user uploads a job description and resumes through the React frontend.
2.  The frontend sends a POST request to the `/api/process` endpoint on the Flask backend.
3.  The `app.py` receives the request and calls the `ResumeScreenerAgent` in `agents.py`.
4.  The `ResumeScreenerAgent` uses the `pdf_text_extractor` tool to extract the text from the resumes.
5.  The agent then calls the `gemini_parser` to send the job description and resume text to the Google Gemini API.
6.  The Gemini API returns a ranked list of candidates with scores and summaries.
7.  The `ResumeScreenerAgent` returns the ranked list to the `app.py`.
8.  The `app.py` sends the ranked list back to the frontend, which displays it to the user.
9.  The user selects candidates for interviews and clicks the "Schedule Interviews" button.
10. The frontend sends a POST request to the `/api/schedule` endpoint with the selected candidates.
11. The `app.py` receives the request and uses the `GoogleCalendarTool` to find available interview slots.
12. The `app.py` then uses the `GoogleCalendarTool` to create the interview events and the `send_email` tool to send confirmation emails to the candidates.

## 📋 Prerequisites

### Software Requirements
- **Python 3.9+** - Backend runtime
- **Node.js 16+** - Frontend development
- **npm/yarn** - Package management

### API Account Requirements
- **Google AI API Access** - Google Gemini API key
- **Google Cloud Project** - For Calendar API
- **Gmail Account** - For email notifications (with app passwords enabled)

## 📸 Screenshots
- ### Frontend UI
   <img width="1900" height="796" alt="Screenshot 2025-09-26 001146" src="https://github.com/user-attachments/assets/f4d6bd8d-1fd2-4976-98c2-1f5ef137ef74" />
  
- ### Ranked Candidates Output
   <img width="1605" height="769" alt="Screenshot 2025-09-28 120232" src="https://github.com/user-attachments/assets/3da939c6-e509-4844-a180-c1dcf9a3e03a" />

 - ### Gemini Resume Parsing in console
   <img width="1391" height="694" alt="Screenshot 2025-09-26 002643" src="https://github.com/user-attachments/assets/86320832-6f9e-4fac-a81b-766e2c8ee8cb" />

- ### Interview Scheduler
  - #### Bulk Scheduler
    <img width="1602" height="766" alt="Screenshot 2025-09-28 120321" src="https://github.com/user-attachments/assets/3e56f249-d449-4437-9c20-5b8be311f3cc" />
  
  - #### Single Scheduler
    <img width="1602" height="771" alt="Screenshot 2025-09-28 120421" src="https://github.com/user-attachments/assets/754b8237-168e-4872-a10e-892120e9a40d" />

 - ### Frontend Calender
    <img width="1265" height="590" alt="Screenshot 2025-09-28 120528" src="https://github.com/user-attachments/assets/089b9ffc-8ade-4812-af1b-042f7ab98b30" />


- ### Google Calendar Event
  <img width="1627" height="756" alt="Screenshot 2025-09-28 120557" src="https://github.com/user-attachments/assets/08287129-7927-413d-b76c-e37eef86de23" />

- ### Google Meet Setup
  <img width="1617" height="767" alt="Screenshot 2025-09-28 130406" src="https://github.com/user-attachments/assets/65ed9e13-0e32-4ab0-894c-ead73c61226f" />

- ### Email Inbox
  <img width="1781" height="805" alt="Screenshot 2025-09-26 001051" src="https://github.com/user-attachments/assets/88bf61ab-7db0-433f-a0f6-afad0a52c947" />



## ⚙️ Setup and Installation

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/hr-agent.git
cd hr-agent
```

### 2. Backend Setup

```bash
# Navigate to the backend directory
cd hr_agent_backend

# Create a Python virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install Python dependencies
pip install -r requirements.txt
```

### 3. Frontend Setup

```bash
# Return to the root directory
cd ..

# Install npm dependencies
npm install
```

### 4. Environment Configuration

#### Backend Environment (`.env` file)

Create a `.env` file in the `hr_agent_backend` directory by copying the example file:

```bash
cd hr_agent_backend
cp .env.example .env
```

Edit the `.env` file with your actual credentials:

```env
# Google Gemini API Configuration
GOOGLE_API_KEY=your-google-ai-key

# Google Calendar API
GOOGLE_CALENDAR_CREDENTIALS_PATH=credentials.json
GOOGLE_CALENDAR_TOKEN_PATH=token.json

# Email Configuration
EMAIL_ADDRESS=your-email@gmail.com
EMAIL_PASSWORD=your-gmail-app-password
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587

# Company Information
COMPANY_NAME=Your Company Name
INTERVIEWER_NAME=John Smith
INTERVIEWER_EMAIL=john.smith@company.com

# Development Mode (set to 'true' for testing without external APIs)
DEV_MODE=false
```

### 5. Google Calendar API Setup (CRITICAL)

This is the most complex setup step. Follow carefully:

#### Step 1: Create Google Cloud Project
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one.
3. Enable the **Google Calendar API**:
   - Navigate to "APIs & Services" → "Library"
   - Search for "Google Calendar API"
   - Click "Enable"

#### Step 2: Create Credentials
1. Go to "APIs & Services" → "Credentials"
2. Click "Create Credentials" → "OAuth 2.0 Client IDs"
3. Configure the OAuth consent screen if prompted:
   - User Type: External (for testing) or Internal (for your organization)
   - Fill in the required fields (app name, user support email).
   - Add your email to the list of test users.
4. Create the OAuth Client ID:
   - Application type: **Desktop Application**
   - Name: "HR AI Agent"
   - Download the credentials JSON file.

#### Step 3: Setup Credentials
1. Rename the downloaded file to `credentials.json`.
2. Place it in the `hr_agent_backend/` directory.
3. The file structure should look like:
```json
{
  "installed": {
    "client_id": "your-client-id.googleusercontent.com",
    "project_id": "your-project-id",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "client_secret": "your-client-secret",
    "redirect_uris": ["http://localhost"]
  }
}
```

#### Step 4: Initial Authentication
The first time you run the backend, it will:
1. Open a browser window for Google OAuth.
2. Ask you to sign in and grant calendar access.
3. This will generate a `token.pickle` file automatically, which will store your refresh tokens for future API calls.

**Note**: This authentication only needs to be done once.

### 6. Email Setup (Gmail App Passwords)

1. Enable 2-Factor Authentication on your Gmail account.
2. Generate an App Password:
   - Go to your Google Account settings.
   - Navigate to Security → 2-Step Verification → App passwords.
   - Generate a new password for "Mail".
   - Use this app password (not your regular password) in the `.env` file.

### 7. Live Calender Preview
1. Go to the Google Calender for which you took the credentials from. 
2. Click on the "Settings and Sharing" icon (three vertical dots) in the top right corner.
3. Select "Settings" from the dropdown menu.
4. In the "Calendar settings" section, click on "Integrate calendar".
5. You will see a calendar ID. This is the unique identifier for your calendar.
6. Copy this calendar ID and add it to your `.env` file in the `hr_agent_backend` directory.
   - Add the following line to your `.env` file:
     ```env
     GOOGLE_CALENDAR_ID=your-calendar-id
     ```


## 🚀 How to Run

### 1. Start the Backend Server

```bash
cd hr_agent_backend
source venv/Scripts/activate 
python app.py
```

The backend will start on `http://localhost:5000`.

**First Run**: If Google Calendar is not authenticated, the backend will open a browser window for OAuth authentication.

### 2. Start the Frontend Development Server

```bash
# From the project root directory
npm run dev
```

The frontend will start on `http://localhost:5173`.
# 🔧 Development Mode

For development and testing without external API dependencies:

```env
# Set in .env file
DEV_MODE=true
```

This enables:
- Mock PDF text extraction
- Mock calendar scheduling  
- Mock email sending
- Simulated processing delays

### . Access the Application

Open `http://localhost:3000` in your browser to use the HR AI Agent dashboard.
