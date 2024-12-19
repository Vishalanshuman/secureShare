import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import os

def get_email_body(new_user,verification_url):
    email_body = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Email Verification</title>
    </head>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
        <div style="max-width: 600px; margin: auto; border: 1px solid #ddd; padding: 20px; border-radius: 8px;">
            <h1 style="color: #4CAF50;">Hi {new_user.email.split('@')[0]},</h1>
            <p>Thank you for signing up! Please verify your email by clicking the link below:</p>
            <p>
                <a href="{verification_url}" 
                style="display: inline-block; background-color: #4CAF50; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">
                Verify Email
                </a>
            </p>
            <p style="margin-top: 20px;">This link will expire in 24 hours.</p>
            <p>Best regards,<br>File Sharing Team</p>
        </div>
    </body>
    </html>
    """
    return email_body

def send_email(new_user,email_body):
    try:
        subject = "Email Verification - File Sharing System"  
        message = MIMEMultipart('alternative', None, [MIMEText(email_body, 'html')])
        message['Subject'] = subject
        message['From'] = os.getenv('MAIL_USERNAME')
        message['To'] = new_user.email

        server = smtplib.SMTP('smtp.gmail.com', 587)  
        server.ehlo()
        server.starttls()
        server.login(os.getenv('MAIL_USERNAME'), os.getenv('MAIL_PASSWORD'))
        server.sendmail(os.getenv('MAIL_USERNAME'), new_user.email, message.as_string())
        server.quit()
        return f"Email sent: {subject}"
    except Exception as e:
        return f'Error in sending mail: {e}'
