"""Quiz solver using Playwright and OpenAI."""
import asyncio
import json
import logging
import re
import sys
from datetime import datetime, timedelta
from typing import Any, Dict, Optional
from playwright.async_api import async_playwright, Page
import requests
from openai import OpenAI

import config
from data_processor import DataProcessor
from prompts import (
    QUIZ_SOLVER_SYSTEM_PROMPT,
    CODE_GENERATION_PROMPT,
    ANSWER_EXTRACTION_PROMPT
)

logger = logging.getLogger(__name__)

class QuizSolver:
    """Solve quiz tasks using browser automation and LLM."""
    
    def __init__(self):
        # Fix for Windows + Python 3.13 + Playwright async compatibility
        if sys.platform == 'win32':
            asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
        
        self.client = OpenAI(api_key=config.OPENAI_API_KEY)
        self.data_processor = DataProcessor()
        self.start_time = None
    
    def _is_timeout_exceeded(self) -> bool:
        """Check if 3-minute timeout has been exceeded."""
        if not self.start_time:
            return False
        elapsed = (datetime.now() - self.start_time).total_seconds()
        return elapsed > config.QUIZ_TIMEOUT_SECONDS
    
    async def solve_quiz_chain(self, initial_url: str):
        """
        Solve a chain of quizzes starting from the initial URL.
        
        Args:
            initial_url: Starting quiz URL
        """
        self.start_time = datetime.now()
        current_url = initial_url
        attempt_count = 0
        
        logger.info(f"Starting quiz chain from {initial_url}")
        
        while current_url and not self._is_timeout_exceeded():
            try:
                logger.info(f"Solving quiz at {current_url}")
                result = await self.solve_single_quiz(current_url)
                
                if result.get("correct"):
                    logger.info(f"✓ Correct answer for {current_url}")
                    current_url = result.get("url")  # Get next quiz URL
                    attempt_count = 0  # Reset attempts for new quiz
                else:
                    logger.warning(f"✗ Wrong answer for {current_url}: {result.get('reason')}")
                    attempt_count += 1
                    
                    # Check if we should retry or move to next
                    next_url = result.get("url")
                    if next_url and next_url != current_url:
                        # New quiz provided, move to it
                        logger.info(f"Moving to next quiz: {next_url}")
                        current_url = next_url
                        attempt_count = 0
                    elif attempt_count >= config.MAX_RETRIES:
                        logger.error(f"Max retries exceeded for {current_url}")
                        break
                    # else: retry the same quiz
                
            except Exception as e:
                logger.error(f"Error solving quiz {current_url}: {e}", exc_info=True)
                break
        
        if self._is_timeout_exceeded():
            logger.warning("Quiz chain stopped: timeout exceeded")
        else:
            logger.info("Quiz chain completed successfully")
    
    async def solve_single_quiz(self, quiz_url: str) -> Dict[str, Any]:
        """
        Solve a single quiz.
        
        Args:
            quiz_url: URL of the quiz
            
        Returns:
            Response from submission endpoint
        """
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            try:
                # Navigate to quiz page
                logger.info(f"Loading quiz page: {quiz_url}")
                await page.goto(quiz_url, timeout=config.BROWSER_TIMEOUT_MS)
                await page.wait_for_load_state("networkidle")
                
                # Get rendered HTML content
                content = await page.content()
                text_content = await page.inner_text("body")
                
                logger.info(f"Quiz page loaded, content length: {len(text_content)}")
                
                # Extract quiz information using LLM
                quiz_info = self._extract_quiz_info(text_content)
                logger.info(f"Extracted quiz info: {quiz_info}")
                
                # Solve the quiz
                answer = await self._solve_quiz(quiz_info, page)
                logger.info(f"Generated answer: {answer}")
                
                # Submit the answer
                result = self._submit_answer(
                    quiz_info["submit_url"],
                    quiz_url,
                    answer
                )
                
                return result
                
            finally:
                await browser.close()
    
    def _extract_quiz_info(self, content: str) -> Dict[str, Any]:
        """
        Extract quiz information from page content using LLM.
        
        Args:
            content: Page text content
            
        Returns:
            Dictionary with question, answer_type, data_sources, submit_url
        """
        try:
            response = self.client.chat.completions.create(
                model=config.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": "You extract structured information from quiz questions. Return valid JSON only."},
                    {"role": "user", "content": ANSWER_EXTRACTION_PROMPT.format(content=content[:4000])}
                ],
                temperature=0.1,
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            logger.info(f"LLM extracted quiz info: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Error extracting quiz info: {e}")
            # Fallback: try to extract submit URL manually
            submit_url_match = re.search(r'https://[^\s<>"]+/submit', content)
            return {
                "question": content[:500],
                "answer_type": "string",
                "data_sources": [],
                "submit_url": submit_url_match.group(0) if submit_url_match else ""
            }
    
    async def _solve_quiz(self, quiz_info: Dict[str, Any], page: Page) -> Any:
        """
        Solve the quiz using LLM to generate and execute code.
        
        Args:
            quiz_info: Extracted quiz information
            page: Playwright page object
            
        Returns:
            The answer to submit
        """
        question = quiz_info["question"]
        answer_type = quiz_info.get("answer_type", "string")
        
        # Generate solution code using LLM
        code = self._generate_solution_code(question)
        
        # Execute the code safely
        answer = self._execute_solution_code(code, quiz_info)
        
        # Format answer based on type
        return self._format_answer(answer, answer_type)
    
    def _generate_solution_code(self, question: str) -> str:
        """
        Generate Python code to solve the quiz using LLM.
        
        Args:
            question: The quiz question
            
        Returns:
            Python code as string
        """
        try:
            response = self.client.chat.completions.create(
                model=config.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": QUIZ_SOLVER_SYSTEM_PROMPT},
                    {"role": "user", "content": CODE_GENERATION_PROMPT.format(question=question)}
                ],
                temperature=0.2
            )
            
            code = response.choices[0].message.content
            
            # Extract code from markdown if present
            if "```python" in code:
                code = re.search(r'```python\n(.*?)```', code, re.DOTALL).group(1)
            elif "```" in code:
                code = re.search(r'```\n(.*?)```', code, re.DOTALL).group(1)
            
            logger.info(f"Generated code:\n{code}")
            return code
            
        except Exception as e:
            logger.error(f"Error generating code: {e}")
            return "answer = None"
    
    def _execute_solution_code(self, code: str, quiz_info: Dict[str, Any]) -> Any:
        """
        Execute the generated solution code safely.
        
        Args:
            code: Python code to execute
            quiz_info: Quiz information
            
        Returns:
            The answer variable from executed code
        """
        # Create safe execution environment
        safe_globals = {
            "requests": requests,
            "pd": __import__("pandas"),
            "np": __import__("numpy"),
            "BeautifulSoup": __import__("bs4").BeautifulSoup,
            "data_processor": self.data_processor,
            "json": json,
            "re": re,
            "base64": __import__("base64"),
        }
        
        safe_locals = {}
        
        try:
            exec(code, safe_globals, safe_locals)
            answer = safe_locals.get("answer")
            logger.info(f"Code executed successfully, answer: {answer}")
            return answer
        except Exception as e:
            logger.error(f"Error executing code: {e}", exc_info=True)
            # Fallback: try to answer with LLM directly
            return self._llm_direct_answer(quiz_info["question"])
    
    def _llm_direct_answer(self, question: str) -> str:
        """
        Get direct answer from LLM without code execution.
        
        Args:
            question: The quiz question
            
        Returns:
            Direct answer
        """
        try:
            response = self.client.chat.completions.create(
                model=config.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": QUIZ_SOLVER_SYSTEM_PROMPT},
                    {"role": "user", "content": f"Answer this question directly, return only the answer:\n{question}"}
                ],
                temperature=0.1
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"Error getting direct answer: {e}")
            return ""
    
    def _format_answer(self, answer: Any, answer_type: str) -> Any:
        """
        Format answer based on expected type.
        
        Args:
            answer: Raw answer
            answer_type: Expected type (number, string, boolean, file, json)
            
        Returns:
            Formatted answer
        """
        if answer is None:
            return None
        
        if answer_type == "number":
            try:
                return float(answer) if '.' in str(answer) else int(answer)
            except:
                return answer
        elif answer_type == "boolean":
            if isinstance(answer, bool):
                return answer
            return str(answer).lower() in ['true', 'yes', '1']
        elif answer_type == "json":
            if isinstance(answer, (dict, list)):
                return answer
            try:
                return json.loads(answer)
            except:
                return answer
        else:
            return answer
    
    def _submit_answer(self, submit_url: str, quiz_url: str, answer: Any) -> Dict[str, Any]:
        """
        Submit answer to the endpoint.
        
        Args:
            submit_url: Submission endpoint URL
            quiz_url: Original quiz URL
            answer: The answer to submit
            
        Returns:
            Response from server
        """
        payload = {
            "email": config.STUDENT_EMAIL,
            "secret": config.STUDENT_SECRET,
            "url": quiz_url,
            "answer": answer
        }
        
        logger.info(f"Submitting answer to {submit_url}")
        logger.info(f"Payload: {json.dumps(payload, indent=2)}")
        
        try:
            response = requests.post(
                submit_url,
                json=payload,
                timeout=30
            )
            
            result = response.json()
            logger.info(f"Submission response: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Error submitting answer: {e}")
            return {"correct": False, "reason": str(e)}
