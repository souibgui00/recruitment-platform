import re
import time
import os
from typing import List, Any
from applications.agents.base import BasePlatformAgent


class LeverAgent(BasePlatformAgent):
    """
    Agent specialized in handling Lever job boards (jobs.lever.co).
    Uses AI (Groq LLM) to intelligently fill ALL form fields including:
    - Standard fields (name, email, phone, LinkedIn)
    - Custom text questions
    - Cover letter / Resume upload
    """

    def detect(self, page, url: str) -> bool:
        url_lower = url.lower()
        if "lever.co" in url_lower:
            return True
        try:
            if page.query_selector(".application-form"):
                return True
            for frame in page.frames:
                if "lever.co" in (frame.url or "").lower():
                    return True
        except Exception:
            pass
        return False

    def _get_form_context(self, page, add_log):
        """Find the correct context (iframe or main page) for the Lever form."""
        for frame in page.frames:
            if "lever.co" in (frame.url or "").lower():
                add_log("FILL_LEVER", f"Formulaire Lever trouvé dans l'iframe : {frame.url}", "SUCCESS")
                return frame
        if page.query_selector(".application-form"):
            add_log("FILL_LEVER", "Formulaire Lever inline détecté.", "SUCCESS")
            return page
        return page

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
        add_log("FILL_LEVER", "Début du remplissage intelligent du formulaire Lever...", "INFO")
        form_ctx = self._get_form_context(page, add_log)

        # ── Wait for form to fully render ──
        time.sleep(2)
        for attempt in range(8):
            try:
                test = form_ctx.query_selector("input:not([type='hidden']), textarea")
                if test:
                    break
            except Exception:
                pass
            time.sleep(1)

        # ── Extract candidate data ──
        full_name = personal_info.full_name if personal_info else "Candidat"
        email_to_use = personal_info.email if personal_info else ""
        phone_to_use = personal_info.phone if personal_info else ""
        linkedin_url = getattr(personal_info, "linkedin_url", "") or ""
        github_url = getattr(personal_info, "github_url", "") or ""

        cv_text = self.get_cv_text(cv)
        if not linkedin_url and cv_text:
            linkedin_url = self.extract_linkedin(cv_text)
        if not github_url and cv_text:
            github_url = self.extract_github(cv_text)

        fields_filled = 0

        # ══════════════════════════════════════════════════════════
        # PHASE 1: Scan all form fields via JavaScript
        # ══════════════════════════════════════════════════════════
        add_log("FILL_LEVER", "Phase 1: Scanning des champs du formulaire...", "INFO")

        try:
            scan_result = form_ctx.evaluate(r'''
            (() => {
                const results = [];
                const inputs = document.querySelectorAll(
                    'input:not([type="hidden"]):not([type="file"]):not([type="radio"]):not([type="checkbox"]), textarea, select'
                );
                inputs.forEach((el, idx) => {
                    let label = '';
                    if (el.id) {
                        const lbl = document.querySelector('label[for="' + el.id + '"]');
                        if (lbl) label = lbl.textContent.trim();
                    }
                    if (!label && el.name) {
                        const lbl = document.querySelector('label[for="' + el.name + '"]');
                        if (lbl) label = lbl.textContent.trim();
                    }
                    if (!label) {
                        const p = el.closest('label');
                        if (p) label = p.textContent.trim();
                    }
                    if (!label) {
                        const c = el.closest('.application-question') || el.closest('.field') || el.parentElement;
                        if (c) {
                            const l = c.querySelector('label, .label, span, p');
                            if (l && l !== el) label = l.textContent.trim();
                        }
                    }
                    if (!label) label = el.getAttribute('aria-label') || el.placeholder || el.name || '';

                    label = label.replace(/\s*\*\s*$/, '').replace(/\n/g, ' ').trim();

                    let options = [];
                    if (el.tagName.toLowerCase() === 'select') {
                        Array.from(el.options).forEach(opt => {
                            if (opt.value && opt.value !== '') {
                                options.push({ label: opt.textContent.trim(), value: opt.value });
                            }
                        });
                    }

                    results.push({
                        index: idx,
                        label: label,
                        value: el.value || '',
                        tag: el.tagName.toLowerCase(),
                        options: options
                    });
                });
                return results;
            })()
            ''')
        except Exception as e:
            add_log("FILL_LEVER", f"Erreur scan JS: {str(e)[:80]}", "WARNING")
            scan_result = []

        add_log("FILL_LEVER", f"Trouvé {len(scan_result)} champs.", "SUCCESS")
        for f in scan_result:
            add_log("FILL_LEVER", f"  → #{f['index']}: tag={f['tag']} label='{f.get('label','')[:40]}'", "INFO")

        input_elements = form_ctx.query_selector_all(
            "input:not([type='hidden']):not([type='file']):not([type='radio']):not([type='checkbox']), textarea, select"
        )

        # ══════════════════════════════════════════════════════════
        # PHASE 2: Map labels to values and fill
        # ══════════════════════════════════════════════════════════
        add_log("FILL_LEVER", "Phase 2: Remplissage des champs...", "INFO")

        for field_info in scan_result:
            idx = field_info['index']
            label = field_info['label']
            tag = field_info['tag']
            options = field_info.get('options', [])

            if idx >= len(input_elements):
                continue

            el = input_elements[idx]
            label_lower = label.lower()

            # Skip already filled
            try:
                current_val = el.evaluate("e => e.value") or ""
                if current_val.strip():
                    continue
            except Exception:
                pass

            # ── Handle SELECT dropdowns ──
            if tag == "select" and options:
                opt_labels = [o['label'] for o in options]
                chosen = self.ask_llm_choose_option(label or "Select an option", opt_labels, cv_text)
                target_val = None
                for o in options:
                    if chosen.lower() in o['label'].lower() or o['label'].lower() in chosen.lower():
                        target_val = o['value']
                        break
                if target_val:
                    try:
                        el.select_option(target_val)
                        fields_filled += 1
                        add_log("FILL_LEVER", f"Dropdown '{label[:30]}' → '{chosen}'", "SUCCESS")
                    except Exception as se:
                        add_log("FILL_LEVER", f"Erreur select: {str(se)[:50]}", "WARNING")
                continue

            # ── Handle TEXT inputs and TEXTAREAS ──
            value = None

            if 'name' == label_lower or 'full name' in label_lower or 'nom' in label_lower:
                value = full_name
            elif 'email' in label_lower:
                value = email_to_use
            elif 'phone' in label_lower or 'téléphone' in label_lower:
                value = phone_to_use
            elif 'linkedin' in label_lower:
                value = linkedin_url
            elif 'github' in label_lower or 'portfolio' in label_lower or 'website' in label_lower:
                value = github_url
            elif 'cover letter' in label_lower or 'lettre' in label_lower or 'comments' in label_lower:
                value = cover_letter
            elif label:
                value = self.ask_llm(label, cv_text, cover_letter)

            if not value or value.lower() in ("none", "n/a", ""):
                continue

            try:
                el.click(timeout=2000)
                time.sleep(0.15)
                el.fill(value, timeout=3000)
                fields_filled += 1
                add_log("FILL_LEVER", f"Texte '{label[:30]}' → '{str(value)[:30]}'", "SUCCESS")
            except Exception as fe:
                add_log("FILL_LEVER", f"Erreur saisie '{label}': {str(fe)[:50]}", "WARNING")

        # ══════════════════════════════════════════════════════════
        # PHASE 3: Upload Resume/CV file
        # ══════════════════════════════════════════════════════════
        add_log("FILL_LEVER", "Phase 3: Upload du CV...", "INFO")
        try:
            resume_input = form_ctx.query_selector(
                "input[type='file'][name='resume'], input[type='file'][name*='cv'], input[type='file']"
            )
            if resume_input:
                cv_path = cv.raw_file_url
                if cv_path and not cv_path.startswith("http") and "/" in cv_path:
                    abs_cv_path = f"/app/{cv_path}"
                    if os.path.exists(abs_cv_path):
                        resume_input.set_input_files(abs_cv_path)
                        fields_filled += 1
                        add_log("FILL_LEVER", f"CV téléchargé : {cv.filename}", "SUCCESS")
                    else:
                        add_log("FILL_LEVER", f"Fichier CV introuvable : {abs_cv_path}", "WARNING")
            else:
                add_log("FILL_LEVER", "Aucun champ de fichier CV trouvé.", "WARNING")
        except Exception as e:
            add_log("FILL_LEVER", f"Échec de l'upload du CV : {str(e)}", "WARNING")

        add_log("FILL_LEVER", f"Remplissage terminé : {fields_filled} champ(s) rempli(s).", "SUCCESS")
        return fields_filled > 0

    def submit_form(self, page, add_log) -> bool:
        try:
            form_ctx = self._get_form_context(page, add_log)
            submit_btn = form_ctx.query_selector(
                "button#postulate, button[type='submit'], input[type='submit'], "
                "button.postings-btn, a.postings-btn"
            )
            if submit_btn:
                submit_btn.click()
                add_log("SUBMIT_LEVER", "Bouton de soumission cliqué.", "SUCCESS")
                time.sleep(5)
                return True
            else:
                add_log("SUBMIT_LEVER", "Bouton de soumission non trouvé.", "WARNING")
        except Exception as e:
            add_log("SUBMIT_LEVER", f"Échec de la soumission : {str(e)}", "WARNING")
        return False
