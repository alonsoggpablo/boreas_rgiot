#!/usr/bin/env python
"""
Script to create a Django superuser programmatically
Usage: python create_superuser.py
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'boreas_mediacion.settings')
django.setup()

from django.contrib.auth.models import User

username = 'pablo'
password = 'laura10'
email = 'pablo@example.com'

# Check if user already exists
if User.objects.filter(username=username).exists():
    print(f"✅ User '{username}' already exists")
    user = User.objects.get(username=username)
    # Update password
    user.set_password(password)
    user.save()
    print(f"✅ Password updated for user '{username}'")
else:
    # Create the superuser
    User.objects.create_superuser(username=username, email=email, password=password)
    print(f"✅ Superuser '{username}' created successfully")
    print(f"   Username: {username}")
    print(f"   Password: {password}")
