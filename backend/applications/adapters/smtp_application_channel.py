import os
import smtplib
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any, Optional, List
from applications.ports.application_channel import IApplicationChannel


class SmtpApplicationChannel(IApplicationChannel):
    """
    Adapter implementing application submission via email using a real SMTP server.
    Reads host, port, username, password and sender from environment variables.
    Generates a rich, professional application email including:
    - Candidate profile (name, contact, skills, experiences)
    - AI matching analysis (score, strengths, gaps, summary)
    - Cover letter generated from the LLM summary
    """

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
        smtp_host = os.environ.get("SMTP_HOST")
        smtp_port = os.environ.get("SMTP_PORT")
        smtp_user = os.environ.get("SMTP_USERNAME")
        smtp_pass = os.environ.get("SMTP_PASSWORD")
        smtp_from = os.environ.get("SMTP_FROM_EMAIL")

        if not all([smtp_host, smtp_port, smtp_user, smtp_pass, smtp_from]):
            missing = [k for k, v in {
                "SMTP_HOST": smtp_host,
                "SMTP_PORT": smtp_port,
                "SMTP_USERNAME": smtp_user,
                "SMTP_PASSWORD": smtp_pass,
                "SMTP_FROM_EMAIL": smtp_from
            }.items() if not v]
            return {
                "success": False,
                "error_message": f"SMTP configuration is incomplete. Missing variables: {', '.join(missing)}"
            }

        try:
            recipient = candidate_email or smtp_from

            # ── Build candidate profile section ──────────────────────────────────
            candidate_name = "Candidat"
            candidate_phone = "Non renseigné"
            candidate_location = "Non renseignée"
            if personal_info:
                candidate_name = personal_info.full_name or candidate_name
                candidate_phone = personal_info.phone or candidate_phone
                candidate_location = personal_info.location or candidate_location

            # ── Build experiences section ────────────────────────────────────────
            exp_lines = ""
            if experiences:
                for exp in experiences[:5]:  # cap at 5 most recent
                    period = str(exp.start_date.year) if exp.start_date else "?"
                    period += " – " + (str(exp.end_date.year) if exp.end_date else "Présent")
                    exp_lines += f"  • {exp.title} @ {exp.company} ({period})\n"
                    if exp.description:
                        short_desc = exp.description[:180].rstrip()
                        exp_lines += f"    {short_desc}{'...' if len(exp.description) > 180 else ''}\n"
            if not exp_lines:
                exp_lines = "  Aucune expérience disponible dans le CV parsé.\n"

            # ── Build skills section ─────────────────────────────────────────────
            skills_line = ", ".join(skills[:20]) if skills else "Non spécifiées"

            # ── Build AI analysis section ────────────────────────────────────────
            score_line = f"{round(match.compatibility_score, 1)}%" if match else "N/A"
            semantic_line = f"{round(match.semantic_similarity * 100, 1)}%" if match else "N/A"
            llm_line = f"{round(match.llm_score, 1)}%" if match else "N/A"

            strengths_lines = ""
            if match and match.matching_points:
                for pt in match.matching_points:
                    strengths_lines += f"  ✓ {pt}\n"
            else:
                strengths_lines = "  Aucun point identifié.\n"

            gaps_lines = ""
            if match and match.gap_points:
                for pt in match.gap_points:
                    gaps_lines += f"  △ {pt}\n"
            else:
                gaps_lines = "  Aucune lacune identifiée.\n"

            ai_summary = (match.summary or "Aucune synthèse disponible.") if match else "Aucune synthèse disponible."

            # ── Cover letter from AI summary ─────────────────────────────────────
            cover_letter = f"""Madame, Monsieur,

Je me permets de vous adresser ma candidature pour le poste de {job_offer.title} au sein de votre entreprise {job_offer.company}.

Fort(e) de mon expérience dans les domaines couverts par ce poste, je suis convaincu(e) que mon profil correspond aux exigences de ce rôle. {ai_summary}

Je reste disponible pour tout entretien ou complément d'information.

Cordialement,
{candidate_name}
{candidate_phone} | {recipient}"""

            # ── Assemble final email body ────────────────────────────────────────
            body = f"""════════════════════════════════════════════════════
        CANDIDATURE AUTOMATIQUE — Recrute.IA
════════════════════════════════════════════════════

📌 OFFRE CIBLÉE
─────────────────
Poste       : {job_offer.title}
Entreprise  : {job_offer.company}
Lieu        : {job_offer.location or 'Non précisé'}
Lien        : {job_offer.source_url or 'Non spécifié'}

────────────────────────────────────────────────────
👤 PROFIL DU CANDIDAT
────────────────────────────────────────────────────
Nom complet   : {candidate_name}
Email         : {recipient}
Téléphone     : {candidate_phone}
Localisation  : {candidate_location}
CV            : {cv.filename or 'Non spécifié'}

────────────────────────────────────────────────────
🛠️  COMPÉTENCES CLÉS
────────────────────────────────────────────────────
{skills_line}

────────────────────────────────────────────────────
💼 EXPÉRIENCES PROFESSIONNELLES
────────────────────────────────────────────────────
{exp_lines}
────────────────────────────────────────────────────
🤖 ANALYSE DE COMPATIBILITÉ IA
────────────────────────────────────────────────────
Score Global          : {score_line}
  ↳ Similarité Vector : {semantic_line}
  ↳ Évaluation LLM    : {llm_line}

Points Forts identifiés par l'IA :
{strengths_lines}
Lacunes ou points d'attention :
{gaps_lines}
Synthèse IA :
  {ai_summary}

────────────────────────────────────────────────────
✉️  LETTRE DE MOTIVATION GÉNÉRÉE
────────────────────────────────────────────────────

{cover_letter}

════════════════════════════════════════════════════
ID Candidature : {application.id}
Date d'envoi   : {datetime.utcnow().strftime('%d/%m/%Y à %H:%M')} UTC
Moteur         : intfloat/multilingual-e5-large + Groq / Llama-3
════════════════════════════════════════════════════
"""

            msg = MIMEMultipart()
            msg["From"] = smtp_from
            msg["To"] = recipient
            msg["Subject"] = f"[Candidature IA] {job_offer.title} — {job_offer.company} ({score_line} compatibilité)"
            msg.attach(MIMEText(body, "plain", "utf-8"))

            port = int(smtp_port)
            server = smtplib.SMTP(smtp_host, port)
            server.ehlo()
            if port == 587:
                server.starttls()
                server.ehlo()
            server.login(smtp_user, smtp_pass)
            server.sendmail(smtp_from, recipient, msg.as_string())
            server.close()

            return {"success": True, "error_message": None}

        except Exception as e:
            return {"success": False, "error_message": str(e)}
