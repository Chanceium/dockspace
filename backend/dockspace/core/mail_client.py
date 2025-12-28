"""
IMAP/SMTP email client service.
Handles connecting to mail servers, fetching emails, and sending messages.
"""
import imaplib
import smtplib
import email
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from email.header import decode_header
from typing import List, Dict, Optional, Tuple
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class MailClientException(Exception):
    """Base exception for mail client errors."""
    pass


class IMAPConnectionError(MailClientException):
    """IMAP connection failed."""
    pass


class SMTPConnectionError(MailClientException):
    """SMTP connection failed."""
    pass


class MailClient:
    """
    Email client for IMAP/SMTP operations.

    Handles:
    - IMAP connection and email fetching
    - SMTP connection and email sending
    - Email parsing and formatting
    - Folder management
    """

    def __init__(self, imap_host: str, imap_port: int, imap_security: str,
                 smtp_host: str, smtp_port: int, smtp_security: str,
                 username: str, password: str):
        """
        Initialize mail client with connection details.

        Args:
            imap_host: IMAP server hostname
            imap_port: IMAP server port
            imap_security: 'None', 'SSL/TLS', or 'STARTTLS'
            smtp_host: SMTP server hostname
            smtp_port: SMTP server port
            smtp_security: 'None', 'SSL/TLS', or 'STARTTLS'
            username: Email account username
            password: Email account password
        """
        self.imap_host = imap_host
        self.imap_port = imap_port
        self.imap_security = imap_security
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.smtp_security = smtp_security
        self.username = username
        self.password = password
        self.imap_connection = None
        self.smtp_connection = None

    def connect_imap(self) -> imaplib.IMAP4:
        """
        Connect to IMAP server.

        Returns:
            IMAP4 connection object

        Raises:
            IMAPConnectionError: If connection fails
        """
        try:
            if self.imap_security == 'SSL/TLS':
                self.imap_connection = imaplib.IMAP4_SSL(self.imap_host, self.imap_port)
            else:
                self.imap_connection = imaplib.IMAP4(self.imap_host, self.imap_port)
                if self.imap_security == 'STARTTLS':
                    self.imap_connection.starttls()

            self.imap_connection.login(self.username, self.password)
            logger.info(f"IMAP connected: {self.username}@{self.imap_host}")
            return self.imap_connection

        except imaplib.IMAP4.error as e:
            logger.error(f"IMAP connection failed: {e}")
            error_msg = str(e).lower()
            if 'authentication' in error_msg or 'login' in error_msg:
                raise IMAPConnectionError(f"Authentication failed. Please check your username and password.")
            raise IMAPConnectionError(f"IMAP connection failed: {str(e)}")
        except OSError as e:
            # Network errors (DNS, connection refused, etc.)
            logger.error(f"IMAP network error: {e}")
            if e.errno == -2 or 'Name or service not known' in str(e):
                raise IMAPConnectionError(f"Cannot resolve IMAP host '{self.imap_host}'. Please check the server address.")
            if 'Connection refused' in str(e):
                raise IMAPConnectionError(f"Connection refused by '{self.imap_host}:{self.imap_port}'. Please check the host and port.")
            raise IMAPConnectionError(f"Network error connecting to IMAP server: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected IMAP error: {e}")
            raise IMAPConnectionError(f"Unexpected error: {str(e)}")

    def connect_smtp(self) -> smtplib.SMTP:
        """
        Connect to SMTP server.

        Returns:
            SMTP connection object

        Raises:
            SMTPConnectionError: If connection fails
        """
        try:
            if self.smtp_security == 'SSL/TLS':
                self.smtp_connection = smtplib.SMTP_SSL(self.smtp_host, self.smtp_port, timeout=10)
            else:
                self.smtp_connection = smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=10)
                if self.smtp_security == 'STARTTLS':
                    self.smtp_connection.starttls()

            self.smtp_connection.login(self.username, self.password)
            logger.info(f"SMTP connected: {self.username}@{self.smtp_host}")
            return self.smtp_connection

        except smtplib.SMTPException as e:
            logger.error(f"SMTP connection failed: {e}")
            error_msg = str(e).lower()
            if 'authentication' in error_msg or 'login' in error_msg:
                raise SMTPConnectionError(f"Authentication failed. Please check your username and password.")
            raise SMTPConnectionError(f"SMTP connection failed: {str(e)}")
        except OSError as e:
            # Network errors (DNS, connection refused, etc.)
            logger.error(f"SMTP network error: {e}")
            if e.errno == -2 or 'Name or service not known' in str(e):
                raise SMTPConnectionError(f"Cannot resolve SMTP host '{self.smtp_host}'. Please check the server address.")
            if 'Connection refused' in str(e):
                raise SMTPConnectionError(f"Connection refused by '{self.smtp_host}:{self.smtp_port}'. Please check the host and port.")
            raise SMTPConnectionError(f"Network error connecting to SMTP server: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected SMTP error: {e}")
            raise SMTPConnectionError(f"Unexpected error: {str(e)}")

    def test_connection(self) -> Tuple[bool, str]:
        """
        Test both IMAP and SMTP connections.

        Returns:
            Tuple of (success, message)
        """
        try:
            # Test IMAP
            imap = self.connect_imap()
            imap.logout()

            # Test SMTP
            smtp = self.connect_smtp()
            smtp.quit()

            return True, "Connection successful"

        except IMAPConnectionError as e:
            return False, f"IMAP error: {str(e)}"
        except SMTPConnectionError as e:
            return False, f"SMTP error: {str(e)}"
        except Exception as e:
            return False, f"Unexpected error: {str(e)}"

    def list_folders(self) -> List[Dict[str, any]]:
        """
        List all IMAP folders/mailboxes.

        Returns:
            List of folder dictionaries with name and count
        """
        try:
            imap = self.connect_imap()
            status, folders = imap.list()

            folder_list = []
            for folder in folders:
                # Parse folder response: e.g., b'(\\HasNoChildren) "." "INBOX"'
                parts = folder.decode().split('"')
                if len(parts) >= 3:
                    folder_name = parts[-2]

                    # Get message count
                    status, data = imap.select(f'"{folder_name}"', readonly=True)
                    count = int(data[0]) if status == 'OK' else 0

                    # Map common folder names to icons
                    icon_map = {
                        'INBOX': 'ri-inbox-line',
                        'Sent': 'ri-send-plane-line',
                        'Drafts': 'ri-draft-line',
                        'Trash': 'ri-delete-bin-line',
                        'Spam': 'ri-spam-line',
                        'Junk': 'ri-spam-line',
                        'Archive': 'ri-archive-line',
                    }

                    icon = icon_map.get(folder_name, 'ri-folder-line')

                    folder_list.append({
                        'name': folder_name,
                        'value': folder_name.lower(),
                        'icon': icon,
                        'count': count
                    })

            imap.logout()
            return folder_list

        except Exception as e:
            logger.error(f"Failed to list folders: {e}")
            raise MailClientException(f"Failed to list folders: {str(e)}")

    def decode_header_value(self, header_value: str) -> str:
        """Decode email header value handling encoding."""
        if not header_value:
            return ""

        decoded_parts = decode_header(header_value)
        decoded_string = ""

        for part, encoding in decoded_parts:
            if isinstance(part, bytes):
                decoded_string += part.decode(encoding or 'utf-8', errors='ignore')
            else:
                decoded_string += part

        return decoded_string

    def parse_email_address(self, address: str) -> Tuple[str, str]:
        """
        Parse email address into name and email.

        Args:
            address: Email address string (e.g., "Name <email@example.com>")

        Returns:
            Tuple of (name, email)
        """
        if '<' in address and '>' in address:
            name = address.split('<')[0].strip().strip('"')
            email_addr = address.split('<')[1].split('>')[0].strip()
            return name, email_addr
        return "", address.strip()

    def fetch_emails(self, folder: str = 'INBOX', limit: int = 50, offset: int = 0) -> List[Dict[str, any]]:
        """
        Fetch emails from a folder.

        Args:
            folder: Folder name (default: INBOX)
            limit: Maximum number of emails to fetch
            offset: Number of emails to skip

        Returns:
            List of email dictionaries
        """
        try:
            imap = self.connect_imap()
            imap.select(f'"{folder}"', readonly=True)

            # Search for all emails
            status, data = imap.search(None, 'ALL')
            email_ids = data[0].split()

            # Reverse to get newest first
            email_ids = list(reversed(email_ids))

            # Apply pagination
            email_ids = email_ids[offset:offset + limit]

            emails = []
            for email_id in email_ids:
                try:
                    status, data = imap.fetch(email_id, '(RFC822)')
                    raw_email = data[0][1]
                    msg = email.message_from_bytes(raw_email)

                    # Parse from address
                    from_header = self.decode_header_value(msg.get('From', ''))
                    from_name, from_email = self.parse_email_address(from_header)

                    # Get subject
                    subject = self.decode_header_value(msg.get('Subject', 'No Subject'))

                    # Get date
                    date_str = msg.get('Date', '')
                    try:
                        date_obj = email.utils.parsedate_to_datetime(date_str)
                        date_formatted = date_obj.strftime('%Y-%m-%d')
                        time_formatted = date_obj.strftime('%I:%M %p')
                    except:
                        date_formatted = 'Unknown'
                        time_formatted = ''

                    # Get body preview
                    body_preview = self.extract_body_preview(msg)

                    # Check for attachments
                    has_attachments = any(part.get_content_disposition() == 'attachment'
                                         for part in msg.walk())

                    emails.append({
                        'id': int(email_id),
                        'uid': email_id.decode(),
                        'from': from_name or from_email,
                        'fromEmail': from_email,
                        'subject': subject,
                        'preview': body_preview[:150],
                        'date': date_formatted,
                        'time': time_formatted,
                        'read': '\\Seen' in str(data),
                        'starred': '\\Flagged' in str(data),
                        'hasAttachments': has_attachments,
                    })

                except Exception as e:
                    logger.error(f"Failed to parse email {email_id}: {e}")
                    continue

            imap.logout()
            return emails

        except Exception as e:
            logger.error(f"Failed to fetch emails: {e}")
            raise MailClientException(f"Failed to fetch emails: {str(e)}")

    def extract_body_preview(self, msg) -> str:
        """Extract plain text body preview from email message."""
        body = ""

        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get("Content-Disposition"))

                if content_type == "text/plain" and "attachment" not in content_disposition:
                    try:
                        body = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                        break
                    except:
                        pass
        else:
            try:
                body = msg.get_payload(decode=True).decode('utf-8', errors='ignore')
            except:
                pass

        # Clean up body
        body = body.replace('\r\n', ' ').replace('\n', ' ').strip()
        return body

    def fetch_email_detail(self, folder: str, email_id: str) -> Dict[str, any]:
        """
        Fetch full email details including body and attachments.

        Args:
            folder: Folder name
            email_id: Email UID

        Returns:
            Email detail dictionary
        """
        try:
            imap = self.connect_imap()
            imap.select(f'"{folder}"', readonly=True)

            status, data = imap.fetch(email_id.encode(), '(RFC822)')
            raw_email = data[0][1]
            msg = email.message_from_bytes(raw_email)

            # Parse from, to, cc
            from_header = self.decode_header_value(msg.get('From', ''))
            from_name, from_email = self.parse_email_address(from_header)

            to_header = self.decode_header_value(msg.get('To', ''))
            cc_header = self.decode_header_value(msg.get('Cc', ''))

            # Get subject and date
            subject = self.decode_header_value(msg.get('Subject', 'No Subject'))
            date_str = msg.get('Date', '')

            try:
                date_obj = email.utils.parsedate_to_datetime(date_str)
                date_formatted = date_obj.strftime('%Y-%m-%d')
                time_formatted = date_obj.strftime('%I:%M %p')
            except:
                date_formatted = 'Unknown'
                time_formatted = ''

            # Extract body
            body_plain = ""
            body_html = ""
            attachments = []

            if msg.is_multipart():
                for part in msg.walk():
                    content_type = part.get_content_type()
                    content_disposition = str(part.get("Content-Disposition"))

                    if "attachment" in content_disposition:
                        # Handle attachment
                        filename = part.get_filename()
                        if filename:
                            attachments.append({
                                'name': self.decode_header_value(filename),
                                'size': len(part.get_payload(decode=True)),
                            })
                    elif content_type == "text/plain":
                        try:
                            body_plain = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                        except:
                            pass
                    elif content_type == "text/html":
                        try:
                            body_html = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                        except:
                            pass
            else:
                try:
                    body_plain = msg.get_payload(decode=True).decode('utf-8', errors='ignore')
                except:
                    pass

            imap.logout()

            return {
                'id': email_id,
                'from': from_name or from_email,
                'fromEmail': from_email,
                'to': to_header,
                'cc': cc_header,
                'subject': subject,
                'body': body_plain or body_html,
                'bodyHtml': body_html,
                'date': date_formatted,
                'time': time_formatted,
                'attachments': attachments,
            }

        except Exception as e:
            logger.error(f"Failed to fetch email detail: {e}")
            raise MailClientException(f"Failed to fetch email detail: {str(e)}")

    def send_email(self, to: str, subject: str, body: str,
                   cc: Optional[str] = None, bcc: Optional[str] = None,
                   reply_to: Optional[str] = None) -> bool:
        """
        Send an email via SMTP.

        Args:
            to: Recipient email address(es)
            subject: Email subject
            body: Email body (plain text)
            cc: CC recipients (optional)
            bcc: BCC recipients (optional)
            reply_to: Reply-To header (optional)

        Returns:
            True if sent successfully
        """
        try:
            msg = MIMEMultipart()
            msg['From'] = self.username
            msg['To'] = to
            msg['Subject'] = subject

            if cc:
                msg['Cc'] = cc
            if reply_to:
                msg['Reply-To'] = reply_to

            msg.attach(MIMEText(body, 'plain'))

            smtp = self.connect_smtp()

            # Build recipient list
            recipients = [to]
            if cc:
                recipients.extend([addr.strip() for addr in cc.split(',')])
            if bcc:
                recipients.extend([addr.strip() for addr in bcc.split(',')])

            smtp.sendmail(self.username, recipients, msg.as_string())
            smtp.quit()

            logger.info(f"Email sent successfully to {to}")
            return True

        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            raise MailClientException(f"Failed to send email: {str(e)}")

    def close(self):
        """Close all connections."""
        if self.imap_connection:
            try:
                self.imap_connection.logout()
            except:
                pass

        if self.smtp_connection:
            try:
                self.smtp_connection.quit()
            except:
                pass
