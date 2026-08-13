import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional

class EmailService:
    def __init__(self):
        self.smtp_host = os.environ.get("SMTP_HOST", "smtp.gmail.com")
        self.smtp_port = int(os.environ.get("SMTP_PORT", "587"))
        self.smtp_username = os.environ.get("SMTP_USERNAME")
        self.smtp_password = os.environ.get("SMTP_PASSWORD")
        self.from_email = os.environ.get("SMTP_FROM_EMAIL", self.smtp_username)
        self.frontend_url = os.environ.get("FRONTEND_URL", "http://localhost:3000")

    def send_email(self, to_email: str, subject: str, html_content: str) -> bool:
        """Send email using SMTP"""
        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.from_email
            msg['To'] = to_email

            msg.attach(MIMEText(html_content, 'html'))

            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)
            
            return True
        except Exception as e:
            print(f"Failed to send email: {e}")
            return False

    def send_verification_email(self, to_email: str, verification_token: str) -> bool:
        """Send email verification email"""
        verification_url = f"{self.frontend_url}/auth/verify-email?token={verification_token}"
        
        html_content = f"""
        <html>
        <body>
            <h2>Vérifiez votre adresse email</h2>
            <p>Merci de vous être inscrit sur notre plateforme de recrutement IA.</p>
            <p>Veuillez cliquer sur le lien ci-dessous pour vérifier votre adresse email:</p>
            <p><a href="{verification_url}">Vérifier mon email</a></p>
            <p>Si vous n'avez pas créé de compte, vous pouvez ignorer cet email.</p>
            <p>Ce lien expirera dans 24 heures.</p>
        </body>
        </html>
        """
        
        return self.send_email(to_email, "Vérifiez votre adresse email", html_content)

    def send_password_reset_email(self, to_email: str, reset_token: str) -> bool:
        """Send password reset email"""
        reset_url = f"{self.frontend_url}/auth/reset-password?token={reset_token}"
        
        html_content = f"""
        <html>
        <body>
            <h2>Réinitialisation de mot de passe</h2>
            <p>Vous avez demandé une réinitialisation de votre mot de passe.</p>
            <p>Cliquez sur le lien ci-dessous pour réinitialiser votre mot de passe:</p>
            <p><a href="{reset_url}">Réinitialiser mon mot de passe</a></p>
            <p>Si vous n'avez pas demandé cette réinitialisation, vous pouvez ignorer cet email.</p>
            <p>Ce lien expirera dans 1 heure.</p>
        </body>
        </html>
        """
        
        return self.send_email(to_email, "Réinitialisation de mot de passe", html_content)

    def send_email_change_verification(self, new_email: str, verification_token: str, old_email: str) -> bool:
        """Send email change verification to new email address"""
        verification_url = f"{self.frontend_url}/auth/confirm-email-change?token={verification_token}"
        
        html_content = f"""
        <html>
        <body>
            <h2>Confirmation de changement d'email</h2>
            <p>Vous avez demandé de changer votre adresse email de {old_email} à {new_email}.</p>
            <p>Veuillez cliquer sur le lien ci-dessous pour confirmer ce changement:</p>
            <p><a href="{verification_url}">Confirmer le changement d'email</a></p>
            <p>Si vous n'avez pas demandé ce changement, vous pouvez ignorer cet email.</p>
            <p>Ce lien expirera dans 24 heures.</p>
        </body>
        </html>
        """
        
        return self.send_email(new_email, "Confirmation de changement d'email", html_content)

# Singleton instance
email_service = EmailService()