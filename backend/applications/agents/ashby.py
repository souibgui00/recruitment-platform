import time
import os
from typing import List, Any
from applications.agents.base import BasePlatformAgent


class AshbyAgent(BasePlatformAgent):
    """
    Agent specialized in Ashby HQ job boards (careers.ashbyhq.com or similar self-hosted).
    Ashby uses a tabbed layout: 'Job Description' | 'Apply' tabs.
    After clicking Apply, a form is revealed — either inline (Gem widget) or in an iframe.
    Uses AI (Groq LLM) to intelligently fill custom fields.
    """

    def detect(self, page, url: str) -> bool:
        # Detect Ashby by URL, tab structure, global objects, or iframes
        url_lower = url.lower()
        if "ashbyhq.com" in url_lower or "ashby" in url_lower:
            return True
        try:
            # Check for Ashby global object or ashby specific classes
            is_ashby = page.evaluate("() => typeof window.Ashby !== 'undefined' || document.querySelector('.ashby-job-board') !== null")
            if is_ashby:
                return True
                
            # Check for tabs
            tab = page.query_selector("button:has-text('Apply'), a:has-text('Apply')")
            desc_tab = page.query_selector("button:has-text('Job Description'), a:has-text('Job Description')")
            if tab and desc_tab:
                return True
                
            # Check for ashby iframe
            for frame in page.frames:
                if "ashbyhq.com" in (frame.url or "").lower():
                    return True
        except Exception:
            pass
        return False

    def _get_form_context(self, page, add_log):
        """
        After Apply tab is clicked, find the best context for form filling.
        Checks for iframe (ashby/gem), then falls back to main page.
        """
        all_frames = page.frames
        add_log("FILL_ASHBY", f"{len(all_frames)} frame(s) détectée(s) sur la page.", "INFO")

        for frame in all_frames:
            frame_url = frame.url or ""
            if frame_url and frame_url != "about:blank" and frame_url != page.url:
                add_log("FILL_ASHBY", f"Frame externe : {frame_url}", "INFO")
                try:
                    test_el = frame.query_selector("input, textarea")
                    if test_el:
                        add_log("FILL_ASHBY", f"Formulaire trouvé dans la frame : {frame_url}", "SUCCESS")
                        return frame, ("gem" in frame_url.lower())
                except Exception:
                    continue

        # No external frame found — form is inline in the main page
        add_log("FILL_ASHBY", "Formulaire inline détecté dans la page principale.", "INFO")
        return page, False

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
        add_log("FILL_ASHBY", "Interface Ashby détectée. Clic sur l'onglet 'Apply'...")
        fields_filled = 0

        # Step 1: Click the Apply tab
        try:
            apply_tab = page.query_selector("button:has-text('Apply'), a:has-text('Apply')")
            if apply_tab and apply_tab.is_visible():
                apply_tab.click()
                add_log("FILL_ASHBY", "Onglet 'Apply' cliqué. Attente du chargement du formulaire (6s)...", "SUCCESS")
                time.sleep(6)
            else:
                add_log("FILL_ASHBY", "Onglet 'Apply' non trouvé. Recherche directe des champs...", "WARNING")
                time.sleep(2)
        except Exception as e:
            add_log("FILL_ASHBY", f"Erreur clic onglet Apply : {str(e)}", "WARNING")

        # Step 2: Resolve form context (iframe or main page)
        form_ctx, is_gem = self._get_form_context(page, add_log)

        # Step 3: If Gem detected in frame URL, delegate to GemAgent
        if is_gem:
            add_log("FILL_ASHBY", "Widget Gem.com détecté. Délégation au GemAgent...", "SUCCESS")
            from applications.agents.gem import GemAgent
            return GemAgent().fill_form(page, cv, personal_info, cover_letter, skills, experiences, add_log)

        # Step 4: Check if inline form looks like Gem (by page content)
        try:
            page_content = page.content().lower()
            if "gem.com" in page_content or "powered by gem" in page_content:
                add_log("FILL_ASHBY", "Widget Gem inline détecté dans le DOM. Délégation au GemAgent...", "SUCCESS")
                from applications.agents.gem import GemAgent
                return GemAgent().fill_form(page, cv, personal_info, cover_letter, skills, experiences, add_log)
        except Exception:
            pass

        # Step 5: Fill standard Ashby fields in the resolved context
        candidate_name = personal_info.full_name if personal_info and personal_info.full_name else ""
        email_to_use = personal_info.email if personal_info and personal_info.email else ""
        phone_to_use = personal_info.phone if personal_info and personal_info.phone else ""

        # Extract CV text and LinkedIn for AI-powered filling
        cv_text = self.get_cv_text(cv)
        linkedin_url = getattr(personal_info, "linkedin_url", "") or ""
        if not linkedin_url and cv_text:
            linkedin_url = self.extract_linkedin(cv_text)

        first_name, last_name = "", ""
        if candidate_name and " " in candidate_name:
            first_name, last_name = candidate_name.split(" ", 1)
        else:
            first_name = candidate_name

        field_mappings = [
            (["input[name='name']", "input[placeholder*='name' i]", "input[id*='name' i]"], candidate_name, "Nom complet"),
            (["input[name='firstName']", "input[placeholder*='first' i]", "input[id*='first' i]"], first_name, "Prénom"),
            (["input[name='lastName']", "input[placeholder*='last' i]", "input[id*='last' i]"], last_name, "Nom"),
            (["input[type='email']", "input[name='email']", "input[placeholder*='email' i]"], email_to_use, "Email"),
            (["input[placeholder*='linkedin' i]", "input[name*='linkedin' i]", "input[type='url']"], linkedin_url, "LinkedIn"),
            (["input[type='tel']", "input[name='phone']", "input[placeholder*='phone' i]"], phone_to_use, "Téléphone"),
            (["textarea[name='coverLetter']", "textarea[placeholder*='cover' i]", "textarea[placeholder*='letter' i]", "textarea"], cover_letter, "Lettre de motivation"),
        ]

        for selectors, value, label in field_mappings:
            if not value:
                continue
            for sel in selectors:
                try:
                    el = form_ctx.query_selector(sel)
                    if el and el.is_visible():
                        el.click()
                        time.sleep(0.2)
                        el.fill(value)
                        fields_filled += 1
                        add_log("FILL_ASHBY", f"✅ Champ '{label}' rempli.", "SUCCESS")
                        break
                except Exception:
                    continue

        # Step 6: CV upload
        try:
            for sel in ["input[type='file'][name*='resume' i]", "input[type='file'][name*='cv' i]", "input[type='file']"]:
                el = form_ctx.query_selector(sel)
                if el and cv and cv.raw_file_url and not cv.raw_file_url.startswith("http"):
                    abs_cv_path = f"/app/{cv.raw_file_url}"
                    if os.path.exists(abs_cv_path):
                        el.set_input_files(abs_cv_path)
                        fields_filled += 1
                        add_log("FILL_ASHBY", f"✅ CV uploadé : {cv.filename}", "SUCCESS")
                        break
        except Exception as e:
            add_log("FILL_ASHBY", f"⚠️ Échec upload CV : {str(e)}", "WARNING")

        # Step 7: AI-powered custom field filling (textareas, radios, remaining inputs)
        if cv_text:
            add_log("FILL_ASHBY", "🤖 Phase IA : Analyse des questions personnalisées...", "INFO")

            # Fill empty textareas
            try:
                textareas = form_ctx.query_selector_all("textarea")
                for ta in textareas:
                    if not ta.is_visible():
                        continue
                    current_val = ta.input_value()
                    if current_val and len(current_val.strip()) > 5:
                        continue
                    placeholder = ta.get_attribute("placeholder") or ""
                    question = placeholder if placeholder else "Why are you a strong fit?"
                    answer = self.ask_llm(question, cv_text, cover_letter)
                    if answer:
                        ta.fill(answer, timeout=3000)
                        fields_filled += 1
                        add_log("FILL_ASHBY", f"✅ 🤖 Textarea rempli par IA.", "SUCCESS")
            except Exception as e:
                add_log("FILL_ASHBY", f"⚠️ Erreur IA textareas : {str(e)[:80]}", "WARNING")

            # Handle radio buttons
            try:
                radios = form_ctx.query_selector_all("input[type='radio']")
                if radios:
                    from applications.agents.gem import GemAgent
                    gem = GemAgent()
                    radio_groups = gem._find_radio_groups(form_ctx, add_log)
                    for q, opts in radio_groups.items():
                        chosen = self.ask_llm_choose_option(q, opts, cv_text)
                        gem._click_radio_option(form_ctx, q, chosen, add_log)
                        fields_filled += 1
            except Exception as e:
                add_log("FILL_ASHBY", f"⚠️ Erreur IA radios : {str(e)[:80]}", "WARNING")

        return fields_filled > 0

    def submit_form(self, page, add_log) -> bool:
        # If Gem widget is present, delegate submission to GemAgent
        try:
            has_gem = False
            for frame in page.frames:
                if frame.url and "gem.com" in frame.url:
                    has_gem = True
                    break
            if not has_gem:
                page_content = page.content().lower()
                if "gem.com" in page_content or "powered by gem" in page_content:
                    has_gem = True

            if has_gem:
                add_log("SUBMIT_ASHBY", "Formulaire Gem détecté lors de la soumission. Délégation au GemAgent...", "INFO")
                from applications.agents.gem import GemAgent
                return GemAgent().submit_form(page, add_log)
        except Exception as e:
            add_log("SUBMIT_ASHBY", f"Erreur lors de la vérification de délégation : {str(e)}", "WARNING")

        contexts = [page] + list(page.frames)
        for ctx in contexts:
            for sel in ["button[type='submit']", "button:has-text('Submit')", "button:has-text('Apply')", "input[type='submit']"]:
                try:
                    btn = ctx.query_selector(sel)
                    if btn:
                        try:
                            btn.scroll_into_view_if_needed()
                        except Exception:
                            pass

                        add_log("SUBMIT_ASHBY", f"Bouton soumission trouvé ({sel}). Clic...", "INFO")
                        btn.click(force=True, timeout=5000)
                        time.sleep(4)
                        return True
                except Exception:
                    pass
        return False
