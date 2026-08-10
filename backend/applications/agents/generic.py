import time
from typing import List, Any
from applications.agents.base import BasePlatformAgent

class GenericAgent(BasePlatformAgent):
    """
    Fallback agent that uses heuristics to identify and fill fields on any web page.
    """

    def detect(self, page, url: str) -> bool:
        # Fallback agent, always returns True if no other agent is selected
        return True

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
        add_log("FILL_GENERIC", "Détection heuristique des champs sur la page...")
        fields_filled = 0

        candidate_name = personal_info.full_name if personal_info and personal_info.full_name else "Candidat"
        email_to_use = personal_info.email if personal_info and personal_info.email else ""
        phone_to_use = personal_info.phone if personal_info and personal_info.phone else ""

        # Name field
        name_selectors = [
            "input[name*='name']", "input[placeholder*='name']", "input[placeholder*='nom']",
            "input[id*='name']", "input[type='text'][autocomplete*='name']"
        ]
        for sel in name_selectors:
            try:
                el = page.query_selector(sel)
                if el and el.is_visible():
                    el.fill(candidate_name)
                    fields_filled += 1
                    add_log("FILL_GENERIC", f"Champ Nom rempli avec : '{candidate_name}'")
                    break
            except Exception:
                pass

        # Email field
        email_selectors = [
            "input[type='email']", "input[name*='email']", "input[placeholder*='email']",
            "input[id*='email']"
        ]
        for sel in email_selectors:
            try:
                el = page.query_selector(sel)
                if el and el.is_visible():
                    el.fill(email_to_use)
                    fields_filled += 1
                    add_log("FILL_GENERIC", f"Champ Email rempli avec : '{email_to_use}'")
                    break
            except Exception:
                pass

        # Phone field
        phone_selectors = [
            "input[type='tel']", "input[name*='phone']", "input[placeholder*='phone']",
            "input[placeholder*='téléphone']", "input[id*='phone']"
        ]
        for sel in phone_selectors:
            try:
                el = page.query_selector(sel)
                if el and el.is_visible():
                    el.fill(phone_to_use)
                    fields_filled += 1
                    add_log("FILL_GENERIC", f"Champ Téléphone rempli avec : '{phone_to_use}'")
                    break
            except Exception:
                pass

        # Cover letter field
        cover_selectors = [
            "textarea", "textarea[name*='cover']", "textarea[name*='letter']",
            "textarea[name*='message']", "textarea[placeholder*='Cover']", "textarea[placeholder*='motivation']"
        ]
        for sel in cover_selectors:
            try:
                el = page.query_selector(sel)
                if el and el.is_visible():
                    el.fill(cover_letter)
                    fields_filled += 1
                    add_log("FILL_GENERIC", "Lettre de motivation injectée dans le champ texte.")
                    break
            except Exception:
                pass

        # CV File upload field
        try:
            file_selectors = [
                "input[type='file'][name*='resume']", "input[type='file'][name*='cv']",
                "input[type='file'][id*='resume']", "input[type='file'][id*='cv']",
                "input[type='file']"
            ]
            for sel in file_selectors:
                el = page.query_selector(sel)
                if el and el.is_visible():
                    cv_path = cv.raw_file_url
                    if cv_path and not cv_path.startswith("http") and "/" in cv_path:
                        abs_cv_path = f"/app/{cv_path}"
                        import os
                        if os.path.exists(abs_cv_path):
                            el.set_input_files(abs_cv_path)
                            fields_filled += 1
                            add_log("FILL_GENERIC", f"CV téléchargé via sélecteur ({sel}) : {cv.filename}", "SUCCESS")
                            break
        except Exception as e:
            add_log("FILL_GENERIC", f"Échec de l'upload du CV : {str(e)}", "WARNING")

        return fields_filled > 0

    def submit_form(self, page, add_log) -> bool:
        submit_selectors = [
            "button[type='submit']", "input[type='submit']", "button:has-text('Submit')",
            "button:has-text('Postuler')", "button:has-text('Send')", "input:has-text('Submit')"
        ]
        for sel in submit_selectors:
            try:
                btn = page.query_selector(sel)
                if btn and btn.is_visible():
                    add_log("SUBMIT_GENERIC", f"Bouton de soumission détecté ({sel}). Clic en cours...")
                    btn.click()
                    time.sleep(3)
                    return True
            except Exception:
                pass
        return False
