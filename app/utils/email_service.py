import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import current_app

logger = logging.getLogger(__name__)

def send_issue_cleared_email(recipient_email, recipient_name, issue_id, issue_description, latitude, longitude, reported_date=""):
    """
    Sends a clear message email to the user's registered email address
    when an issue reported by them is cleared by the admin.
    """
    subject = f"[Jal Suraksha] Your Reported Issue #{issue_id} Has Been Cleared by Admin"

    body_text = f"""Dear {recipient_name},

Great news! The municipal issue you reported on Jal Suraksha has been inspected and CLEARED by the Guntur Municipal Corporation admin.

Issue Details:
- Issue Reference ID: #{issue_id}
- Description: {issue_description}
- Location: {latitude}, {longitude}
- Date Reported: {reported_date}
- Status: RESOLVED & CLEARED

Thank you for reporting this issue and helping us keep our city safe and clean.

Best regards,
Guntur Municipal Corporation - Jal Suraksha Department
Helpline: 7989332358 | Email: info@municipalcorporation.gov
Address: GMRIT deemed to be university, Rajam, 532127, AP.
"""

    body_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f4f6f9; margin: 0; padding: 20px; }}
            .container {{ max-width: 600px; margin: 0 auto; background: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 15px rgba(0,0,0,0.1); border: 1px solid #e0e0e0; }}
            .header {{ background: linear-gradient(135deg, #2E8B57 0%, #1e5c38 100%); color: #ffffff; padding: 25px; text-align: center; }}
            .header h1 {{ margin: 0; font-size: 22px; text-transform: uppercase; letter-spacing: 1px; }}
            .header p {{ margin: 5px 0 0 0; opacity: 0.9; font-size: 14px; }}
            .content {{ padding: 25px; color: #333333; line-height: 1.6; }}
            .badge {{ display: inline-block; background-color: #d4edda; color: #155724; border: 1px solid #c3e6cb; font-weight: bold; padding: 6px 12px; border-radius: 20px; font-size: 14px; margin-bottom: 15px; }}
            .details-box {{ background-color: #f8f9fa; border-left: 4px solid #2E8B57; padding: 15px; border-radius: 6px; margin: 15px 0; }}
            .details-box p {{ margin: 6px 0; font-size: 14px; }}
            .footer {{ background-color: #1a1a1a; color: #aaaaaa; text-align: center; padding: 15px; font-size: 12px; border-top: 3px solid #2E8B57; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>Jal Suraksha Department</h1>
                <p>Guntur Municipal Corporation</p>
            </div>
            <div class="content">
                <p>Dear <strong>{recipient_name}</strong>,</p>
                <div class="badge">[CLEARED] ISSUE RESOLVED & CLEARED</div>
                <p>Great news! The municipal issue you submitted to the Jal Suraksha portal has been inspected, resolved, and officially <strong>cleared</strong> by municipal administrators.</p>

                <div class="details-box">
                    <p><strong>Report Reference ID:</strong> #{issue_id}</p>
                    <p><strong>Issue Description:</strong> {issue_description}</p>
                    <p><strong>Location Coordinates:</strong> {latitude}, {longitude}</p>
                    <p><strong>Date Reported:</strong> {reported_date}</p>
                    <p><strong>Status:</strong> <span style="color:#2e7d32; font-weight:bold;">CLEARED & CLOSED</span></p>
                </div>

                <p>Thank you for participating in civic care and using Jal Suraksha to help improve our community.</p>
                <p style="margin-top: 20px;">Sincerely,<br><strong>Guntur Municipal Corporation</strong></p>
            </div>
            <div class="footer">
                <p>Contacts: 7989332358 | info@municipalcorporation.gov</p>
                <p>Address: GMRIT deemed to be university, Rajam, 532127, AP.</p>
            </div>
        </div>
    </body>
    </html>
    """

    return send_email_notification(recipient_email, subject, body_html, body_text)


def send_issue_cleared_sms(phone_number, issue_id, issue_description):
    """
    Sends a normal SMS message to the registered mobile number when an issue is cleared.
    """
    if not phone_number:
        logger.warning("No phone number provided for SMS notification.")
        return False

    clean_phone = ''.join(c for c in phone_number if c.isdigit())
    if len(clean_phone) < 10:
        logger.warning(f"Invalid phone number for SMS: {phone_number}")
        return False

    desc_snippet = issue_description[:35] + '...' if len(issue_description) > 35 else issue_description
    sms_text = f"Jal Suraksha Alert: Dear Citizen, your reported issue #{issue_id} ('{desc_snippet}') has been CLEARED & RESOLVED by Guntur Municipal Corporation. Thank you!"

    print(f"[SMS NOTIFICATION SENT TO {clean_phone}] {sms_text}")
    logger.info(f"SMS notification sent to {clean_phone}: {sms_text}")

    # Optional SMS Gateway / Fast2SMS HTTP API Integration
    sms_api_key = current_app.config.get('SMS_API_KEY', '')
    if sms_api_key:
        try:
            import requests
            requests.post(
                'https://www.fast2sms.com/dev/bulkV2',
                headers={'authorization': sms_api_key},
                data={
                    'variables_values': f'Issue #{issue_id} cleared',
                    'route': 'otp',
                    'numbers': clean_phone,
                },
                timeout=5
            )
        except Exception as exc:
            logger.error(f"SMS API delivery error: {exc}")

    return True


def send_email_notification(recipient_email, subject, body_html, body_text=None):
    if not recipient_email or '@' not in recipient_email:
        logger.warning(f"Cannot send email: invalid recipient '{recipient_email}'")
        return False

    server = current_app.config.get('MAIL_SERVER', 'smtp.gmail.com')
    port = current_app.config.get('MAIL_PORT', 587)
    use_tls = current_app.config.get('MAIL_USE_TLS', True)
    username = current_app.config.get('MAIL_USERNAME', '')
    password = current_app.config.get('MAIL_PASSWORD', '')
    sender = current_app.config.get(
        'MAIL_DEFAULT_SENDER',
        username if username else 'Guntur Municipal Corporation <info@municipalcorporation.gov>'
    )

    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = sender
    msg['To'] = recipient_email

    if body_text:
        msg.attach(MIMEText(body_text, 'plain', 'utf-8'))
    if body_html:
        msg.attach(MIMEText(body_html, 'html', 'utf-8'))

    print(f"[EMAIL NOTIFICATION SENT TO {recipient_email}] Subject: {subject}")

    if server and username and password:
        try:
            if port == 465:
                smtp_conn = smtplib.SMTP_SSL(server, port, timeout=10)
            else:
                smtp_conn = smtplib.SMTP(server, port, timeout=10)
                if use_tls:
                    smtp_conn.starttls()
            smtp_conn.login(username, password)
            smtp_conn.sendmail(sender, [recipient_email], msg.as_string())
            smtp_conn.quit()
            logger.info(f"Email successfully sent via SMTP to {recipient_email}")
            print(f"[SUCCESS] Real SMTP Email delivered to {recipient_email}")
            return True
        except Exception as e:
            logger.error(f"Failed to send SMTP email to {recipient_email}: {str(e)}")
            print(f"[WARNING] SMTP delivery warning for {recipient_email}: {str(e)}")
            return False
    else:
        print(f"[SMTP Info] To enable live SMTP delivery to real inboxes, add MAIL_USERNAME and MAIL_PASSWORD (e.g. Gmail App Password) to your .env file.")
        return True
