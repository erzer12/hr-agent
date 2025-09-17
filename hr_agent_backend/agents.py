"""
HR AI Agent Crew using CrewAI
Defines autonomous agents for resume screening, interview scheduling, and email communication
"""

import os
import json
import logging
from typing import List, Dict, Any
from crewai import Agent, Task, Crew
from tools import PDFTextExtractor, GoogleCalendarTool, EmailSender
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_google_genai import ChatGoogleGenerativeAI

logger = logging.getLogger(__name__)

class HRAgentCrew:
    """Main crew orchestrating HR AI agents"""
    
    def __init__(self):
        self.llm = self._initialize_llm()
        self.tools = self._initialize_tools()
        self.agents = self._create_agents()
    
    def _initialize_llm(self):
        """Initialize LLM based on configuration"""
        llm_provider = os.getenv('LLM_PROVIDER', 'openai').lower()
        api_key = os.getenv('LLM_API_KEY')
        
        if not api_key:
            raise ValueError("LLM_API_KEY environment variable is required")
        
        if llm_provider == 'openai':
            return ChatOpenAI(
                model='gpt-4-turbo-preview',
                temperature=0.1,
                api_key=api_key
            )
        elif llm_provider == 'anthropic':
            return ChatAnthropic(
                model='claude-3-sonnet-20240229',
                temperature=0.1,
                api_key=api_key
            )
        elif llm_provider == 'google':
            return ChatGoogleGenerativeAI(
                model='gemini-pro',
                temperature=0.1,
                google_api_key=api_key
            )
        else:
            raise ValueError(f"Unsupported LLM provider: {llm_provider}")
    
    def _initialize_tools(self):
        """Initialize all tools required by agents"""
        return {
            'pdf_extractor': PDFTextExtractor(),
            'calendar': GoogleCalendarTool(),
            'email_sender': EmailSender()
        }
    
    def _create_agents(self):
        """Create specialized AI agents"""
        
        # Agent 1: Resume Screener
        resume_screener = Agent(
            role='Senior HR Resume Screener',
            goal='Analyze resumes and rank candidates based on job requirements with high accuracy',
            backstory="""You are an expert HR professional with 15+ years of experience in talent acquisition. 
            You have a keen eye for identifying top talent and matching candidates to job requirements. 
            You excel at extracting key information from resumes and providing objective, data-driven assessments.""",
            verbose=True,
            allow_delegation=False,
            llm=self.llm,
            tools=[self.tools['pdf_extractor']]
        )
        
        # Agent 2: Interview Scheduler
        interview_scheduler = Agent(
            role='Professional Interview Scheduler',
            goal='Efficiently schedule interviews by finding optimal time slots and creating calendar events',
            backstory="""You are a highly organized scheduling coordinator who excels at managing complex calendars. 
            You understand the importance of timely interview scheduling and always find the best available slots 
            while respecting business hours and professional standards.""",
            verbose=True,
            allow_delegation=False,
            llm=self.llm,
            tools=[self.tools['calendar']]
        )
        
        # Agent 3: Email Communication Specialist
        email_draftsman = Agent(
            role='Professional Email Communication Specialist',
            goal='Compose and send personalized, professional interview confirmation emails',
            backstory="""You are a professional communicator who crafts clear, engaging, and personalized emails. 
            You understand the importance of first impressions and always maintain a professional yet warm tone 
            that reflects well on the company's brand and culture.""",
            verbose=True,
            allow_delegation=False,
            llm=self.llm,
            tools=[self.tools['email_sender']]
        )
        
        return {
            'screener': resume_screener,
            'scheduler': interview_scheduler,
            'email_writer': email_draftsman
        }
    
    def process_resumes(self, job_description: str, resume_files: List[str]) -> Dict[str, Any]:
        """Process resumes and return ranked candidates"""
        
        # Task: Screen and rank resumes
        screening_task = Task(
            description=f"""
            Analyze the provided resume files and rank candidates based on their fit for the job.
            
            Job Description:
            {job_description}
            
            Resume Files: {resume_files}
            
            For each resume:
            1. Extract candidate information (name, email, phone)
            2. Analyze skills, experience, and qualifications against job requirements
            3. Assign a match score from 1-10 (10 being perfect match)
            4. Generate 3-5 key bullet points explaining why they're a good/poor fit
            5. Rank all candidates by their scores (highest first)
            
            Return results as a JSON object with this structure:
            {{
                "candidates": [
                    {{
                        "name": "Full Name",
                        "email": "email@example.com",
                        "phone": "phone number (if available)",
                        "score": 8.5,
                        "summary": [
                            "Key strength or qualification 1",
                            "Key strength or qualification 2",
                            "Key strength or qualification 3"
                        ]
                    }}
                ]
            }}
            
            Focus on objective evaluation based on:
            - Relevant work experience
            - Required skills and technologies
            - Education and certifications
            - Career progression and achievements
            """,
            agent=self.agents['screener'],
            expected_output="JSON object with ranked candidates list"
        )
        
        # Execute the screening task
        crew = Crew(
            agents=[self.agents['screener']],
            tasks=[screening_task],
            verbose=True
        )
        
        try:
            result = crew.kickoff()
            
            # Parse JSON result
            if isinstance(result, str):
                candidates_data = json.loads(result)
            else:
                candidates_data = result
            
            logger.info(f"Successfully screened {len(candidates_data.get('candidates', []))} candidates")
            return candidates_data
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error: {str(e)}")
            # Return fallback structure
            return {"candidates": []}
        except Exception as e:
            logger.error(f"Resume screening error: {str(e)}")
            raise
    
    def schedule_interviews(self, candidates: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Schedule interviews for selected candidates"""
        
        # Task 1: Schedule calendar events
        scheduling_task = Task(
            description=f"""
            Schedule 30-minute interview slots for the following candidates:
            {json.dumps(candidates, indent=2)}
            
            Requirements:
            - Find available slots within next 5 business days (Monday-Friday)
            - Business hours: 9:00 AM - 5:00 PM
            - Each interview should be 30 minutes
            - Create calendar events with title: "Interview: [Company Name] - [Candidate Name]"
            - Add interviewer email: interviewer@company.com
            - Include candidate email as attendee
            
            Return the scheduled interviews as JSON:
            {{
                "scheduled_interviews": [
                    {{
                        "candidate_name": "Full Name",
                        "candidate_email": "email@example.com",
                        "interview_date": "2024-01-15",
                        "interview_time": "10:00 AM",
                        "timezone": "EST",
                        "meeting_link": "Google Meet link or TBD"
                    }}
                ]
            }}
            """,
            agent=self.agents['scheduler'],
            expected_output="JSON with scheduled interview details"
        )
        
        # Task 2: Send confirmation emails
        email_task = Task(
            description="""
            Based on the scheduled interviews from the previous task, compose and send personalized 
            interview confirmation emails to each candidate.

            Use this template and fill in the placeholders:

            Subject: Interview Confirmation: [Company Name] - [Candidate Name]

            Dear [Candidate Name],

            Thank you for your interest in the [Job Title] position at [Company Name]. We were impressed with your background and would like to invite you for an interview.

            Your interview has been scheduled for:
            - Date: [Interview Date]
            - Time: [Interview Time] [Timezone]
            - Interviewer: [Interviewer Name]

            The interview will be conducted via [Platform/Location] and a meeting link will be sent shortly. Please take a moment to confirm your availability by replying to this email.

            [Optional: Add any pre-interview instructions or required documents here.]

            We look forward to speaking with you.

            Best regards,
            The [Company Name] Talent Team
            
            Send emails to all candidates and confirm delivery.
            
            Return confirmation as JSON:
            {{
                "emails_sent": [
                    {{
                        "candidate_name": "Full Name",
                        "candidate_email": "email@example.com",
                        "email_sent": true,
                        "send_time": "timestamp"
                    }}
                ]
            }}
            """,
            agent=self.agents['email_writer'],
            expected_output="JSON confirming email delivery",
            context=[scheduling_task]
        )
        
        # Execute both tasks in sequence
        crew = Crew(
            agents=[self.agents['scheduler'], self.agents['email_writer']],
            tasks=[scheduling_task, email_task],
            verbose=True
        )
        
        try:
            result = crew.kickoff()
            
            # Parse final result
            if isinstance(result, str):
                final_result = json.loads(result)
            else:
                final_result = result
            
            logger.info(f"Successfully scheduled interviews for {len(candidates)} candidates")
            
            return {
                "status": "success",
                "message": f"Interviews scheduled and confirmation emails sent to {len(candidates)} candidates",
                "details": final_result
            }
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error in scheduling: {str(e)}")
            return {
                "status": "error",
                "message": "Error processing interview scheduling results"
            }
        except Exception as e:
            logger.error(f"Interview scheduling error: {str(e)}")
            raise

class MockHRAgentCrew:
    """Mock implementation for testing without actual API calls"""
    
    def process_resumes(self, job_description: str, resume_files: List[str]) -> Dict[str, Any]:
        """Mock resume processing for development/testing"""
        import time
        time.sleep(2)  # Simulate processing time
        
        # Generate mock candidates based on uploaded files
        mock_candidates = []
        for i, resume_file in enumerate(resume_files[:5]):  # Limit to 5 for demo
            filename = os.path.basename(resume_file)
            name = filename.replace('.pdf', '').replace('_', ' ').title()
            
            mock_candidates.append({
                "name": f"{name}",
                "email": f"{name.lower().replace(' ', '.')}@email.com",
                "phone": f"555-{100 + i:04d}",
                "score": round(10 - (i * 0.5), 1),  # Decreasing scores
                "summary": [
                    f"Strong background in relevant field with {5-i}+ years experience",
                    f"Excellent technical skills matching job requirements",
                    f"Proven track record of successful project delivery",
                    "Strong communication and leadership abilities" if i < 2 else "Good technical foundation"
                ][:3 + (2 if i < 3 else 0)]
            })
        
        return {"candidates": mock_candidates}
    
    def schedule_interviews(self, candidates: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Mock interview scheduling"""
        import time
        time.sleep(3)  # Simulate scheduling time
        
        return {
            "status": "success",
            "message": f"Successfully scheduled interviews for {len(candidates)} candidates and sent confirmation emails",
            "details": {
                "scheduled_interviews": len(candidates),
                "emails_sent": len(candidates)
            }
        }