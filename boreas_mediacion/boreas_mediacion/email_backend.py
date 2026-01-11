"""
Custom SMTP Email Backend with fixed HELO hostname
Fixes "Invalid HELO name" errors from strict SMTP servers
"""
import smtplib
from django.core.mail.backends.smtp import EmailBackend
from django.conf import settings


class FixedHELOSMTPBackend(EmailBackend):
    """
    SMTP backend that sends a proper FQDN in HELO instead of container hostname.
    Fixes "Access denied - Invalid HELO name (RFC2821 4.1.1.1)" errors.
    """
    
    def open(self):
        """
        Ensure an SMTP connection to the email server. Return whether or not a
        new connection was required (True or False) or an exception if there was
        an error. Retrieve a new connection/reconnect if needed.
        
        We override the parent to set a proper HELO hostname.
        """
        if self.connection is not None:
            # Connection already exists
            return False

        connection_params = {
            'local_hostname': 'boreas.rggestionyenergia.com',  # Use a proper FQDN for HELO
        }
        
        try:
            self.connection = smtplib.SMTP(
                self.host,
                self.port,
                **connection_params,
                timeout=self.timeout,
            )

            # TLS encapsulation
            if self.use_tls:
                self.connection.starttls()
            if self.use_ssl:
                # Calling starttls() before login() is explicitly forbidden in PEP 487
                # on most transports, so this should be done after the initial SMTP
                # negotiation.
                if not self.use_tls:
                    self.connection.starttls()

            if self.username and self.password:
                self.connection.login(self.username, self.password)
            return True
        except OSError:
            if not self.fail_silently:
                raise
