import os
import time
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
from groq import Groq
from playwright.sync_api import sync_playwright

from applications.ports.application_channel import IApplicationChannel
from applications.agents.greenhouse import GreenhouseAgent
from applications.agents.lever import LeverAgent
from applications.agents.ashby import AshbyAgent
from applications.agents.gem import GemAgent
from applications.agents.generic import GenericAgent

logger = logging.getLogger(__name__)


class PlaywrightApplicationChannel(IApplicationChannel):
    """
    Adapter implementing autonomous web applications using Playwright headless browser
    and specialized platform agents (Greenhouse, Lever, Generic).
    """

    def __init__(self):
        self.groq_api_key = os.environ.get("GROQ_API_KEY", "")
        self.groq_client = Groq(api_key=self.groq_api_key) if self.groq_api_key else None
        # Register specialized platform agents (ordered by priority)
        self.agents = [
            GreenhouseAgent(),
            LeverAgent(),
            GemAgent(),
            AshbyAgent(),
            GenericAgent()  # Generic fallback must be last
        ]

    def _generate_cover_letter(self, candidate_name: str, job_title: str, company: str, match_summary: str) -> str:
        """Generates a professional, personalized cover letter using Groq LLM."""
        if not self.groq_client:
            return f"""Madame, Monsieur,

Je souhaite poser ma candidature pour le poste de {job_title} chez {company}.
Fort de mon parcours, je serais ravi d'apporter mes compétences à votre équipe.

Cordialement,
{candidate_name}"""

        prompt = f"""Rédige une lettre de motivation professionnelle, courtoise et percutante en français (max 200 mots) pour poser ma candidature au poste ci-dessous.

Candidat : {candidate_name}
Poste : {job_title}
Entreprise : {company}
Synthèse de compatibilité : {match_summary}

Ne mets pas d'en-tête de date ni d'adresse. Commence par 'Madame, Monsieur,' et termine par la signature du candidat."""

        try:
            response = self.groq_client.chat.completions.create(
                messages=[
                    {"role": "system", "content": "Tu es un assistant RH spécialisé dans la rédaction de lettres de motivation percutantes."},
                    {"role": "user", "content": prompt}
                ],
                model="llama-3.3-70b-versatile",
                temperature=0.6,
                max_tokens=400,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.warning(f"Error generating cover letter via Groq: {e}")
            return f"""Madame, Monsieur,

Je postule avec enthousiasme au poste de {job_title} chez {company}.
{match_summary}

Cordialement,
{candidate_name}"""

    def submit(
        self,
        application,
        cv,
        job_offer,
        candidate_email: Optional[str] = None,
        match=None,
        personal_info=None,
        experiences=None,
        skills=None
    ) -> Dict[str, Any]:
        logs: List[Dict[str, Any]] = []
        screenshots: Dict[str, str] = {}
        
        def add_log(step: str, message: str, status: str = "INFO"):
            entry = {
                "timestamp": datetime.utcnow().strftime("%H:%M:%S"),
                "step": step,
                "message": message,
                "status": status
            }
            logs.append(entry)
            logger.info(f"[{step}] {message}")

        candidate_name = personal_info.full_name if personal_info and personal_info.full_name else "Candidat"
        email_to_use = candidate_email or (personal_info.email if personal_info else "candidat@example.com")

        # 1. Generate Cover Letter
        add_log("1_COVER_LETTER", "Génération de la lettre de motivation personnalisée via Groq LLM...")
        summary_text = match.summary if match and match.summary else "Profil compatible avec le poste."
        cover_letter = self._generate_cover_letter(candidate_name, job_offer.title, job_offer.company, summary_text)
        add_log("1_COVER_LETTER", "Lettre de motivation générée avec succès.", "SUCCESS")

        # Create screenshot output dir
        app_id_str = str(application.id)
        rel_dir = f"screenshots/applications/{app_id_str}"
        abs_dir = os.path.join("/app/static", rel_dir)
        os.makedirs(abs_dir, exist_ok=True)

        url = job_offer.source_url
        if not url:
            add_log("2_NAVIGATION", "Aucune URL source disponible pour cette offre.", "ERROR")
            return {
                "success": False,
                "error_message": "Aucune URL source pour cette offre d'emploi.",
                "cover_letter": cover_letter,
                "execution_logs": logs,
                "screenshots": screenshots
            }

        add_log("2_NAVIGATION", f"Lancement du navigateur Playwright (Chromium headless) vers {url}...")

        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(
                    headless=True,
                    args=["--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage"]
                )
                context = browser.new_context(
                    viewport={"width": 1280, "height": 2200},
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                )
                page = context.new_page()
                
                # Apply stealth to bypass bot detection
                try:
                    from playwright_stealth import Stealth
                    stealth_obj = Stealth()
                    stealth_obj.apply_stealth_sync(page)
                    add_log("2_NAVIGATION", "Mode Stealth activé avec succès.", "SUCCESS")
                except Exception as stealth_err:
                    add_log("2_NAVIGATION", f"Stealth non disponible: {str(stealth_err)}", "WARNING")

                # Open page
                try:
                    page.goto(url, wait_until="domcontentloaded", timeout=30000)
                    time.sleep(2)
                except Exception as goto_err:
                    add_log("2_NAVIGATION", f"Chargement partiel de la page: {str(goto_err)}", "WARNING")

                # Screenshot 1: Page opened
                img1_rel = f"/static/{rel_dir}/step1_opened.png"
                img1_abs = os.path.join(abs_dir, "step1_opened.png")
                page.screenshot(path=img1_abs, full_page=True)
                screenshots["step1_opened"] = img1_rel
                page_title = page.title()
                add_log("2_NAVIGATION", f"Page d'origine ouverte : '{page_title}'. Capture d'écran enregistrée.", "SUCCESS")

                # --- NEW TAB & EXTERNAL REDIRECTION HANDLING ---
                add_log("3_REDIRECT_HANDLING", "Vérification de la présence d'un bouton d'application externe...")
                
                apply_selectors = [
                    # Generic text-based
                    "a:has-text('Apply')", "button:has-text('Apply')",
                    "a:has-text('Postuler')", "button:has-text('Postuler')",
                    "a:has-text('Apply Now')", "button:has-text('Apply Now')",
                    "a:has-text('Apply for this job')", "a:has-text('Apply for this position')",
                    # Remotive specific
                    "a.btn-apply", "a[class*='apply']", "button[class*='apply']",
                    # Arbeitnow specific
                    "a.btn-primary[href*='apply']", "a[href*='/apply']",
                    # Common patterns
                    "[data-testid*='apply']", ".apply-button", "#apply-button",
                    "a[href*='greenhouse']", "a[href*='lever.co']", "a[href*='ashby']",
                    "a[href*='workable']", "a[href*='jobs.']",
                ]

                apply_element = None
                for sel in apply_selectors:
                    try:
                        el = page.query_selector(sel)
                        if el and el.is_visible():
                            apply_element = el
                            break
                    except Exception:
                        continue

                if apply_element:
                    # Check if it has a direct href we can navigate to
                    href = None
                    try:
                        href = apply_element.get_attribute("href")
                    except Exception:
                        pass

                    if href and href.startswith("http"):
                        add_log("3_REDIRECT_HANDLING", f"Lien d'application direct trouvé : {href}. Redirection en cours...", "INFO")
                        page.goto(href, wait_until="domcontentloaded", timeout=30000)
                        time.sleep(3)
                        
                        # Refresh screenshot 1 with true target page
                        page.screenshot(path=img1_abs, full_page=True)
                        add_log("3_REDIRECT_HANDLING", f"Redirigé vers la page de candidature : '{page.title()}'", "SUCCESS")
                    else:
                        # Attempt to click it and catch new tab if it opens
                        add_log("3_REDIRECT_HANDLING", "Clic sur le bouton d'application dynamique (attente nouvel onglet)...", "INFO")
                        try:
                            with context.expect_page(timeout=10000) as new_page_info:
                                apply_element.click()
                            
                            # Switch context to the new page/tab
                            new_page = new_page_info.value
                            new_page.wait_for_load_state("domcontentloaded")
                            time.sleep(3)
                            
                            # Apply stealth on new page
                            try:
                                from playwright_stealth import stealth
                                stealth(new_page)
                            except Exception:
                                pass

                            # Switch main page pointer
                            page = new_page
                            # Update main screenshot with target tab content
                            page.screenshot(path=img1_abs, full_page=True)
                            add_log("3_REDIRECT_HANDLING", f"Nouvel onglet détecté et activé : '{page.title()}'", "SUCCESS")
                        except Exception as click_err:
                            add_log("3_REDIRECT_HANDLING", f"Pas de redirection d'onglet détectée ou erreur : {str(click_err)}. Poursuite sur la page actuelle.", "INFO")
                else:
                    add_log("3_REDIRECT_HANDLING", "Aucun bouton d'application externe détecté. Recherche directe du formulaire.", "INFO")

                # Detect active specialized platform agent on the REAL target page
                active_agent = None
                for agent in self.agents:
                    if agent.detect(page, page.url):
                        active_agent = agent
                        break

                agent_name = active_agent.__class__.__name__
                add_log("3_AGENT_SELECTION", f"Agent de plateforme sélectionné pour le formulaire : {agent_name}", "SUCCESS")

                # Check for blocking walls (CAPTCHA or Login) before filling
                add_log("4_BLOCK_CHECK", "Analyse de la page à la recherche de CAPTCHA ou de connexion requise...")
                block_reason = active_agent.detect_blocking(page)
                if block_reason:
                    add_log("4_BLOCK_CHECK", f"Blocage détecté : {block_reason}. Tentative de résolution active avec le mode Stealth (attente 20s)...", "WARNING")
                    
                    resolved = False
                    # Wait up to 20 seconds, checking every 4 seconds
                    for i in range(5):
                        time.sleep(4)
                        # Check again
                        current_block = active_agent.detect_blocking(page)
                        # Take refreshed screenshot of the waiting state
                        img2_rel = f"/static/{rel_dir}/step2_filled.png"
                        img2_abs = os.path.join(abs_dir, "step2_filled.png")
                        page.screenshot(path=img2_abs, full_page=True)
                        screenshots["step2_filled"] = img2_rel

                        if not current_block:
                            add_log("4_BLOCK_CHECK", "Blocage contourné avec succès par l'agent Stealth !", "SUCCESS")
                            resolved = True
                            break
                        else:
                            add_log("4_BLOCK_CHECK", f"Toujours bloqué... essai {i+1}/5.", "INFO")
                    
                    if not resolved:
                        add_log("4_BLOCK_CHECK", f"Blocage persistant après attente. Statut mis à jour en Action Requise.", "WARNING")
                        browser.close()
                        return {
                            "success": True,
                            "status": "MANUAL_REQUIRED",
                            "error_message": f"Action humaine requise : {block_reason}. Veuillez résoudre le CAPTCHA ou vous connecter sur le site de l'offre.",
                            "cover_letter": cover_letter,
                            "execution_logs": logs,
                            "screenshots": screenshots
                        }

                add_log("4_BLOCK_CHECK", "Aucun mur de blocage actif détecté. Poursuite de la candidature.", "SUCCESS")

                # Fill the form using the active agent
                filled_success = active_agent.fill_form(
                    page=page,
                    cv=cv,
                    personal_info=personal_info,
                    cover_letter=cover_letter,
                    skills=skills or [],
                    experiences=experiences or [],
                    add_log=add_log
                )

                # Screenshot 2: Form filled
                img2_rel = f"/static/{rel_dir}/step2_filled.png"
                img2_abs = os.path.join(abs_dir, "step2_filled.png")
                page.screenshot(path=img2_abs, full_page=True)
                screenshots["step2_filled"] = img2_rel

                if not filled_success:
                    add_log("5_FILLING_FIELDS", "L'agent n'a trouvé aucun champ de formulaire modifiable. Soumission annulée par sécurité.", "WARNING")
                    # Take screenshot and return MANUAL_REQUIRED — never submit an empty form
                    page.screenshot(path=img2_abs, full_page=True)
                    screenshots["step2_filled"] = img2_rel
                    browser.close()
                    return {
                        "success": True,
                        "status": "MANUAL_REQUIRED",
                        "error_message": "Champs non remplis : le formulaire n'a pas pu être analysé automatiquement. Veuillez remplir et soumettre manuellement via la lettre de motivation ci-dessous.",
                        "cover_letter": cover_letter,
                        "execution_logs": logs,
                        "screenshots": screenshots
                    }
                else:
                    add_log("5_FILLING_FIELDS", "Formulaire rempli avec succès par l'agent.", "SUCCESS")

                # Attempt to click submit ONLY if fields were filled
                submit_clicked = active_agent.submit_form(page, add_log)

                # Verify if submission actually succeeded (not just clicked)
                submitted = False
                error_msg = "Champs de base remplis, mais des questions spécifiques à l'offre (ex: salaire, contrat) nécessitent votre saisie manuelle pour finaliser."
                
                if submit_clicked:
                    time.sleep(4)  # Let pages load/redirect
                    
                    # Verification logic
                    success_urls = ["thank", "success", "submit", "confirm", "done", "received", "complete"]
                    success_texts = [
                        "thank you", "thanks", "received", "submitted", "confirmation",
                        "merci", "candidature reçue", "succès", "félicitations"
                    ]
                    
                    current_url = page.url.lower()
                    page_content = page.content().lower()
                    
                    # Check URL and content
                    url_success = any(s in current_url for s in success_urls)
                    content_success = any(t in page_content for t in success_texts) and not any(err in page_content for err in ["please enter", "required field", "is required"])
                    
                    if url_success or content_success:
                        submitted = True
                        add_log("6_SUBMISSION", "Validation de soumission réussie (confirmation détectée).", "SUCCESS")
                    else:
                        # Check for security/verification code
                        if any(w in page_content for w in ["verification code", "security code", "verification_code", "security_code", "code de vérification", "code de sécurité", "saisir le code"]):
                            error_msg = "Intervention requise : Un code de vérification vous a été envoyé par email. Veuillez finaliser la soumission en saisissant ce code."
                            add_log("6_SUBMISSION", "Détection d'un code de vérification / sécurité requis par l'entreprise.", "WARNING")
                        elif any(w in page_content for w in ["captcha", "recaptcha", "google.com/recaptcha", "hcaptcha"]):
                            error_msg = "Intervention requise : Un CAPTCHA bloque la soumission automatique. Veuillez finaliser manuellement."
                            add_log("6_SUBMISSION", "Détection d'un CAPTCHA bloquant la soumission automatique.", "WARNING")
                        
                        # Check if form inputs are still visible in any of the frames
                        try:
                            any_visible_inputs = False
                            for frame in page.frames:
                                try:
                                    inputs = frame.locator(
                                        "input[type='text'], input[type='email'], input[type='tel'], input[type='url'], input:not([type])"
                                    )
                                    count = inputs.count()
                                    for idx in range(count):
                                        if inputs.nth(idx).is_visible():
                                            any_visible_inputs = True
                                            break
                                except Exception:
                                    continue
                                if any_visible_inputs:
                                    break
                            
                            if not any_visible_inputs:
                                submitted = True
                                add_log("6_SUBMISSION", "Formulaire disparu (champs invisibles). Soumission probablement réussie.", "SUCCESS")
                        except Exception:
                            pass
                        
                        if not submitted:
                            add_log("6_SUBMISSION", "La page du formulaire est toujours active. Soumission incomplète (champs requis manquants).", "WARNING")

                # Screenshot 3: Final result (taken after verification wait to see confirmation or errors)
                img3_rel = f"/static/{rel_dir}/step3_result.png"
                img3_abs = os.path.join(abs_dir, "step3_result.png")
                page.screenshot(path=img3_abs, full_page=True)
                screenshots["step3_result"] = img3_rel

                browser.close()

                if submitted:
                    add_log("6_SUBMISSION", "Candidature soumise avec succès !", "SUCCESS")
                    return {
                        "success": True,
                        "status": "SENT",
                        "error_message": None,
                        "cover_letter": cover_letter,
                        "execution_logs": logs,
                        "screenshots": screenshots
                    }
                else:
                    add_log("6_SUBMISSION", "La soumission automatique n'a pas pu être finalisée. Soumission manuelle requise pour les champs restants.", "WARNING")
                    return {
                        "success": True,
                        "status": "MANUAL_REQUIRED",
                        "error_message": error_msg,
                        "cover_letter": cover_letter,
                        "execution_logs": logs,
                        "screenshots": screenshots
                    }

        except Exception as e:
            logger.error(f"Playwright execution failed: {e}", exc_info=True)
            add_log("ERROR", f"Erreur fatale lors de l'exécution de l'agent : {str(e)}", "ERROR")
            return {
                "success": False,
                "status": "FAILED",
                "error_message": str(e),
                "cover_letter": cover_letter,
                "execution_logs": logs,
                "screenshots": screenshots
            }
