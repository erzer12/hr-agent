"""
Optimized HR Agent system using direct Gemini API calls
Reduces token usage and eliminates unnecessary LLM overhead
"""

import os
import json
import logging
import time
from datetime import datetime
from typing import List, Dict, Any, Callable
from tools import GoogleCalendarTool, EmailSender, PDFTextExtractor
from tools import MockGoogleCalendarTool, MockEmailSender, MockPDFTextExtractor
from gemini_parser import GeminiResumeParser, MockGeminiResumeParser
import ssl
from googleapiclient.errors import HttpError
import requests

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


def call_with_retries(
    fn: Callable[..., Any],
    *args,
    retries: int = 3,
    backoff_factor: float = 1.0,
    allowed_exceptions: tuple = (ssl.SSLError, HttpError, requests.exceptions.RequestException, OSError),
    **kwargs
) -> Any:
    """
    Generic retry wrapper for transient errors (SSL / network / Google HttpError).
    Uses exponential backoff: sleep = backoff_factor * (2 ** attempt)
    Raises the last exception if retries exhausted.
    """
    attempt = 0
    while True:
        try:
            return fn(*args, **kwargs)
        except allowed_exceptions as exc:
            attempt += 1
            if attempt > retries:
                logger.exception(f"Exceeded max retries ({retries}) for function {getattr(fn, '__name__', str(fn))}")
                raise
            sleep_for = backoff_factor * (2 ** (attempt - 1))
            logger.warning(
                f"Transient error calling {getattr(fn, '__name__', str(fn))}: {exc!r}. "
                f"Retrying {attempt}/{retries} after {sleep_for}s..."
            )
            time.sleep(sleep_for)
        except Exception:
            # Non-network/HTTP error: bubble up immediately
            logger.exception(f"Non-retryable exception in {getattr(fn, '__name__', str(fn))}")
            raise


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
        """Process resumes using optimized Gemini API calls"""
        try:
            logger.info(f"Processing {len(resume_files)} resumes")

            # Step 1: Extract text from PDFs
            resume_texts = self.pdf_extractor._run(resume_files)

            # Step 2: Process with Gemini parser
            candidates = self.gemini_parser.batch_process_resumes(resume_texts, job_description)

            logger.info(f"Successfully processed {len(candidates)} candidates")
            return {"candidates": candidates}

        except Exception as e:
            logger.error(f"Error processing resumes: {str(e)}")
            raise

    def get_available_slots(self, retries: int = 3, delay: int = 2) -> List[Dict[str, Any]]:
        """Get available interview slots with retry on SSL/network errors"""
        # Use the generic retry helper to protect the calendar call
        try:
            slots = call_with_retries(
                self.calendar_tool._run,
                'find_slots',
                duration_minutes=30,
                days_ahead=14,
                retries=retries,
                backoff_factor=delay
            )
            return slots
        except HttpError as he:
            logger.error(f"Google Calendar API HttpError while fetching slots: {he}")
            raise
        except ssl.SSLError as se:
            logger.error(f"SSL error while fetching slots after retries: {se}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error fetching slots: {e}")
            raise

    def get_calendar_url(self) -> str:
        """Get Google Calendar iframe URL (protected with retries)"""
        try:
            return call_with_retries(self.calendar_tool.get_calendar_iframe_url, retries=2, backoff_factor=1.0)
        except Exception as e:
            logger.error(f"Error fetching calendar iframe URL: {e}")
            raise

    def draft_email(self, candidate: Dict[str, Any], interview_details: Dict[str, Any]) -> str:
        """Draft interview confirmation email (local operation)"""
        try:
            # drafting email typically doesn't hit network, but send through retry wrapper if it does internally
            return call_with_retries(self.email_sender.draft_email, candidate['name'], candidate['email'], interview_details, retries=1, backoff_factor=0.5)
        except Exception as e:
            logger.error(f"Error drafting email: {e}")
            raise

    def schedule_interview(self, candidate: Dict[str, Any], start_time: str, end_time: str,
                           retries: int = 3, delay: int = 2) -> Dict[str, Any]:
        """Schedule a single interview with retries on SSL and network errors"""
        for attempt in range(1, retries + 1):
            try:
                logger.info(f"Scheduling interview for {candidate.get('name')} (attempt {attempt}/{retries})")

                # Create calendar event via calendar_tool (wrapped in call_with_retries)
                event_details = call_with_retries(
                    self.calendar_tool._run,
                    'create_event',
                    title=f"Interview: {os.getenv('COMPANY_NAME', 'Company')} - {candidate.get('name')}",
                    start_time=start_time,
                    end_time=end_time,
                    attendee_emails=[candidate.get('email'), os.getenv('INTERVIEWER_EMAIL', 'interviewer@company.com')],
                    description=f"Interview with {candidate.get('name')} for the open position.",
                    retries=2,
                    backoff_factor=delay
                )

                # Prepare interview details for email; be permissive in parsing the ISO timestamp
                interview_details = {}
                try:
                    dt = datetime.fromisoformat(start_time)
                    interview_details['date'] = dt.strftime('%Y-%m-%d')
                    interview_details['time'] = dt.strftime('%I:%M %p')
                    interview_details['timezone'] = dt.tzname() if dt.tzinfo else os.getenv('TIMEZONE', 'UTC')
                except Exception:
                    # If we can't parse the ISO string, fall back to raw strings
                    logger.warning("Failed to parse start_time with datetime.fromisoformat(); using raw string values")
                    interview_details['date'] = start_time
                    interview_details['time'] = start_time
                    interview_details['timezone'] = os.getenv('TIMEZONE', 'UTC')

                interview_details['meeting_link'] = event_details.get('meeting_link', event_details.get('hangoutLink', 'TBD'))

                # Send confirmation email (wrap email sending which may perform network calls)
                email_sent = call_with_retries(
                    self.email_sender._run,
                    candidate.get('email'),
                    candidate.get('name'),
                    interview_details,
                    retries=1,
                    backoff_factor=0.5
                )

                return {
                    "status": "success",
                    "message": f"Successfully scheduled interview for {candidate.get('name')}",
                    "details": {
                        "candidate_name": candidate.get('name'),
                        "interview_date": interview_details['date'],
                        "interview_time": interview_details['time'],
                        "meeting_link": interview_details['meeting_link'],
                        "email_sent": email_sent
                    }
                }

            except (ssl.SSLError, requests.exceptions.RequestException) as transient_err:
                logger.warning(f"Transient error scheduling interview (attempt {attempt}/{retries}): {transient_err}")
                # let call_with_retries handle sleeping if it was used; if here, we sleep then retry
                if attempt < retries:
                    time.sleep(delay * (2 ** (attempt - 1)))
                    continue
                logger.exception("Exceeded retries while scheduling interview due to transient errors")
                raise
            except HttpError as he:
                logger.error(f"Google Calendar API HttpError while scheduling interview: {he}")
                # HttpError is probably not transient in some cases, re-raise to let upper layers decide
                raise
            except Exception as e:
                logger.error(f"Unexpected error scheduling interview: {e}")
                raise

        # If we exit the loop without returning:
        raise Exception(f"Failed to schedule interview for {candidate.get('name')} after {retries} attempts")

    def get_scheduled_interviews(self) -> List[Dict[str, Any]]:
        """Get all scheduled interviews from calendar (protected by retries)"""
        try:
            events = call_with_retries(self.optimized_calendar_list_events, days_ahead=30, retries=2, backoff_factor=1.0)
            interviews = []

            for event in events:
                summary = event.get('summary', '')
                if 'Interview:' in summary or summary.lower().startswith('interview'):
                    interviews.append({
                        'id': event.get('id'),
                        'title': summary,
                        'start_time': event.get('start', {}).get('dateTime') or event.get('start', {}).get('date'),
                        'end_time': event.get('end', {}).get('dateTime') or event.get('end', {}).get('date'),
                        'attendees': [att.get('email') for att in event.get('attendees', [])] if event.get('attendees') else [],
                        'status': event.get('status', 'confirmed')
                    })

            return interviews
        except Exception as e:
            logger.error(f"Error fetching scheduled interviews: {str(e)}")
            return []

    # Helper to call calendar_tool.list_events in a safe way (some calendar tool implementations may be different)
    def optimized_calendar_list_events(self, days_ahead: int = 30):
        """
        Call calendar_tool.list_events if available, otherwise fall back to a `_run` call.
        This wrapper helps compatibility with different implementations of GoogleCalendarTool / mocks.
        """
        if hasattr(self.calendar_tool, 'list_events') and callable(getattr(self.calendar_tool, 'list_events')):
            return self.calendar_tool.list_events(days_ahead=days_ahead)
        else:
            # assume _run interface
            return self.calendar_tool._run('list_events', days_ahead=days_ahead)


# ---------------------------
# HRAgentCrew Wrapper
# ---------------------------

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
        return self.optimized_system.get_scheduled_interviews()
