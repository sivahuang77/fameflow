
import imaplib
import email
import configparser
import time
import logging
import smtplib
from email.header import decode_header
from email.mime.text import MIMEText

# Import the core logic module
import core_logic

# --- Logging Setup ---
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

CONFIG_FILE = 'email_config.ini'

def read_config():
    """Reads configuration from email_config.ini."""
    config = configparser.ConfigParser()
    if not config.read(CONFIG_FILE):
        logger.error(f"Configuration file '{CONFIG_FILE}' not found or is empty.")
        return None
    try:
        return config['EMAIL']
    except KeyError:
        logger.error(f"Section [EMAIL] not found in '{CONFIG_FILE}'.")
        return None

def send_email_reply(config, recipient_email, subject, body):
    """Sends an email reply using SMTP settings from config."""
    try:
        smtp_server = config['SMTP_SERVER']
        smtp_port = int(config['SMTP_PORT'])
        email_address = config['EMAIL_ADDRESS']
        app_password = config['APP_PASSWORD']
        use_tls = config.getboolean('SMTP_USE_TLS')

        msg = MIMEText(body, 'plain', 'utf-8')
        msg['From'] = email_address
        msg['To'] = recipient_email
        msg['Subject'] = f"Re: {subject}" # Add "Re:" to the subject

        with smtplib.SMTP(smtp_server, smtp_port) as server:
            if use_tls:
                server.starttls()
            server.login(email_address, app_password)
            server.send_message(msg)
        logger.info(f"Successfully sent email reply to {recipient_email}")
    except Exception as e:
        logger.error(f"Failed to send email reply to {recipient_email}: {e}")

def process_emails(config):
    """Connects to the email server and processes unread emails."""
    try:
        # Connect to the server
        mail = imaplib.IMAP4_SSL(config['IMAP_SERVER'])
        # Login
        mail.login(config['EMAIL_ADDRESS'], config['APP_PASSWORD'])
        # Select the inbox
        mail.select('inbox')
        logger.info("Successfully connected to the inbox.")

        # Search for all unread emails
        status, messages = mail.search(None, 'UNSEEN')
        if status != 'OK':
            logger.error("Failed to search for emails.")
            mail.logout()
            return

        message_ids = messages[0].split()
        if not message_ids:
            logger.info("No new unread emails.")
            mail.logout()
            return
            
        logger.info(f"Found {len(message_ids)} new emails.")

        for msg_id in message_ids:
            # Fetch the email by ID
            status, msg_data = mail.fetch(msg_id, '(RFC822)')
            if status == 'OK':
                for response_part in msg_data:
                    if isinstance(response_part, tuple):
                        msg = email.message_from_bytes(response_part[1])
                        
                        # Decode sender and subject
                        sender, encoding = decode_header(msg.get("From"))[0]
                        if isinstance(sender, bytes):
                            sender = sender.decode(encoding or 'utf-8')
                        
                        # Extract the email address from sender string
                        sender_email = email.utils.parseaddr(sender)[1]

                        # Get email body
                        body = ""
                        if msg.is_multipart():
                            for part in msg.walk():
                                content_type = part.get_content_type()
                                if content_type == "text/plain":
                                    body = part.get_payload(decode=True).decode()
                                    break
                        else:
                            body = msg.get_payload(decode=True).decode()

                        if body:
                            logger.info(f"Processing email from: {sender_email}")

                            # Decode subject
                            subject, encoding = decode_header(msg.get("Subject"))[0]
                            if isinstance(subject, bytes):
                                subject = subject.decode(encoding or 'utf-8')

                            # Delegate to core logic
                            ai_response = core_logic.process_message(
                                user_identifier=sender_email,
                                message_text=body.strip(),
                                platform='email'
                            )

                            if ai_response:
                                # Send automatic reply
                                send_email_reply(config, sender_email, subject, ai_response)

                            # Mark email as read
                            mail.store(msg_id, '+FLAGS', r'\Seen')
                        else:
                            logger.warning(f"Could not find plain text body in email from {sender_email}")

        mail.logout()
        logger.info("Logged out from the email server.")

    except imaplib.IMAP4.error as e:
        logger.error(f"IMAP Error: {e}. Please check your credentials and IMAP server in '{CONFIG_FILE}'.")
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")

def main():
    """Main loop to periodically check for emails."""
    config = read_config()
    if not config:
        return

    interval = int(config.get('CHECK_INTERVAL_SECONDS', 60))
    logger.info(f"Starting email checker. Will check every {interval} seconds.")

    while True:
        process_emails(config)
        logger.info(f"Waiting for {interval} seconds before the next check...")
        time.sleep(interval)

if __name__ == "__main__":
    main()
