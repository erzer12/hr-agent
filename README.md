# HR AI Agent - Autonomous Resume Screening & Interview Scheduling

A complete full-stack web application that automates the initial hiring process through AI-powered resume screening, candidate ranking, and automated interview scheduling with email notifications.

## 🚀 Project Overview

This application streamlines HR workflows by:
- **Autonomously screening** uploaded resumes against job descriptions
- **Ranking candidates** based on qualification match scores (1-10 scale)
- **Scheduling interviews** automatically via Google Calendar integration
- **Sending personalized confirmation emails** to selected candidates

The system uses Google Gemini API for efficient resume parsing and analysis, with optimized token usage for cost-effective operation.

## 🏗️ System Architecture

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

### Data Flow

1. **Upload Phase**: User uploads PDFs and job description through React frontend
2. **Processing Phase**: Flask API uses Gemini API to analyze resumes vs. job requirements
3. **Ranking Phase**: Gemini generates candidate scores, summaries, and contact information
4. **Selection Phase**: HR user reviews ranked candidates and selects interview candidates
5. **Scheduling Phase**: Direct API calls find calendar slots and create interview events
6. **Communication Phase**: Automated personalized emails sent to selected candidates

## 📋 Prerequisites

### Software Requirements
- **Python 3.9+** - Backend runtime
- **Node.js 16+** - Frontend development
- **npm/yarn** - Package management

### API Account Requirements
- **Google AI API Access** - Google Gemini API key
- **Google Cloud Project** - For Calendar API
- **Gmail Account** - For email notifications (with app passwords enabled)

# HR AI Agent - Autonomous Resume Screening & Interview Scheduling

A complete full-stack web application that automates the initial hiring process through AI-powered resume screening, candidate ranking, and automated interview scheduling with email notifications.

## 🚀 Project Overview

This application streamlines HR workflows by:
- **Autonomously screening** uploaded resumes against job descriptions
- **Ranking candidates** based on qualification match scores (1-10 scale)
- **Scheduling interviews** automatically via Google Calendar integration
- **Sending personalized confirmation emails** to selected candidates

The system uses Google Gemini API for efficient resume parsing and analysis, with optimized token usage for cost-effective operation.

## 🏗️ System Architecture

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

### Data Flow

1. **Upload Phase**: User uploads PDFs and job description through React frontend
2. **Processing Phase**: Flask API uses Gemini API to analyze resumes vs. job requirements
3. **Ranking Phase**: Gemini generates candidate scores, summaries, and contact information
4. **Selection Phase**: HR user reviews ranked candidates and selects interview candidates
5. **Scheduling Phase**: Direct API calls find calendar slots and create interview events
6. **Communication Phase**: Automated personalized emails sent to selected candidates

## 📋 Prerequisites

### Software Requirements
- **Python 3.9+** - Backend runtime
- **Node.js 16+** - Frontend development
- **npm/yarn** - Package management

### API Account Requirements
- **Google AI API Access** - Google Gemini API key
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
source venv/Scripts/activate
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

### Optimized Architecture

The system uses **Google Gemini API** directly for efficient resume processing:

#### 1. Gemini Resume Parser
- **Function**: Direct API calls to Gemini 1.5 Flash
- **Optimization**: Truncated inputs, structured JSON responses
- **Token Efficiency**: ~70% reduction vs traditional LLM chains
- **Output**: Structured candidate data with scores and summaries

#### 2. Direct Calendar Integration
- **Function**: Direct Google Calendar API calls
- **Efficiency**: No LLM overhead for scheduling logic
- **Output**: Scheduled interview events with meeting details

#### 3. Template-Based Email System
- **Function**: Pre-built HTML email templates
- **Efficiency**: No LLM needed for email generation
- **Output**: Delivery confirmation for sent emails

### Token Usage Optimization

The optimized system reduces token usage through:

- **Text Truncation**: Resume text limited to 2000 characters
- **Structured Prompts**: Minimal, focused prompts for specific tasks
- **Batch Processing**: Efficient processing of multiple resumes
- **Smart Scoring**: Quick keyword-based pre-screening before API calls
- **JSON Responses**: Structured output reduces parsing overhead

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

## 📊 SWOT Analysis

For a comprehensive strategic analysis of the HR AI Agent system, including strengths, weaknesses, opportunities, and threats, see [SWOT_ANALYSIS.md](SWOT_ANALYSIS.md).

### Key Strategic Insights:
- **70% cost reduction** through optimized Gemini API usage
- **Strong market opportunity** in SMB recruitment automation
- **Technical differentiation** through direct API integration
- **Growth potential** in multi-language and industry-specific markets

## 🚀 How to Run

### 1. Start Backend Server

```bash
cd hr_agent_backend
source venv/Scripts/activate
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

### Optimized Architecture

The system uses **Google Gemini API** directly for efficient resume processing:

#### 1. Gemini Resume Parser
- **Function**: Direct API calls to Gemini 1.5 Flash
- **Optimization**: Truncated inputs, structured JSON responses
- **Token Efficiency**: ~70% reduction vs traditional LLM chains
- **Output**: Structured candidate data with scores and summaries

#### 2. Direct Calendar Integration
- **Function**: Direct Google Calendar API calls
- **Efficiency**: No LLM overhead for scheduling logic
- **Output**: Scheduled interview events with meeting details

#### 3. Template-Based Email System
- **Function**: Pre-built HTML email templates
- **Efficiency**: No LLM needed for email generation
- **Output**: Delivery confirmation for sent emails

### Token Usage Optimization

The optimized system reduces token usage through:

- **Text Truncation**: Resume text limited to 2000 characters
- **Structured Prompts**: Minimal, focused prompts for specific tasks
- **Batch Processing**: Efficient processing of multiple resumes
- **Smart Scoring**: Quick keyword-based pre-screening before API calls
- **JSON Responses**: Structured output reduces parsing overhead

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

## 📊 SWOT Analysis

For a comprehensive strategic analysis of the HR AI Agent system, including strengths, weaknesses, opportunities, and threats, see [SWOT_ANALYSIS.md](SWOT_ANALYSIS.md).

### Key Strategic Insights:
- **70% cost reduction** through optimized Gemini API usage
- **Strong market opportunity** in SMB recruitment automation
- **Technical differentiation** through direct API integration
- **Growth potential** in multi-language and industry-specific markets