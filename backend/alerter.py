"""
Alerter: Send notifications via Resend API
Sends emails when:
- New funding detected
- Company starts hiring
"""

import os
import logging
from typing import Optional, List, Dict
from datetime import datetime
import requests
from sqlalchemy.orm import Session
from sqlalchemy import select
from models import Alert, Company

logger = logging.getLogger(__name__)

RESEND_API_KEY = os.getenv("RESEND_API_KEY", "")
RESEND_API_URL = "https://api.resend.com/emails"
FROM_EMAIL = os.getenv("FROM_EMAIL", "noreply@startup-radar.com")
TO_EMAILS = os.getenv("TO_EMAILS", "").split(",") if os.getenv("TO_EMAILS") else []


class Alerter:
    """Send email alerts via Resend API"""

    def __init__(self, api_key: str = RESEND_API_KEY, from_email: str = FROM_EMAIL):
        self.api_key = api_key
        self.from_email = from_email

    def send_email(self, to: str, subject: str, html: str, text: str = "") -> bool:
        """
        Send email via Resend API
        
        Args:
            to: Recipient email
            subject: Email subject
            html: HTML email body
            text: Plain text version
            
        Returns:
            True if sent successfully
        """
        if not self.api_key:
            logger.warning("⚠️  Resend API key not set, skipping email")
            return False

        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }

            payload = {
                "from": self.from_email,
                "to": to,
                "subject": subject,
                "html": html,
                "text": text or subject,
            }

            response = requests.post(
                RESEND_API_URL,
                json=payload,
                headers=headers,
                timeout=15,
            )

            if response.status_code == 200:
                logger.info(f"✅ Email sent to {to}")
                return True
            else:
                logger.error(f"❌ Resend API error: {response.status_code} - {response.text}")
                return False

        except Exception as e:
            logger.error(f"❌ Email sending error: {str(e)}")
            return False

    def format_funding_alert(self, company: Company) -> tuple[str, str]:
        """Format new funding alert email"""
        subject = f"🚀 {company.company_name} raised ${company.amount_usd/1e6:.1f}M"

        html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <h2>🚀 New Funding Announcement</h2>
            
            <p><strong>{company.company_name}</strong> has raised funding!</p>
            
            <table style="width: 100%; max-width: 600px; border-collapse: collapse; margin: 20px 0;">
                <tr style="background-color: #f5f5f5;">
                    <td style="padding: 10px;"><strong>Amount</strong></td>
                    <td style="padding: 10px;">${company.amount_usd/1e6:.1f}M USD</td>
                </tr>
                <tr>
                    <td style="padding: 10px;"><strong>Round</strong></td>
                    <td style="padding: 10px;">{company.round_type or 'Unknown'}</td>
                </tr>
                <tr style="background-color: #f5f5f5;">
                    <td style="padding: 10px;"><strong>Investors</strong></td>
                    <td style="padding: 10px;">{', '.join(company.investors) if company.investors else 'Not specified'}</td>
                </tr>
                <tr>
                    <td style="padding: 10px;"><strong>Country</strong></td>
                    <td style="padding: 10px;">{company.country or 'Unknown'}</td>
                </tr>
                <tr style="background-color: #f5f5f5;">
                    <td style="padding: 10px;"><strong>Announced</strong></td>
                    <td style="padding: 10px;">{company.announcement_date.strftime('%B %d, %Y') if company.announcement_date else 'Unknown'}</td>
                </tr>
            </table>
            
            {f'<p><a href="{company.source_url}" style="color: #0066cc;">Read article</a></p>' if company.source_url else ''}
            {f'<p><a href="{company.website_url}" style="color: #0066cc;">Visit website</a></p>' if company.website_url else ''}
            
            <hr style="margin: 30px 0; border: none; border-top: 1px solid #ccc;">
            <p style="font-size: 0.9em; color: #666;">Startup Radar - Automated Funding Discovery</p>
        </body>
        </html>
        """

        text = f"""
        New Funding: {company.company_name}
        Amount: ${company.amount_usd/1e6:.1f}M USD
        Round: {company.round_type}
        Investors: {', '.join(company.investors) if company.investors else 'Not specified'}
        Country: {company.country}
        Announced: {company.announcement_date}
        """

        return subject, html

    def format_hiring_alert(self, company: Company) -> tuple[str, str]:
        """Format hiring detection alert email"""
        subject = f"💼 {company.company_name} is hiring! ({company.open_roles_count or '?'} roles)"

        html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <h2>💼 Hiring Opportunity</h2>
            
            <p><strong>{company.company_name}</strong> is actively hiring!</p>
            
            <table style="width: 100%; max-width: 600px; border-collapse: collapse; margin: 20px 0;">
                <tr style="background-color: #f5f5f5;">
                    <td style="padding: 10px;"><strong>Company</strong></td>
                    <td style="padding: 10px;">{company.company_name}</td>
                </tr>
                <tr>
                    <td style="padding: 10px;"><strong>Open Roles</strong></td>
                    <td style="padding: 10px;">{company.open_roles_count or '?'}</td>
                </tr>
                <tr style="background-color: #f5f5f5;">
                    <td style="padding: 10px;"><strong>Tech Roles Found</strong></td>
                    <td style="padding: 10px;">{', '.join(company.job_titles) if company.job_titles else 'Engineering, Design, etc.'}</td>
                </tr>
                <tr>
                    <td style="padding: 10px;"><strong>Funding</strong></td>
                    <td style="padding: 10px;">${company.amount_usd/1e6:.1f}M {company.round_type}</td>
                </tr>
            </table>
            
            {f'<p><a href="{company.website_url}/careers" style="background-color: #0066cc; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; display: inline-block;">View Jobs</a></p>' if company.website_url else ''}
            {f'<p><a href="{company.linkedin_url}" style="color: #0066cc;">View on LinkedIn</a></p>' if company.linkedin_url else ''}
            
            <hr style="margin: 30px 0; border: none; border-top: 1px solid #ccc;">
            <p style="font-size: 0.9em; color: #666;">Startup Radar - Automated Hiring Detection</p>
        </body>
        </html>
        """

        text = f"""
        Hiring Alert: {company.company_name}
        Open Roles: {company.open_roles_count or '?'}
        Tech Roles: {', '.join(company.job_titles) if company.job_titles else 'Engineering, Design, etc.'}
        Funding: ${company.amount_usd/1e6:.1f}M {company.round_type}
        """

        return subject, html

    def send_new_funding_alert(self, company: Company, recipients: List[str] = None) -> bool:
        """Send alert for new funding"""
        recipients = recipients or TO_EMAILS
        if not recipients:
            logger.warning("⚠️  No recipients configured for alerts")
            return False

        subject, html = self.format_funding_alert(company)
        
        success = True
        for recipient in recipients:
            if not self.send_email(recipient.strip(), subject, html):
                success = False

        return success

    def send_hiring_alert(self, company: Company, recipients: List[str] = None) -> bool:
        """Send alert for hiring detection"""
        recipients = recipients or TO_EMAILS
        if not recipients:
            logger.warning("⚠️  No recipients configured for alerts")
            return False

        subject, html = self.format_hiring_alert(company)
        
        success = True
        for recipient in recipients:
            if not self.send_email(recipient.strip(), subject, html):
                success = False

        return success

    def process_alerts(self, db: Session) -> Dict[str, int]:
        """
        Send pending alerts
        
        Returns:
            Stats: {sent: N, failed: N}
        """
        stats = {"sent": 0, "failed": 0}

        try:
            # Get pending alerts
            stmt = select(Alert).where(Alert.sent == False)
            alerts = db.execute(stmt).scalars().all()

            for alert in alerts:
                # Get company details
                company_stmt = select(Company).where(Company.id == alert.company_id)
                company = db.execute(company_stmt).scalar_one_or_none()

                if not company:
                    continue

                # Send alert
                if self.send_email(
                    to=alert.recipient_email or TO_EMAILS[0],
                    subject=alert.message.split("\n")[0],
                    html=alert.message,
                ):
                    alert.sent = True
                    alert.sent_at = datetime.utcnow()
                    alert.status = "sent"
                    stats["sent"] += 1
                else:
                    alert.status = "failed"
                    stats["failed"] += 1

                db.commit()

            logger.info(f"📧 Alerts processed: {stats}")
            return stats

        except Exception as e:
            logger.error(f"Alert processing error: {str(e)}")
            return stats


from typing import Dict

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    alerter = Alerter()
    
    # Test email formatting (no actual send)
    from datetime import datetime
    
    test_company = Company(
        id=1,
        company_name="TestCorp",
        amount_usd=5000000,
        round_type="Series A",
        investors=["Sequoia", "Y Combinator"],
        country="USA",
        announcement_date=datetime.now(),
        website_url="https://testcorp.com",
    )
    
    subject, html = alerter.format_funding_alert(test_company)
    print(f"Subject: {subject}")
    print(f"HTML length: {len(html)}")
