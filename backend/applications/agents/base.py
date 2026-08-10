import abc
import os
import re
import logging
from typing import Optional, Dict, Any, List

logger = logging.getLogger(__name__)


class BasePlatformAgent(abc.ABC):
    """
    Abstract base class for platform-specific job application web agents.
    Includes AI-powered helpers for intelligent form filling.
    """

    # ──────────────────────────────────────────────────────────────
    # Abstract methods (must be implemented by subclasses)
    # ──────────────────────────────────────────────────────────────

    @abc.abstractmethod
    def detect(self, page, url: str) -> bool:
        """
        Returns True if this agent is responsible for handling this job offer page.
        """
        pass

    @abc.abstractmethod
    def fill_form(
        self,
        page,
        cv,
        personal_info,
        cover_letter: str,
        skills: List[str],
        experiences: List[Any],
        add_log
    ) -> bool:
        """
        Attempts to locate and fill all required application fields on the page.
        Returns True if at least some fields were filled successfully.
        """
        pass

    @abc.abstractmethod
    def submit_form(self, page, add_log) -> bool:
        """
        Attempts to click the submission button.
        Returns True if the form appears to submit successfully.
        """
        pass

    # ──────────────────────────────────────────────────────────────
    # AI-powered helpers for intelligent form filling
    # ──────────────────────────────────────────────────────────────

    def get_cv_text(self, cv) -> str:
        """Extract raw text from the candidate's CV PDF."""
        if not cv or not cv.raw_file_url:
            return ""
        try:
            from cv_management.adapters.pdf_text_extractor import PdfTextExtractor
            path = cv.raw_file_url
            if not path.startswith("http") and not os.path.exists(path):
                path = f"/app/{path}"
            extractor = PdfTextExtractor()
            return extractor.extract_text(path)
        except Exception as e:
            logger.warning(f"Failed to extract CV text: {e}")
            return ""

    def extract_linkedin(self, cv_text: str) -> str:
        """Extract the real LinkedIn profile URL from the CV text."""
        # Try regex first (fast, reliable)
        match = re.search(r'(https?://(?:www\.)?linkedin\.com/in/[a-zA-Z0-9_-]+/?)', cv_text)
        if match:
            return match.group(1).rstrip("/")

        # LLM fallback
        api_key = os.environ.get("GROQ_API_KEY", "")
        if api_key:
            try:
                from groq import Groq
                client = Groq(api_key=api_key)
                response = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[
                        {"role": "user", "content": f"Extract ONLY the LinkedIn profile URL from this text. Return ONLY the URL, nothing else. If not found, return 'NONE'.\n\n{cv_text[:3000]}"}
                    ],
                    temperature=0.0,
                    max_tokens=80
                )
                res = response.choices[0].message.content.strip()
                if "linkedin.com/in/" in res:
                    return res
            except Exception:
                pass
        return ""

    def extract_github(self, cv_text: str) -> str:
        """Extract the GitHub/Portfolio URL from the CV text."""
        match = re.search(r'(https?://(?:www\.)?github\.com/[a-zA-Z0-9_-]+/?)', cv_text)
        if match:
            return match.group(1).rstrip("/")
        # Also look for portfolio-like links
        match = re.search(r'(https?://[a-zA-Z0-9_.-]+\.(dev|io|com|me|tech)/?\S*)', cv_text)
        if match:
            url = match.group(1)
            if "linkedin" not in url and "gmail" not in url:
                return url
        return ""

    def ask_llm(self, question: str, cv_text: str, cover_letter: str = "", job_description: str = "") -> str:
        """
        Use Groq LLM to generate a smart, concise answer to a custom form question,
        based on the candidate's CV and job context.
        """
        api_key = os.environ.get("GROQ_API_KEY", "")
        if not api_key:
            return ""

        try:
            from groq import Groq
            client = Groq(api_key=api_key)

            prompt = f"""You are filling a job application form on behalf of a candidate. Answer the form question below.

CANDIDATE CV (summary):
{cv_text[:2500]}

COVER LETTER (already generated):
{cover_letter[:800]}

JOB CONTEXT:
{job_description[:500]}

FORM QUESTION:
"{question}"

INSTRUCTIONS:
- If this is a "why are you a good fit?" question, write a compelling 2-3 sentence answer highlighting relevant experience from the CV. Do NOT copy the cover letter verbatim.
- If this asks for salary expectations, give a reasonable range (e.g. "80,000 - 100,000 EUR/year" for a senior role, adjust based on the job level).
- If this is a yes/no question (e.g. B2B contract, visa sponsorship, work authorization), answer with just "Yes" or "No" — prefer "Yes" for flexibility questions.
- If this asks for years of experience, extract the number from the CV.
- If this asks for location/timezone, extract from CV or answer "Europe / CET timezone".
- Keep your answer concise, professional, and directly relevant.
- Answer in the SAME LANGUAGE as the question.
- Return ONLY the answer text, nothing else (no quotes, no labels, no explanation).

ANSWER:"""

            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": "You answer job application form questions on behalf of candidates. Be concise, professional, and accurate."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=200
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.warning(f"LLM ask_llm failed: {e}")
            return ""

    def ask_llm_choose_option(self, question: str, options: List[str], cv_text: str) -> str:
        """
        Use LLM to choose the best option from a list (for radio buttons / dropdowns).
        Returns the exact text of the chosen option.
        """
        api_key = os.environ.get("GROQ_API_KEY", "")
        if not api_key:
            return options[0] if options else ""

        try:
            from groq import Groq
            client = Groq(api_key=api_key)

            options_text = "\n".join([f"- {opt}" for opt in options])
            prompt = f"""A job application form asks:
"{question}"

Available options:
{options_text}

Candidate CV (summary):
{cv_text[:1500]}

Choose the BEST option for this candidate. Return ONLY the exact text of the chosen option, nothing else.
- For B2B/contract flexibility questions, prefer "Yes".
- For visa/sponsorship questions, answer based on the CV nationality/location.
- For work authorization, prefer "Yes" if the candidate is in Europe.

CHOSEN OPTION:"""

            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=0.0,
                max_tokens=50
            )
            chosen = response.choices[0].message.content.strip().strip('"').strip("'")
            # Find closest match in actual options
            for opt in options:
                if chosen.lower() == opt.lower() or chosen.lower() in opt.lower() or opt.lower() in chosen.lower():
                    return opt
            return options[0]
        except Exception as e:
            logger.warning(f"LLM ask_llm_choose_option failed: {e}")
            return options[0] if options else ""

    # ──────────────────────────────────────────────────────────────
    # Blocking detection (shared across all agents)
    # ──────────────────────────────────────────────────────────────

    def detect_blocking(self, page) -> Optional[str]:
        """
        Scans the page for actual blocking walls (Cloudflare challenge, mandatory login).
        Returns the type of block found, or None.
        Only flags CAPTCHA if the page ITSELF is blocked, not just if a captcha widget exists on the form.
        """
        page_content = page.content().lower()
        page_title = page.title().lower()

        # Check for Cloudflare challenge page (the page itself is the challenge)
        cloudflare_signals = [
            "just a moment...",
            "checking your browser",
            "enable javascript and cookies",
            "ray id:",  # Cloudflare ray ID footer
            "cf-browser-verification",
        ]
        if any(signal in page_content for signal in cloudflare_signals):
            return "CLOUDFLARE_CHALLENGE"

        # Check for a full-page blocking CAPTCHA (not embedded in form)
        # Only trigger if the main body content is essentially just a captcha
        try:
            # If there are no visible text paragraphs or headings and there IS a captcha iframe, it's blocking
            captcha_blocking_selectors = ["#cf-challenge-running", "#cf-challenge", "#challenge-form"]
            for sel in captcha_blocking_selectors:
                el = page.query_selector(sel)
                if el and el.is_visible():
                    return "CAPTCHA_OR_CLOUDFLARE_DETECTED"
        except Exception:
            pass

        # Check for Login wall (password input is visible and there's no other content)
        try:
            pass_input = page.query_selector("input[type='password']")
            if pass_input and pass_input.is_visible():
                # Only flag if the page looks like a dedicated login page
                login_indicators = ["sign in", "log in", "connexion", "se connecter", "mot de passe"]
                if any(ind in page_content for ind in login_indicators) and len(page_content) < 50000:
                    return "LOGIN_REQUIRED"
        except Exception:
            pass

        return None
