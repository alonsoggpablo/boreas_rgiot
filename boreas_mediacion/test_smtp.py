#!/usr/bin/env python
"""Test SMTP connection with auth"""
import smtplib
import os
import sys

sys.path.insert(0, '/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'boreas_mediacion.settings')

import django
django.setup()

from django.conf import settings

print("=" * 70)
print("SMTP Configuration Test")
print("=" * 70)
print(f"EMAIL_HOST: {settings.EMAIL_HOST}")
print(f"EMAIL_PORT: {settings.EMAIL_PORT}")
print(f"EMAIL_HOST_USER: {settings.EMAIL_HOST_USER}")
print(f"EMAIL_HOST_PASSWORD: {'*' * len(settings.EMAIL_HOST_PASSWORD)} ({len(settings.EMAIL_HOST_PASSWORD)} chars)")
print(f"EMAIL_USE_TLS: {settings.EMAIL_USE_TLS}")
print()

try:
    print("1. Creating SMTP connection...")
    server = smtplib.SMTP(settings.EMAIL_HOST, settings.EMAIL_PORT, local_hostname='boreas.rggestionyenergia.com')
    print(f"   ✅ Connected to {settings.EMAIL_HOST}:{settings.EMAIL_PORT}")
    
    print("\n2. Starting TLS...")
    server.starttls()
    print("   ✅ TLS negotiation complete")
    
    print(f"\n3. Logging in as {settings.EMAIL_HOST_USER}...")
    server.login(settings.EMAIL_HOST_USER, settings.EMAIL_HOST_PASSWORD)
    print("   ✅ Authentication successful!")
    
    print("\n4. Sending test email...")
    msg = f"From: {settings.EMAIL_HOST_USER}\nTo: alonsogpablo@gestionyenergia.com\nSubject: SMTP Test\n\nTest email from Boreas."
    server.sendmail(settings.EMAIL_HOST_USER, ['alonsogpablo@gestionyenergia.com'], msg)
    print("   ✅ Email sent!")
    
    server.quit()
    print("\n✅ All tests passed!")
    
except Exception as e:
    print(f"\n❌ Error: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
