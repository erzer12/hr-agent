"""
Optimized HR Agent system using direct Gemini API calls
Reduces token usage and eliminates unnecessary LLM overhead
"""

import os
import json
import logging
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
    
    def schedule_interviews(self, candidates: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Schedule interviews using direct tool calls (no LLM needed)
        """
        try:
            logger.info(f"Scheduling interviews for {len(candidates)} candidates")
            
            # Step 1: Find available time slots
            available_slots = self.calendar_tool._run('find_slots', duration_minutes=30, days_ahead=5)
            
            if len(available_slots) < len(candidates):
                logger.warning(f"Only {len(available_slots)} slots available for {len(candidates)} candidates")
            
            scheduled_interviews = []
            emails_sent = []
            
            # Step 2: Schedule interviews and send emails
            for i, candidate in enumerate(candidates):
                if i >= len(available_slots):
                    logger.warning(f"No more slots available for candidate {candidate['name']}")
                    break
                
                slot = available_slots[i]
                
                # Create calendar event
                event_details = self.calendar_tool._run(
                    'create_event',
                    title=f"Interview: {os.getenv('COMPANY_NAME', 'Company')} - {candidate['name']}",
                    start_time=slot['start_time'],
                    end_time=slot['end_time'],
                    attendee_emails=[candidate['email'], os.getenv('INTERVIEWER_EMAIL', 'interviewer@company.com')],
                    description=f"Interview with {candidate['name']} for the open position."
                )
                
                # Prepare interview details for email
                interview_details = {
                    'date': slot['date'],
                    'time': slot['time'],
                    'timezone': slot['timezone'],
                    'meeting_link': event_details.get('meeting_link', 'TBD')
                }
                
                # Send confirmation email
                email_sent = self.email_sender._run(
                    candidate['email'],
                    candidate['name'],
                    interview_details
                )
                
                scheduled_interviews.append({
                    'candidate_name': candidate['name'],
                    'candidate_email': candidate['email'],
                    'interview_date': slot['date'],
                    'interview_time': slot['time'],
                    'timezone': slot['timezone'],
                    'meeting_link': interview_details['meeting_link']
                })
                
                emails_sent.append({
                    'candidate_name': candidate['name'],
                    'candidate_email': candidate['email'],
                    'email_sent': email_sent
                })
            
            success_count = len([e for e in emails_sent if e['email_sent']])
            
            return {
                "status": "success",
                "message": f"Successfully scheduled {len(scheduled_interviews)} interviews and sent {success_count} confirmation emails",
                "details": {
                    "scheduled_interviews": len(scheduled_interviews),
                    "emails_sent": success_count,
                    "interviews": scheduled_interviews
                }
            }
            
        except Exception as e:
            logger.error(f"Error scheduling interviews: {str(e)}")
            raise

# Maintain backward compatibility
class HRAgentCrew:
    """Wrapper to maintain compatibility with existing code"""
    
    def __init__(self):
        self.optimized_system = OptimizedHRSystem()
    
    def process_resumes(self, job_description: str, resume_files: List[str]) -> Dict[str, Any]:
        return self.optimized_system.process_resumes(job_description, resume_files)
    
    def schedule_interviews(self, candidates: List[Dict[str, Any]]) -> Dict[str, Any]:
        return self.optimized_system.schedule_interviews(candidates)