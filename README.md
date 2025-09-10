# HR AI Agent - Autonomous Resume Screening & Interview Scheduling

A complete full-stack web application that automates the initial hiring process through AI-powered resume screening, candidate ranking, and automated interview scheduling with email notifications.

## 🚀 Project Overview

This application streamlines HR workflows by:
- **Autonomously screening** uploaded resumes against job descriptions
- **Ranking candidates** based on qualification match scores (1-10 scale)
- **Scheduling interviews** automatically via Google Calendar integration
- **Sending personalized confirmation emails** to selected candidates

The system uses specialized AI agents powered by CrewAI framework to handle different aspects of the hiring process, ensuring consistent and objective candidate evaluation.

## 🏗️ System Architecture

```
┌─────────────────┐    HTTP/JSON    ┌─────────────────┐    CrewAI    ┌─────────────────┐
│   React Frontend│ ──────────────► │  Flask Backend  │ ──────────► │   AI Agents     │
│                 │                 │                 │             │                 │
│ • Job Input     │                 │ • /api/process  │             │ • ResumeScreener│
│ • File Upload   │                 │ • /api/schedule │             │ • InterviewSched│
│ • Candidate UI  │                 │                 │             │ • EmailDraftsman│
└─────────────────┘                 └─────────────────┘             └─────────────────┘
                                           │                               │
                                           ▼                               ▼
                                    ┌─────────────────┐            ┌─────────────────┐
                                    │ External APIs   │            │ Custom Tools    │
                                    │                 │            │                 │
                                    │ • LLM APIs      │            │ • PDF Extractor │
                                    │ • Google Cal    │            │ • Calendar Tool │
                                    │ • SMTP/Email    │            │ • Email Sender  │
                                    └─────────────────┘            └─────────────────┘
```

### Data Flow

1. **Upload Phase**: User uploads PDFs and job description through React frontend
2. **Processing Phase**: Flask API triggers AI agents to analyze resumes vs. job requirements
3. **Ranking Phase**: AI generates candidate scores, summaries, and contact information
4. **Selection Phase**: HR user reviews ranked candidates and selects interview candidates
5. **Scheduling Phase**: AI agents find calendar slots and create interview events
6. **Communication Phase**: Automated personalized emails sent to selected candidates

## 📋 Prerequisites

### Software Requirements
- **Python 3.9+** - Backend runtime
- **Node.js 16+** - Frontend development
- **npm/yarn** - Package management

### API Account Requirements
- **LLM API Access** - One of:
  - OpenAI API key (GPT-4)
  - Anthropic API key (Claude)
  - Google AI API key (Gemini)
- **Google Cloud Project** - For Calendar API
- **Gmail Account** - For email notifications (with app passwords enabled)

## ⚙️ Setup and Installation

### 1. Clone and Setup Project Structure

```bash
# Clone the repository (or create the directory structure)
mkdir hr-ai-agent && cd hr-ai-agent

# Create backend directory
mkdir hr_agent_backend
cd hr_agent_backend

# Create Python virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install Python dependencies
pip install -r requirements.txt
```

### 2. Frontend Setup

```bash
# Return to root directory
cd ..

# The React frontend is already configured in src/App.tsx
# Install any additional dependencies if needed
npm install
```

### 3. Environment Configuration

#### Backend Environment (.env file)

Create `hr_agent_backend/.env` file:

```bash
cd hr_agent_backend
cp .env.example .env
```

Edit `.env` with your actual credentials:

```env
# LLM Configuration - Choose ONE
LLM_PROVIDER=openai
LLM_API_KEY=sk-your-openai-key-here

# Alternative LLM options:
# LLM_PROVIDER=anthropic
# ANTHROPIC_API_KEY=your-anthropic-key

# LLM_PROVIDER=google  
# GOOGLE_API_KEY=your-google-ai-key

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

### 4. Google Calendar API Setup (CRITICAL)

This is the most complex setup step. Follow carefully:

#### Step 1: Create Google Cloud Project
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing project
3. Enable the **Google Calendar API**:
   - Navigate to "APIs & Services" → "Library"
   - Search for "Google Calendar API"
   - Click "Enable"

#### Step 2: Create Credentials
1. Go to "APIs & Services" → "Credentials"
2. Click "Create Credentials" → "OAuth 2.0 Client IDs"
3. Configure OAuth consent screen if prompted:
   - User Type: External (for testing) or Internal (for organization)
   - Fill required fields (app name, user support email)
   - Add your email to test users
4. Create OAuth Client ID:
   - Application type: **Desktop Application**
   - Name: "HR AI Agent"
   - Download the credentials JSON file

#### Step 3: Setup Credentials
1. Rename the downloaded file to `credentials.json`
2. Place it in the `hr_agent_backend/` directory
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
1. Open a browser window for Google OAuth
2. Ask you to sign in and grant calendar access
3. Generate a `token.json` file automatically
4. Store refresh tokens for future API calls

**Note**: This authentication only needs to be done once per setup.

### 5. Email Setup (Gmail App Passwords)

1. Enable 2-Factor Authentication on your Gmail account
2. Generate an App Password:
   - Go to Google Account settings
   - Security → 2-Step Verification → App passwords
   - Generate password for "Mail"
   - Use this app password (not your regular password) in `.env`

## 🚀 How to Run

### 1. Start Backend Server

```bash
cd hr_agent_backend
source venv/bin/activate  # On Windows: venv\Scripts\activate
python app.py
```

Backend will start on `http://localhost:5000`

**First Run**: If Google Calendar is not authenticated, the backend will open a browser window for OAuth authentication.

### 2. Start Frontend Development Server

```bash
# From project root directory
npm run dev
```

Frontend will start on `http://localhost:5173`

### 3. Access the Application

Open `http://localhost:5173` in your browser to use the HR AI Agent dashboard.

## 📚 API Endpoints

### Backend API Documentation

#### `POST /api/process`
Process uploaded resumes against job description.

**Request**: Multipart form data
- `job_description` (text): Complete job description
- `resumes` (files): Array of PDF resume files

**Response**: JSON
```json
{
  "candidates": [
    {
      "name": "John Doe",
      "email": "john.doe@email.com", 
      "phone": "555-1234",
      "score": 8.5,
      "summary": [
        "5+ years Python development experience",
        "Strong React and Node.js skills", 
        "Led 3 successful product launches"
      ]
    }
  ]
}
```

#### `POST /api/schedule`
Schedule interviews for selected candidates.

**Request**: JSON
```json
{
  "candidates": [
    {
      "name": "John Doe",
      "email": "john.doe@email.com",
      "phone": "555-1234"
    }
  ]
}
```

**Response**: JSON
```json
{
  "status": "success",
  "message": "Interviews scheduled and confirmation emails sent to 3 candidates",
  "details": {
    "scheduled_interviews": 3,
    "emails_sent": 3
  }
}
```

#### `GET /health`
Health check endpoint.

**Response**: JSON
```json
{
  "status": "healthy",
  "message": "HR AI Agent API is running"
}
```

## 🧠 AI Agent System Details

### Agent Architecture

The system uses **CrewAI** framework with three specialized agents:

#### 1. ResumeScreener Agent
- **Role**: Senior HR Resume Screener
- **Goal**: Analyze and rank resumes with high accuracy
- **Tools**: PDF Text Extractor
- **Output**: Structured candidate data with scores and summaries

#### 2. InterviewScheduler Agent  
- **Role**: Professional Interview Scheduler
- **Goal**: Find optimal time slots and create calendar events
- **Tools**: Google Calendar API wrapper
- **Output**: Scheduled interview events with meeting details

#### 3. EmailDraftsman Agent
- **Role**: Professional Email Communication Specialist  
- **Goal**: Compose and send personalized interview emails
- **Tools**: Email sender with HTML templates
- **Output**: Delivery confirmation for sent emails

### Configurable LLM Support

The system supports multiple LLM providers. Configure via environment variables:

```env
# OpenAI (recommended)
LLM_PROVIDER=openai
LLM_API_KEY=sk-your-openai-key

# Anthropic Claude
LLM_PROVIDER=anthropic  
ANTHROPIC_API_KEY=your-anthropic-key

# Google Gemini
LLM_PROVIDER=google
GOOGLE_API_KEY=your-google-key
```

## 🔧 Development Mode

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

## 🛡️ Security Considerations

- **API Keys**: Store in environment variables, never commit to version control
- **File Upload**: Only PDF files accepted, with size limits (16MB max)
- **OAuth Tokens**: Stored locally, refresh automatically
- **Email Credentials**: Use Gmail app passwords, not account passwords

## 🧪 Testing

```bash
cd hr_agent_backend
python -m pytest tests/ -v
```

## 📈 Production Deployment

For production deployment:

1. **Environment**: Set `DEV_MODE=false`
2. **Security**: Use production OAuth credentials
3. **Scaling**: Consider Redis for session management
4. **Monitoring**: Add logging and health checks
5. **Database**: Consider PostgreSQL for candidate data persistence

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Troubleshooting

### Common Issues

#### "Google Calendar credentials not found"
- Ensure `credentials.json` is in `hr_agent_backend/` directory
- Verify the file is properly formatted JSON
- Check Google Cloud Console has Calendar API enabled

#### "LLM API key not found"  
- Verify `.env` file exists and contains valid API key
- Ensure `LLM_PROVIDER` matches your chosen provider
- Check API key permissions and quotas

#### "PDF extraction failed"
- Ensure uploaded files are valid PDFs
- Check file size limits (16MB max)
- Verify PyPDF2 can read the PDF format

#### "Email sending failed"
- Verify Gmail app password (not regular password)
- Ensure 2FA is enabled on Gmail account
- Check SMTP server settings

### Debug Mode

Enable detailed logging:

```bash
export FLASK_ENV=development
export FLASK_DEBUG=1
python app.py
```

---

## 💡 Features in Development

- **Database integration** for candidate persistence
- **Advanced scoring algorithms** with weighted criteria  
- **Interview feedback collection** and candidate tracking
- **Multi-company support** with role-based access
- **Analytics dashboard** for hiring metrics

For questions or support, please open an issue in the repository.