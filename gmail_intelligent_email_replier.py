import imaplib
import smtplib
import email
from email.header import decode_header
from email.mime.text import MIMEText
import re
import time

# -------- User configuration --------
IMAP_SERVER = "imap.gmail.com"
SMTP_SERVER = "smtp.gmail.com"
IMAP_PORT = 993
SMTP_PORT = 587

# IMPORTANT: For security, do NOT hardcode your real credentials in production.
# Use environment variables or secure vaults.
# For Gmail with 2FA, generate an App Password: https://support.google.com/accounts/answer/185833
EMAIL_ACCOUNT = "sharmademoa@gmail.com"   # <--- Replace with your Gmail address
EMAIL_PASSWORD = "ocyp menl xhrc qcgd"     # <--- Replace with your Gmail app password or normal password if no 2FA

# ------------------------------------

def clean_text(text):
    # Clean text for safe printing
    return ''.join(c if c.isprintable() else ' ' for c in text)

def analyze_email(email_text):
    """
    Analyze the email text and determine the intent or key points.
    This example uses simple keyword matching for demonstration.
    """
    email_text_lower = email_text.lower()

    greetings = ['hello', 'hi', 'greetings', 'dear', 'good morning', 'good evening', 'good afternoon']
    inquiry_words = ['question', 'inquiry', 'need help', 'can you', 'could you', 'would you', 'help me', 'information', 'details', 'support']
    thanks_words = ['thank you', 'thanks', 'appreciate', 'gratitude']
    meeting_words = ['schedule', 'meeting', 'appointment', 'call', 'discuss', 'talk']
    complaint_words = ['issue', 'problem', 'not working', 'error', 'fail', 'delay', 'complain', 'trouble']

    if any(greet in email_text_lower for greet in greetings):
        return 'greeting'
    if any(tk in email_text_lower for tk in thanks_words):
        return 'thanks'
    if any(iw in email_text_lower for iw in inquiry_words):
        return 'inquiry'
    if any(mw in email_text_lower for mw in meeting_words):
        return 'meeting'
    if any(cw in email_text_lower for cw in complaint_words):
        return 'complaint'
    return 'general'

def generate_reply(intent):
    """
    Generate an intelligent reply based on the detected intent.
    """
    if intent == 'greeting':
        return "Hello! Thank you for reaching out. How may I assist you today?"
    elif intent == 'thanks':
        return "You're welcome! Let me know if you need any further assistance."
    elif intent == 'inquiry':
        return "Thank you for your inquiry. I will get back to you with the required information shortly."
    elif intent == 'meeting':
        return "I appreciate your interest in scheduling a meeting. Please let me know your available dates and times."
    elif intent == 'complaint':
        return "I'm sorry to hear about the issue. Could you please provide more details so I can assist you better?"
    else:
        return "Thank you for your message. I will review it and get back to you soon."

def login_imap():
    mail = imaplib.IMAP4_SSL(IMAP_SERVER)
    mail.login(EMAIL_ACCOUNT, EMAIL_PASSWORD)
    return mail

def login_smtp():
    smtp = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
    smtp.starttls()
    smtp.login(EMAIL_ACCOUNT, EMAIL_PASSWORD)
    return smtp

def fetch_unread_emails(mail):
    mail.select("inbox")
    status, messages = mail.search(None, '(UNSEEN)')
    if status != 'OK':
        print("Failed to retrieve emails.")
        return []
    email_ids = messages[0].split()
    return email_ids

def get_email_message(mail, email_id):
    status, msg_data = mail.fetch(email_id, '(RFC822)')
    if status != 'OK':
        print("Failed to fetch message", email_id)
        return None
    msg = email.message_from_bytes(msg_data[0][1])
    return msg

def get_email_text(msg):
    # Extract plain text from email
    if msg.is_multipart():
        parts = msg.get_payload()
        for part in parts:
            content_type = part.get_content_type()
            if content_type == "text/plain":
                return part.get_payload(decode=True).decode(errors='ignore')
    else:
        return msg.get_payload(decode=True).decode(errors='ignore')
    return ""

def decode_mime_words(s):
    # Helper to decode MIME-encoded words in headers
    decoded_words = []
    for word, charset in decode_header(s):
        if charset:
            try:
                decoded_words.append(word.decode(charset))
            except:
                decoded_words.append(word if isinstance(word, str) else word.decode('utf-8', errors='ignore'))
        else:
            decoded_words.append(word if isinstance(word, str) else word.decode('utf-8', errors='ignore'))
    return ''.join(decoded_words)

def send_reply(smtp, to_address, subject, body):
    reply_subject = "Re: " + subject
    msg = MIMEText(body)
    msg['From'] = EMAIL_ACCOUNT
    msg['To'] = to_address
    msg['Subject'] = reply_subject

    smtp.sendmail(EMAIL_ACCOUNT, to_address, msg.as_string())
    print(f"Sent reply to {to_address}")

def main():
    print("Connecting to IMAP server...")
    mail = login_imap()
    print("Connecting to SMTP server...")
    smtp = login_smtp()
    print("Fetching unread emails...")

    unread_email_ids = fetch_unread_emails(mail)
    print(f"Found {len(unread_email_ids)} unread emails.")

    for email_id in unread_email_ids:
        msg = get_email_message(mail, email_id)
        if not msg:
            continue
        
        raw_subject = msg.get("Subject", "")
        subject = decode_mime_words(raw_subject)
        raw_from = msg.get("From", "")
        from_addr = email.utils.parseaddr(raw_from)[1]

        print(f"\nEmail from: {from_addr}")
        print(f"Subject: {subject}")

        email_text = get_email_text(msg)
        # Clean email text to avoid encoding issues in analysis
        clean_email_text = clean_text(email_text)

        # Analyze and generate reply
        intent = analyze_email(clean_email_text)
        reply = generate_reply(intent)

        print("Reply to send:", reply)

        # Send reply
        send_reply(smtp, from_addr, subject, reply)

        # Mark email as seen
        mail.store(email_id, '+FLAGS', '\\Seen')

    mail.logout()
    smtp.quit()
    print("Done processing emails.")

if __name__ == "__main__":
    print("Gmail Intelligent Email Reply Bot")
    print("Important:")
    print("- Make sure IMAP is enabled in your Gmail settings.")
    print("- Use an App Password if you have 2FA enabled on your Google account.")
    print("- This script checks unread emails and replies once.")
    print("- Run this script periodically or automate as per your need.\n")

    try:
        main()
    except Exception as e:
        print("An error occurred:", str(e))
