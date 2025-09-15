"""
Custom tools for HR AI agents
Provides interfaces to external services like Google Calendar, email, and PDF processing
"""

import os
import io
import json
import logging
import smtplib
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Dict, Any, Optional, ClassVar

import PyPDF2
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from crewai.tools import BaseTool
logger = logging.getLogger(__name__)

class PDFTextExtractor(BaseTool):
    """Tool to extract text content from PDF files"""
    
    name: str = "PDF Text Extractor"
    description: str = "Extract text content from PDF resume files for analysis"
    
    def _run(self, file_paths: List[str]) -> Dict[str, str]:
        """
        Extract text from PDF files
        """
        extracted_texts = {}
        
        for file_path in file_paths:
            try:
                with open(file_path, 'rb') as file:
                    pdf_reader = PyPDF2.PdfReader(file)
                    text = ""
                    
                    for page_num in range(len(pdf_reader.pages)):
                        page = pdf_reader.pages[page_num]
                        text += page.extract_text() + "\n"
                    
                    extracted_texts[file_path] = text.strip()
                    logger.info(f"Successfully extracted text from {os.path.basename(file_path)}")
                    
            except Exception as e:
                logger.error(f"Error extracting text from {file_path}: {str(e)}")
                extracted_texts[file_path] = f"Error extracting text: {str(e)}"
        
        return extracted_texts

class GoogleCalendarTool(BaseTool):
    """Tool to interact with Google Calendar API"""
    
    name: str = "Google Calendar Tool"
    description: str = "Schedule interviews and manage calendar events"
    service: Any = None
    
    SCOPES: ClassVar[List[str]] = ['https://www.googleapis.com/auth/calendar']
    
    def __init__(self):
        super().__init__()
        self.service = self._authenticate()
    
    def _authenticate(self):
        """Authenticate with Google Calendar API"""
        creds = None
        script_dir = os.path.dirname(os.path.abspath(__file__))
        credentials_path = os.path.join(script_dir, 'credentials.json')
        token_path = os.getenv('GOOGLE_CALENDAR_TOKEN_PATH', 'token.json')
        
        if os.path.exists(token_path):
            creds = Credentials.from_authorized_user_file(token_path, self.SCOPES)
        
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not os.path.exists(credentials_path):
                    logger.error(f"Google Calendar credentials file not found: {credentials_path}")
                    raise FileNotFoundError(f"Google Calendar credentials file not found: {credentials_path}")
                
                flow = InstalledAppFlow.from_client_secrets_file(credentials_path, self.SCOPES)
                creds = flow.run_local_server(port=8080)
            
            with open(token_path, 'w') as token:
                token.write(creds.to_json())

        return build('calendar', 'v3', credentials=creds, cache_discovery=False)

    def _run(self, action: str, **kwargs) -> Any:
        """
        Execute calendar operations
        """
        try:
            if action == 'find_slots':
                return self.find_available_slots(**kwargs)
            elif action == 'create_event':
                return self.create_event(**kwargs)
            elif action == 'list_events':
                return self.list_events(**kwargs)
            else:
                raise ValueError(f"Unknown action: {action}")
        except Exception as e:
            logger.error(f"Google Calendar API error: {str(e)}")
            raise
    
    def find_available_slots(self, duration_minutes: int = 30, days_ahead: int = 5) -> List[Dict[str, Any]]:
        """
        Find available time slots for interviews
        """
        available_slots = []
        current_date = datetime.now().date()
        
        for i in range(days_ahead * 2):
            check_date = current_date + timedelta(days=i)
            
            if check_date.weekday() >= 5:
                continue
            
            for hour in range(9, 17):
                for minute in [0, 30]:
                    if hour == 16 and minute == 30:
                        break
                    
                    start_time = datetime.combine(check_date, datetime.min.time().replace(hour=hour, minute=minute))
                    end_time = start_time + timedelta(minutes=duration_minutes)
                    
                    if self._is_slot_available(start_time, end_time):
                        available_slots.append({
                            'start_time': start_time.isoformat(),
                            'end_time': end_time.isoformat(),
                            'date': check_date.strftime('%Y-%m-%d'),
                            'time': start_time.strftime('%H:%M'),
                            'timezone': 'EST'
                        })
            
            if len(available_slots) >= 20:
                break
        
        grouped_slots = {}
        for slot in available_slots:
            date = slot['date']
            if date not in grouped_slots:
                grouped_slots[date] = []
            grouped_slots[date].append(slot['time'])
        
        return [{'date': date, 'slots': times} for date, times in grouped_slots.items()]
    
    def _is_slot_available(self, start_time: datetime, end_time: datetime) -> bool:
        """
        Check if a time slot is available
        """
        try:
            events_result = self.service.events().list(
                calendarId='primary',
                timeMin=start_time.isoformat() + 'Z',
                timeMax=end_time.isoformat() + 'Z',
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            
            return len(events) == 0
            
        except HttpError as e:
            logger.error(f"Error checking calendar availability: {str(e)}")
            return True
    
    def create_event(self, title: str, start_time: str, end_time: str, attendee_emails: List[str], description: str = "") -> Dict[str, Any]:
        """
        Create a calendar event
        """
        event = {
            'summary': title,
            'description': description,
            'start': {
                'dateTime': start_time,
                'timeZone': 'America/New_York',
            },
            'end': {
                'dateTime': end_time,
                'timeZone': 'America/New_York',
            },
            'attendees': [{'email': email} for email in attendee_emails],
            'reminders': {
                'useDefault': False,
                'overrides': [
                    {'method': 'email', 'minutes': 24 * 60},
                    {'method': 'popup', 'minutes': 30},
                ],
            },
            # --- START: ADDED SECTION ---
            # This tells Google Calendar to create a new Google Meet conference
            'conferenceData': {
                'createRequest': {
                    'requestId': f"hr-agent-{datetime.now().timestamp()}",
                    'conferenceSolutionKey': {
                        'type': 'hangoutsMeet'
                    }
                }
            }
            # --- END: ADDED SECTION ---
        }
        
        try:
            # The 'conferenceDataVersion=1' parameter is required to get the link back
            created_event = self.service.events().insert(
                calendarId='primary', 
                body=event,
                conferenceDataVersion=1  # <-- ADDED
            ).execute()
            
            logger.info(f"Event created: {created_event.get('htmlLink')}")
            
            return {
                'event_id': created_event['id'],
                'event_link': created_event.get('htmlLink'),
                'meeting_link': created_event.get('hangoutLink', 'TBD')
            }
            
        except HttpError as e:
            logger.error(f"Error creating calendar event: {str(e)}")
            raise
    def get_calendar_iframe_url(self) -> str:
        """Get the public URL for the primary calendar"""
        try:
            calendar = self.service.calendars().get(calendarId='primary').execute()
            return f"https://calendar.google.com/calendar/embed?src={calendar['id']}"
        except HttpError as e:
            logger.error(f"Error getting calendar URL: {str(e)}")
            return ""

    def list_events(self, days_ahead: int = 7) -> List[Dict[str, Any]]:
        """List upcoming events"""
        now = datetime.utcnow()
        time_max = now + timedelta(days=days_ahead)
        
        try:
            events_result = self.service.events().list(
                calendarId='primary',
                timeMin=now.isoformat() + 'Z',
                timeMax=time_max.isoformat() + 'Z',
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            return events_result.get('items', [])
            
        except HttpError as e:
            logger.error(f"Error listing calendar events: {str(e)}")
            return []

class EmailSender(BaseTool):
    """Tool to send interview confirmation emails"""
    
    name: str = "Email Sender"
    description: str = "Send professional interview confirmation emails to candidates"
    smtp_server: str = "smtp.gmail.com"
    smtp_port: int = 587
    email_address: Optional[str] = None
    email_password: Optional[str] = None
    company_name: str = "Your Company"
    interviewer_name: str = "Hiring Manager"
    
    def __init__(self):
        super().__init__()
        self.smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        self.email_address = os.getenv('EMAIL_ADDRESS')
        self.email_password = os.getenv('EMAIL_PASSWORD')
        self.company_name = os.getenv('COMPANY_NAME', 'Your Company')
        self.interviewer_name = os.getenv('INTERVIEWER_NAME', 'Hiring Manager')

    def draft_email(self, candidate_name: str, candidate_email: str, interview_details: Dict[str, Any], template: str = "professional") -> str:
        """Drafts an interview confirmation email."""
        subject = f"Interview Confirmation - {self.company_name}"
        body = self._create_email_body(candidate_name, interview_details)
        return body
    
    def _run(self, candidate_email: str, candidate_name: str, interview_details: Dict[str, Any], template: str = "professional") -> bool:
        """
        Send interview confirmation email
        """
        try:
            subject = f"Interview Confirmation - {self.company_name}"
            body = self._create_email_body(candidate_name, interview_details)

            msg = MIMEMultipart()
            msg['From'] = self.email_address
            msg['To'] = candidate_email
            msg['Subject'] = subject

            msg.attach(MIMEText(body, 'html'))

            if self.email_address and self.email_password:
                server = smtplib.SMTP(self.smtp_server, self.smtp_port)
                server.starttls()
                server.login(self.email_address, self.email_password)
                server.send_message(msg)
                server.quit()

                logger.info(f"Interview confirmation email sent to {candidate_email}")
                return True
            else:
                logger.warning("Email credentials not configured - email not sent")
                return False

        except Exception as e:
            logger.error(f"Error sending email to {candidate_email}: {str(e)}")
            return False
 
    def _create_email_body(self, candidate_name: str, interview_details: Dict[str, Any], template: str = "professional") -> str:
        """Create HTML email body based on template"""
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #f8f9fa; padding: 20px; text-align: center; border-radius: 8px; margin-bottom: 20px; }}
                .content {{ background-color: #fff; padding: 20px; border: 1px solid #dee2e6; border-radius: 8px; }}
                .highlight {{ background-color: #e3f2fd; padding: 15px; border-left: 4px solid #2196f3; margin: 20px 0; }}
                .footer {{ margin-top: 20px; padding-top: 20px; border-top: 1px solid #dee2e6; font-size: 14px; color: #6c757d; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>{self.company_name}</h1>
                    <h2>Interview Confirmation</h2>
                </div>
                
                <div class="content">
                    <p>Dear {candidate_name},</p>
                    
                    <p>Thank you for your interest in joining our team! We're excited to move forward with your application and would like to schedule an interview with you.</p>
                    
                    <div class="highlight">
                        <h3>Interview Details:</h3>
                        <ul>
                            <li><strong>Date:</strong> {interview_details.get('date', 'TBD')}</li>
                            <li><strong>Time:</strong> {interview_details.get('time', 'TBD')} ({interview_details.get('timezone', 'EST')})</li>
                            <li><strong>Duration:</strong> 30 minutes</li>
                            <li><strong>Interviewer:</strong> {self.interviewer_name}</li>
                            <li><strong>Meeting Link:</strong> {interview_details.get('meeting_link', 'Will be provided closer to the interview date')}</li>
                        </ul>
                    </div>
                    
                    <h3>What to Expect:</h3>
                    <ul>
                        <li>Discussion about your background and experience</li>
                        <li>Overview of the role and team</li>
                        <li>Opportunity for you to ask questions about the position and company</li>
                    </ul>
                    
                    <p>We look forward to speaking with you!</p>
                    
                    <p>Best regards,<br>
                    {self.interviewer_name}<br>
                    {self.company_name}<br>
                    </p>
                </div>
                
                <div class="footer">
                    <p>This email was sent from an automated system. Please contact our hiring team if you have any questions.</p>
                </div>
            </div>
        </body>
        </html>
        """

# Mock implementations for development/testing
class MockPDFTextExtractor(PDFTextExtractor):
    """Mock PDF extractor for testing without actual PDF processing"""
    
    def _run(self, file_paths: List[str]) -> Dict[str, str]:
        """Mock text extraction"""
        mock_texts = {}
        for i, file_path in enumerate(file_paths):
            filename = os.path.basename(file_path)
            mock_texts[file_path] = f"""
            Name: {filename.replace('.pdf', '').replace('_', ' ').title()}
            Email: {filename.lower().replace('.pdf', '').replace('_', '.')}@email.com
            Phone: 555-{1000 + i:04d}
            
            Experience: {5 - i} years in software development
            Skills: Python, JavaScript, React, Node.js, SQL
            Education: Bachelor's in Computer Science
            
            Previous roles:
            - Senior Software Engineer at Tech Corp ({2022 - i}-present)
            - Software Engineer at Startup Inc ({2020 - i}-{2022 - i})
            - Junior Developer at Small Company ({2018 - i}-{2020 - i})
            """
        return mock_texts

class MockGoogleCalendarTool(GoogleCalendarTool):
    """Mock calendar tool for testing without Google API"""
    
    def __init__(self):
        # Skip authentication for mock
        pass
    
    def _run(self, action: str, **kwargs) -> Any:
        """Mock calendar operations"""
        if action == 'find_slots':
            return self._mock_find_slots(**kwargs)
        elif action == 'create_event':
            return self._mock_create_event(**kwargs)
        else:
            return []
    
    def _mock_find_slots(self, duration_minutes: int = 30, days_ahead: int = 5) -> List[Dict[str, Any]]:
        """Mock available slots"""
        grouped_slots = {}
        base_date = datetime.now().date() + timedelta(days=1)
        
        for day in range(days_ahead):
            if (base_date + timedelta(days=day)).weekday() < 5:  # Weekdays only
                slot_date = base_date + timedelta(days=day)
                date_str = slot_date.strftime('%Y-%m-%d')
                grouped_slots[date_str] = []
                
                for hour in [10, 11, 14, 15]:  # 10 AM, 11 AM, 2 PM, 3 PM
                    grouped_slots[date_str].append(f'{hour:02d}:00')
        
        return [{'date': date, 'slots': times} for date, times in grouped_slots.items()]
    
    def _mock_create_event(self, **kwargs) -> Dict[str, Any]:
        """Mock event creation"""
        return {
            'event_id': f'mock_event_{datetime.now().timestamp()}',
            'event_link': 'https://calendar.google.com/mock-event',
            'meeting_link': 'https://meet.google.com/mock-meeting'
        }

class MockEmailSender(EmailSender):
    """Mock email sender for testing without actual email sending"""
    
    def __init__(self):
        # Initialize without email credentials
        self.company_name = 'Demo Company'
        self.interviewer_name = 'Demo Interviewer'
    
    def _run(self, candidate_email: str, candidate_name: str, interview_details: Dict[str, Any]) -> bool:
        """Mock email sending"""
        logger.info(f"Mock: Would send email to {candidate_email} for interview on {interview_details.get('date', 'TBD')}")
        return True