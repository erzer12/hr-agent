"""
Optimized HR Agent system using direct Gemini API calls
Reduces token usage and eliminates unnecessary LLM overhead
"""

import os
import json
import logging
from datetime import datetime
from typing import List, Dict, Any
from tools import GoogleCalendarTool, EmailSender, PDFTextExtractor
from tools import MockGoogleCalendarTool, MockEmailSender, MockPDFTextExtractor
from gemini_parser import GeminiResumeParser, MockGeminiResumeParser

logger = logging.getLogger(__name__)

class OptimizedHRSystem:
    """Streamlined HR system using direct Gemini API for resume parsing"""
    
    def __init__(self):
        self.dev_mode = os.getenv('DEV_MODE', 'false').lower() == 'true'
        
        if self.dev_mode:
            logger.info("Running in development mode with mock implementations")
            self.pdf_extractor = MockPDFTextExtractor()
            self.gemini_parser = MockGeminiResumeParser()
            self.calendar_tool = MockGoogleCalendarTool()
            self.email_sender = MockEmailSender()
        else:
            logger.info("Running in production mode with real APIs")
            self.pdf_extractor = PDFTextExtractor()
            self.gemini_parser = GeminiResumeParser()
            self.calendar_tool = GoogleCalendarTool()
            self.email_sender = EmailSender()
    
    def process_resumes(self, job_description: str, resume_files: List[str]) -> Dict[str, Any]:
        """
        Process resumes using optimized Gemini API calls
        Significantly reduced token usage compared to CrewAI approach
        """
        try:
            logger.info(f"Processing {len(resume_files)} resumes")
            
            # Step 1: Extract text from PDFs
            resume_texts = self.pdf_extractor._run(resume_files)
            
            # Step 2: Process with Gemini (optimized for token efficiency)
            candidates = self.gemini_parser.batch_process_resumes(resume_texts, job_description)
            
            logger.info(f"Successfully processed {len(candidates)} candidates")
            
            return {"candidates": candidates}
            
        except Exception as e:
            logger.error(f"Error processing resumes: {str(e)}")
            raise
    
    def get_available_slots(self) -> List[Dict[str, Any]]:
        """Get available interview slots"""
        return self.calendar_tool._run('find_slots', duration_minutes=30, days_ahead=14)

    def get_calendar_url(self) -> str:
        """Get Google Calendar iframe URL"""
        return self.calendar_tool.get_calendar_iframe_url()

    def draft_email(self, candidate: Dict[str, Any], interview_details: Dict[str, Any]) -> str:
        """Draft interview confirmation email"""
        return self.email_sender.draft_email(candidate['name'], candidate['email'], interview_details)

    def schedule_interview(self, candidate: Dict[str, Any], start_time: str, end_time: str) -> Dict[str, Any]:
        """
        Schedule a single interview using direct tool calls
        """
        try:
            logger.info(f"Scheduling interview for {candidate['name']}")

            # Create calendar event
            event_details = self.calendar_tool._run(
                'create_event',
                title=f"Interview: {os.getenv('COMPANY_NAME', 'Company')} - {candidate['name']}",
                start_time=start_time,
                end_time=end_time,
                attendee_emails=[candidate['email'], os.getenv('INTERVIEWER_EMAIL', 'interviewer@company.com')],
                description=f"Interview with {candidate['name']} for the open position."
            )

            # Prepare interview details for email
            interview_details = {
                'date': datetime.fromisoformat(start_time).strftime('%Y-%m-%d'),
                'time': datetime.fromisoformat(start_time).strftime('%I:%M %p'),
                'timezone': 'EST',
                'meeting_link': event_details.get('meeting_link', 'TBD')
            }

            # Send confirmation email
            email_sent = self.email_sender._run(
                candidate['email'],
                candidate['name'],
                interview_details
            )

            return {
                "status": "success",
                "message": f"Successfully scheduled interview for {candidate['name']}",
                "details": {
                    "candidate_name": candidate['name'],
                    "interview_date": interview_details['date'],
                    "interview_time": interview_details['time'],
                    'meeting_link': interview_details['meeting_link'],
                    "email_sent": email_sent
                }
            }

        except Exception as e:
            logger.error(f"Error scheduling interview: {str(e)}")
            raise

# Maintain backward compatibility
class HRAgentCrew:
    """Wrapper to maintain compatibility with existing code"""
    
    def __init__(self):
        self.optimized_system = OptimizedHRSystem()
    
    def process_resumes(self, job_description: str, resume_files: List[str]) -> Dict[str, Any]:
        return self.optimized_system.process_resumes(job_description, resume_files)
    
    def get_available_slots(self) -> List[Dict[str, Any]]:
        return self.optimized_system.get_available_slots()

    def get_calendar_url(self) -> str:
        return self.optimized_system.get_calendar_url()

    def draft_email(self, candidate: Dict[str, Any], interview_details: Dict[str, Any]) -> str:
        return self.optimized_system.draft_email(candidate, interview_details)

    def schedule_interview(self, candidate: Dict[str, Any], start_time: str, end_time: str) -> Dict[str, Any]:
        return self.optimized_system.schedule_interview(candidate, start_time, end_time)

    def get_scheduled_interviews(self) -> List[Dict[str, Any]]:
        """Get all scheduled interviews from calendar"""
        try:
            events = self.calendar_tool.list_events(days_ahead=30)
            interviews = []
            
            for event in events:
                if 'Interview:' in event.get('summary', ''):
                    interviews.append({
                        'id': event['id'],
                        'title': event['summary'],
                        'start_time': event['start']['dateTime'],
                        'end_time': event['end']['dateTime'],
                        'attendees': [att.get('email') for att in event.get('attendees', [])],
                        'status': event.get('status', 'confirmed')
                    })
            
            return interviews
        except Exception as e:
            logger.error(f"Error fetching scheduled interviews: {str(e)}")
            return []