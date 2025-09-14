"""
Optimized Google Gemini API client for resume parsing
Focuses on efficient token usage and structured data extraction
"""

import os
import json
import logging
from typing import List, Dict, Any, Optional
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

logger = logging.getLogger(__name__)

class GeminiResumeParser:
    """Optimized Gemini API client for resume parsing with minimal token usage"""
    
    def __init__(self):
        self.api_key = os.getenv('GOOGLE_API_KEY')
        if not self.api_key:
            raise ValueError("GOOGLE_API_KEY environment variable is required")
        
        genai.configure(api_key=self.api_key)
        
        # Use Gemini Flash for cost efficiency
        self.model = genai.GenerativeModel(
            'gemini-1.5-flash',
            generation_config=genai.types.GenerationConfig(
                temperature=0.1,
                top_p=0.8,
                top_k=20,
                max_output_tokens=1000  # Limit output tokens
            ),
            safety_settings={
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
            }
        )
    
    def extract_candidate_info(self, resume_text: str) -> Dict[str, Any]:
        """
        Extract basic candidate information from resume text
        Optimized for minimal token usage
        """
        # Truncate resume text to reduce tokens (keep first 2000 chars)
        truncated_text = resume_text[:2000] if len(resume_text) > 2000 else resume_text
        
        prompt = f"""Extract candidate info from this resume. Return ONLY valid JSON:

{truncated_text}

Required JSON format:
{{"name":"","email":"","phone":"","skills":[],"experience_years":0,"education":"","summary":""}}"""

        try:
            response = self.model.generate_content(prompt)
            logger.info(f"Gemini API response: {response.text}")
            # Clean the response to remove markdown
            cleaned_text = response.text.strip().replace('```json', '').replace('```', '')
            result = json.loads(cleaned_text)
            
            # Ensure required fields exist
            return {
                "name": result.get("name", "Unknown"),
                "email": result.get("email", ""),
                "phone": result.get("phone", ""),
                "skills": result.get("skills", [])[:10],  # Limit skills
                "experience_years": result.get("experience_years", 0),
                "education": result.get("education", ""),
                "summary": result.get("summary", "")[:200]  # Limit summary
            }
            
        except Exception as e:
            logger.error(f"Error extracting candidate info: {str(e)}")
            return {
                "name": "Parse Error",
                "email": "",
                "phone": "",
                "skills": [],
                "experience_years": 0,
                "education": "",
                "summary": "Failed to parse resume"
            }
    
    def score_candidate(self, candidate_info: Dict[str, Any], job_requirements: str) -> Dict[str, Any]:
        """
        Score candidate against job requirements
        Uses condensed job requirements to reduce tokens
        """
        # Extract key requirements from job description (first 1000 chars)
        condensed_job = job_requirements[:1000] if len(job_requirements) > 1000 else job_requirements
        
        # Create concise candidate summary
        candidate_summary = f"""
Name: {candidate_info['name']}
Experience: {candidate_info['experience_years']} years
Skills: {', '.join(candidate_info['skills'][:5])}
Education: {candidate_info['education'][:100]}
"""
        
        prompt = f"""Score this candidate (1-100) for the job. Return ONLY valid JSON:

JOB: {condensed_job}

CANDIDATE: {candidate_summary}

Required JSON format:
{{"score":0,"reasons":["reason1","reason2","reason3"]}}"""

        try:
            response = self.model.generate_content(prompt)
            logger.info(f"Gemini API response for scoring: {response.text}")
            # Clean the response to remove markdown
            cleaned_text = response.text.strip().replace('```json', '').replace('```', '')
            result = json.loads(cleaned_text)
            
            return {
                "score": min(100, max(1, float(result.get("score", 50)))),
                "reasons": result.get("reasons", ["Unable to assess"])[:3]
            }
            
        except Exception as e:
            logger.error(f"Error scoring candidate: {str(e)}")
            return {
                "score": 50.0,
                "reasons": ["Error in assessment"]
            }
    
    def batch_process_resumes(self, resume_texts: Dict[str, str], job_description: str) -> List[Dict[str, Any]]:
        """
        Process multiple resumes efficiently
        """
        logger.info("Starting batch resume processing...")
        candidates = []
        
        # Extract key job requirements once to reuse
        job_keywords = self._extract_job_keywords(job_description)
        
        for file_path, resume_text in resume_texts.items():
            try:
                logger.info(f"Processing resume: {os.path.basename(file_path)}")
                # Extract candidate info
                candidate_info = self.extract_candidate_info(resume_text)
                logger.info(f"  - Extracted info for: {candidate_info.get('name', 'Unknown')}")
                
                # Quick scoring based on keyword matching (reduces API calls)
                quick_score = self._quick_score(candidate_info, job_keywords)
                
                # Only use API for detailed scoring if quick score is promising (>6)
                if quick_score > 6:
                    logger.info(f"  - Performing detailed scoring for {candidate_info.get('name', 'Unknown')}")
                    detailed_score = self.score_candidate(candidate_info, job_description)
                    final_score = detailed_score["score"]
                    reasons = detailed_score["reasons"]
                else:
                    logger.info(f"  - Performing quick scoring for {candidate_info.get('name', 'Unknown')}")
                    final_score = quick_score
                    reasons = self._generate_quick_reasons(candidate_info, job_keywords)
                
                logger.info(f"  - Finished scoring for {candidate_info.get('name', 'Unknown')}. Score: {final_score}")
                candidates.append({
                    "name": candidate_info["name"],
                    "email": candidate_info["email"],
                    "phone": candidate_info["phone"],
                    "score": final_score,
                    "summary": reasons
                })
                
            except Exception as e:
                logger.error(f"Error processing resume {file_path}: {str(e)}")
                continue
        
        # Sort by score (highest first)
        candidates.sort(key=lambda x: x["score"], reverse=True)
        logger.info("Batch resume processing complete.")
        return candidates
    
    def _extract_job_keywords(self, job_description: str) -> List[str]:
        """Extract key skills/requirements from job description"""
        # Simple keyword extraction (could be enhanced)
        common_skills = [
            'python', 'javascript', 'react', 'node.js', 'sql', 'aws', 'docker',
            'kubernetes', 'git', 'agile', 'scrum', 'machine learning', 'ai',
            'data science', 'backend', 'frontend', 'full stack', 'devops'
        ]
        
        job_lower = job_description.lower()
        found_keywords = [skill for skill in common_skills if skill in job_lower]
        
        return found_keywords
    
    def _quick_score(self, candidate_info: Dict[str, Any], job_keywords: List[str]) -> float:
        """
        Quick scoring based on keyword matching
        Reduces need for API calls
        """
        if not job_keywords:
            return 50.0
        
        candidate_skills = [skill.lower() for skill in candidate_info.get("skills", [])]
        candidate_text = f"{candidate_info.get('summary', '')} {' '.join(candidate_skills)}".lower()
        
        matches = sum(1 for keyword in job_keywords if keyword in candidate_text)
        match_ratio = matches / len(job_keywords)
        
        # Base score on experience and keyword matches
        experience_score = min(candidate_info.get("experience_years", 0) / 5 * 30, 30)
        keyword_score = match_ratio * 50
        education_score = 20 if candidate_info.get("education") else 10
        
        total_score = experience_score + keyword_score + education_score
        return min(100, max(1, total_score))
    
    def _generate_quick_reasons(self, candidate_info: Dict[str, Any], job_keywords: List[str]) -> List[str]:
        """Generate assessment reasons without API call"""
        reasons = []
        
        exp_years = candidate_info.get("experience_years", 0)
        if exp_years >= 5:
            reasons.append(f"Strong experience with {exp_years}+ years in the field")
        elif exp_years >= 2:
            reasons.append(f"Good experience with {exp_years} years in the field")
        else:
            reasons.append("Limited professional experience")
        
        skills = candidate_info.get("skills", [])
        if len(skills) >= 5:
            reasons.append(f"Diverse skill set including {', '.join(skills[:3])}")
        elif len(skills) >= 2:
            reasons.append(f"Relevant skills in {', '.join(skills)}")
        else:
            reasons.append("Limited technical skills listed")
        
        if candidate_info.get("education"):
            reasons.append("Has relevant educational background")
        
        return reasons[:3]

class MockGeminiResumeParser:
    """Mock implementation for development without API usage"""
    
    def batch_process_resumes(self, resume_texts: Dict[str, str], job_description: str) -> List[Dict[str, Any]]:
        """Mock resume processing"""
        candidates = []
        
        for i, (file_path, resume_text) in enumerate(resume_texts.items()):
            filename = os.path.basename(file_path)
            name = filename.replace('.pdf', '').replace('_', ' ').title()
            
            candidates.append({
                "name": name,
                "email": f"{name.lower().replace(' ', '.')}@email.com",
                "phone": f"555-{1000 + i:04d}",
                "score": round(9 - (i * 0.8), 1),
                "summary": [
                    f"Strong technical background with {5-i}+ years experience",
                    f"Excellent match for required skills and qualifications",
                    "Proven track record of successful project delivery"
                ][:3]
            })
        
        return candidates