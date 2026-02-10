"""
Email Signal Parser for Trading AI
Parses trading signals from emails via IMAP.
"""
import asyncio
import imaplib
import email
from email.header import decode_header
import os
import re
import logging
from datetime import datetime, timezone
from typing import Optional, List, Callable
from dataclasses import dataclass
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


@dataclass
class EmailConfig:
    """Email IMAP configuration"""
    imap_server: str
    email_address: str
    password: str
    folder: str = "INBOX"
    check_interval: int = 60  # seconds
    mark_as_read: bool = True
    
    # Filter options
    from_addresses: List[str] = None  # Only process emails from these addresses
    subject_filters: List[str] = None  # Only process if subject contains these strings


class EmailSignalParser:
    """
    Email client for fetching and parsing trading signals from emails.
    """
    
    def __init__(self, config: EmailConfig, signal_callback: Callable = None):
        self.config = config
        self.signal_callback = signal_callback
        self.mail: Optional[imaplib.IMAP4_SSL] = None
        self.running = False
        self.processed_ids = set()
        
        logger.info(f"EmailSignalParser initialized for {config.email_address}")
    
    def connect(self) -> bool:
        """Connect to IMAP server"""
        try:
            self.mail = imaplib.IMAP4_SSL(self.config.imap_server)
            self.mail.login(self.config.email_address, self.config.password)
            self.mail.select(self.config.folder)
            logger.info(f"Connected to {self.config.imap_server}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from IMAP server"""
        if self.mail:
            try:
                self.mail.close()
                self.mail.logout()
            except:
                pass
        logger.info("Disconnected from email server")
    
    async def start_polling(self):
        """Start polling for new emails"""
        if not self.connect():
            return
        
        self.running = True
        logger.info(f"Started polling every {self.config.check_interval} seconds")
        
        while self.running:
            try:
                await self._check_new_emails()
            except Exception as e:
                logger.error(f"Error checking emails: {e}")
                # Reconnect on error
                self.connect()
            
            await asyncio.sleep(self.config.check_interval)
    
    async def _check_new_emails(self):
        """Check for new unread emails"""
        self.mail.noop()  # Keep connection alive
        
        # Search for unread emails
        status, messages = self.mail.search(None, 'UNSEEN')
        
        if status != 'OK':
            return
        
        email_ids = messages[0].split()
        
        for email_id in email_ids:
            if email_id in self.processed_ids:
                continue
            
            try:
                await self._process_email(email_id)
                self.processed_ids.add(email_id)
            except Exception as e:
                logger.error(f"Error processing email {email_id}: {e}")
    
    async def _process_email(self, email_id: bytes):
        """Process a single email"""
        status, msg_data = self.mail.fetch(email_id, '(RFC822)')
        
        if status != 'OK':
            return
        
        raw_email = msg_data[0][1]
        msg = email.message_from_bytes(raw_email)
        
        # Get email metadata
        subject = self._decode_header(msg['Subject'])
        from_addr = self._decode_header(msg['From'])
        date = msg['Date']
        
        logger.debug(f"Processing email: {subject} from {from_addr}")
        
        # Apply filters
        if not self._matches_filters(from_addr, subject):
            logger.debug(f"Email filtered out: {subject}")
            return
        
        # Get email body
        body = self._get_email_body(msg)
        
        if not body:
            return
        
        # Check if looks like trading signal
        if self._looks_like_signal(body):
            logger.info(f"Potential signal detected in email: {subject}")
            
            # Parse signal
            parsed = self.parse_signal(body)
            
            signal_data = {
                "source": "email",
                "source_id": f"email_{email_id.decode()}",
                "subject": subject,
                "from": from_addr,
                "text": body,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "parsed": parsed
            }
            
            # Call callback
            if self.signal_callback:
                try:
                    await self.signal_callback(signal_data)
                except Exception as e:
                    logger.error(f"Signal callback failed: {e}")
        
        # Mark as read if configured
        if self.config.mark_as_read:
            self.mail.store(email_id, '+FLAGS', '\\Seen')
    
    def _decode_header(self, header: str) -> str:
        """Decode email header"""
        if not header:
            return ""
        
        decoded_parts = decode_header(header)
        result = ""
        for part, encoding in decoded_parts:
            if isinstance(part, bytes):
                result += part.decode(encoding or 'utf-8', errors='replace')
            else:
                result += part
        return result
    
    def _get_email_body(self, msg) -> str:
        """Extract email body text"""
        body = ""
        
        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get("Content-Disposition"))
                
                # Skip attachments
                if "attachment" in content_disposition:
                    continue
                
                if content_type == "text/plain":
                    try:
                        body = part.get_payload(decode=True).decode('utf-8', errors='replace')
                        break
                    except:
                        pass
                elif content_type == "text/html" and not body:
                    try:
                        html = part.get_payload(decode=True).decode('utf-8', errors='replace')
                        soup = BeautifulSoup(html, 'html.parser')
                        body = soup.get_text(separator='\n')
                    except:
                        pass
        else:
            try:
                body = msg.get_payload(decode=True).decode('utf-8', errors='replace')
            except:
                pass
        
        return body.strip()
    
    def _matches_filters(self, from_addr: str, subject: str) -> bool:
        """Check if email matches configured filters"""
        # From address filter
        if self.config.from_addresses:
            from_lower = from_addr.lower()
            if not any(addr.lower() in from_lower for addr in self.config.from_addresses):
                return False
        
        # Subject filter
        if self.config.subject_filters:
            subject_lower = subject.lower()
            if not any(filt.lower() in subject_lower for filt in self.config.subject_filters):
                return False
        
        return True
    
    def _looks_like_signal(self, text: str) -> bool:
        """Check if text looks like a trading signal"""
        text_upper = text.upper()
        
        indicators = [
            any(x in text_upper for x in ['LONG', 'SHORT', 'BUY', 'SELL']),
            bool(re.search(r'ENTRY[:\s]*[\d.,]+', text_upper)),
            bool(re.search(r'(?:SL|STOP)[:\s]*[\d.,]+', text_upper)),
            bool(re.search(r'(?:TP|TARGET)[:\s]*[\d.,]+', text_upper)),
            bool(re.search(r'[A-Z]{2,6}[/\-]?(?:USDT|USD|BTC|EUR)', text_upper))
        ]
        
        return sum(indicators) >= 2
    
    def parse_signal(self, text: str) -> dict:
        """Parse trading signal from email text"""
        result = {
            "asset": None,
            "action": None,
            "entry": None,
            "stop_loss": None,
            "take_profits": [],
            "leverage": None,
            "confidence": 0.0
        }
        
        text_upper = text.upper()
        
        # Asset
        asset_match = re.search(r'([A-Z]{2,6})[/\-]?(USDT|USDC|USD|BTC|ETH)', text_upper)
        if asset_match:
            result["asset"] = f"{asset_match.group(1)}/{asset_match.group(2)}"
        
        # Action
        if any(x in text_upper for x in ['LONG', 'BUY']):
            result["action"] = "long"
        elif any(x in text_upper for x in ['SHORT', 'SELL']):
            result["action"] = "short"
        
        # Entry
        entry_match = re.search(r'ENTRY[:\s]*([0-9,.]+)', text_upper)
        if entry_match:
            result["entry"] = self._parse_number(entry_match.group(1))
        
        # Stop Loss
        sl_match = re.search(r'(?:SL|STOP\s*LOSS)[:\s]*([0-9,.]+)', text_upper)
        if sl_match:
            result["stop_loss"] = self._parse_number(sl_match.group(1))
        
        # Take Profits
        for match in re.finditer(r'(?:TP|TARGET)\s*\d*[:\s]*([0-9,.]+)', text_upper):
            tp = self._parse_number(match.group(1))
            if tp and tp not in result["take_profits"]:
                result["take_profits"].append(tp)
        result["take_profits"] = sorted(result["take_profits"])
        
        # Leverage
        lev_match = re.search(r'(?:LEVERAGE|LEV)[:\s]*(\d+)', text_upper)
        if lev_match:
            result["leverage"] = int(lev_match.group(1))
        
        # Calculate confidence
        filled = sum(1 for v in [result["asset"], result["action"], result["entry"], result["stop_loss"]] if v)
        result["confidence"] = filled / 4.0
        if result["take_profits"]:
            result["confidence"] = min(1.0, result["confidence"] + 0.15)
        
        return result
    
    def _parse_number(self, text: str) -> Optional[float]:
        """Parse number from text"""
        if not text:
            return None
        try:
            text = text.strip().replace(',', '')
            return float(text)
        except ValueError:
            return None
    
    def stop(self):
        """Stop the email parser"""
        self.running = False
        self.disconnect()


# Factory function
async def create_email_parser(
    imap_server: str,
    email_address: str,
    password: str,
    signal_callback: Callable,
    from_addresses: List[str] = None,
    subject_filters: List[str] = None
) -> EmailSignalParser:
    """Create and configure an email signal parser"""
    config = EmailConfig(
        imap_server=imap_server,
        email_address=email_address,
        password=password,
        from_addresses=from_addresses,
        subject_filters=subject_filters or ["signal", "trade", "alert"]
    )
    
    parser = EmailSignalParser(config, signal_callback)
    return parser
