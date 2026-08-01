"""Email alert system for new builders"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import List, Dict
from config import EMAIL_FROM, SMTP_SERVER, SMTP_PORT, GMAIL_APP_PASSWORD
from database import BuilderDatabase

class EmailAlert:
    def __init__(self):
        self.db = BuilderDatabase()
        self.email_from = EMAIL_FROM
        self.smtp_server = SMTP_SERVER
        self.smtp_port = SMTP_PORT
        self.gmail_app_password = GMAIL_APP_PASSWORD

    def send_alert(self, to_email: str, builders: List[Dict]) -> bool:
        """Send daily alert email with new builders"""
        if not builders:
            print("No new builders to alert")
            return False

        try:
            subject = f"🏗️ {len(builders)} New Builder(s) Found - Brevard County Permits"
            html_body = self._build_email_html(builders)
            self._send_gmail(to_email, subject, html_body)

            for builder in builders:
                self.db.log_alert_sent(
                    builder['id'],
                    builder['name'],
                    builder['permit_count'],
                    to_email
                )

            print(f"✅ Alert sent to {to_email} with {len(builders)} new builders")
            return True

        except Exception as e:
            print(f"❌ Failed to send email: {str(e)}")
            return False

    def _build_email_html(self, builders: List[Dict]) -> str:
        """Build HTML email body - Display: Builder Name, Address, Zipcode, Lot Size"""
        rows = []

        for builder in builders:
            permits = self.db.get_permits_for_builder(builder['id'])
            permit_details = []
            for p in permits[:1]:
                permit_details.append(f"""
                    <strong>Property Address:</strong> {p['property_address']}<br>
                    <strong>Zipcode:</strong> {p['zipcode']}<br>
                    <strong>Lot Size:</strong> {p['lot_size'] if p['lot_size'] else 'Not available'}<br>
                    <strong>Application Type:</strong> {p['application_type']}<br>
                    <strong>Date Filed:</strong> {p['date_issued']}
                """)
            permit_list = "".join(permit_details)

            rows.append(f"""
            <tr style="background-color: #f9f9f9; border-bottom: 1px solid #ddd;">
                <td colspan="4" style="padding: 15px; background-color: #ecf0f1;">
                    <strong style="font-size: 16px;">🏗️ {builder['name']}</strong>
                    <br><small>License ID: {builder['license_id']}</small>
                </td>
            </tr>
            <tr style="background-color: #ffffff;">
                <td colspan="4" style="padding: 12px; border-left: 4px solid #3498db;">
                    {permit_list}
                </td>
            </tr>
            """)

        html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; background-color: #f5f5f5; }}
                .container {{ max-width: 900px; margin: 0 auto; background-color: white; padding: 20px; border-radius: 8px; }}
                .header {{ background-color: #2c3e50; color: white; padding: 20px; border-radius: 5px; margin-bottom: 20px; }}
                .header h1 {{ margin: 0; font-size: 24px; }}
                .header p {{ margin: 5px 0 0 0; font-size: 14px; opacity: 0.9; }}
                table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
                th {{ background-color: #34495e; color: white; padding: 12px; text-align: left; }}
                .footer {{ background-color: #ecf0f1; padding: 15px; border-radius: 5px; margin-top: 20px; font-size: 12px; color: #7f8c8d; }}
                .action-btn {{ display: inline-block; background-color: #3498db; color: white; padding: 10px 15px; text-decoration: none; border-radius: 3px; margin-top: 15px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🏗️ New Builders Alert</h1>
                    <p>Brevard County Building Permits - IMPACT FEES RESIDENTIAL</p>
                    <p>Generated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}</p>
                </div>

                <p>Hi,</p>
                <p>
                    <strong>{len(builders)} new builder(s)</strong> have filed IMPACT FEES RESIDENTIAL permits in Palm Bay today.
                </p>

                <table>
                    <thead>
                        <tr>
                            <th>Builder Information</th>
                        </tr>
                    </thead>
                    <tbody>
                        {''.join(rows)}
                    </tbody>
                </table>

                <div style="background-color: #e8f4f8; padding: 15px; border-left: 4px solid #3498db; margin: 20px 0;">
                    <strong>📌 Next Steps:</strong>
                    <ul style="margin: 10px 0; padding-left: 20px;">
                        <li>Search the builder's name in your existing contacts</li>
                        <li>Research the builder's track record</li>
                        <li>Reach out with your land sourcing services</li>
                    </ul>
                </div>

                <div class="footer">
                    <p>
                        This is an automated alert from your Brevard Builder Discovery System.
                        Alerts are sent weekdays at 8:30 AM with IMPACT FEES RESIDENTIAL permits filed in Palm Bay.
                    </p>
                </div>
            </div>
        </body>
        </html>
        """
        return html

    def _send_gmail(self, to_email: str, subject: str, html_body: str):
        """Send email via Gmail SMTP"""
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = self.email_from
        msg['To'] = to_email

        msg.attach(MIMEText(html_body, 'html'))

        server = smtplib.SMTP(self.smtp_server, self.smtp_port)
        server.starttls()
        server.login(self.email_from, self.gmail_app_password)
        server.send_message(msg)
        server.quit()


def send_daily_alert():
    """Main function to send daily alert"""
    db = BuilderDatabase()
    alerts = EmailAlert()

    builders = db.get_new_builders_since(days=7)

    if builders:
        alerts.send_alert("admin@bjbacquisitiongroup.com", builders)
    else:
        print("No new builders found in the last 7 days")


if __name__ == "__main__":
    send_daily_alert()
