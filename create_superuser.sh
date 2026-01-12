#!/bin/bash
# Script to create Django superuser "pablo" with password "laura10"
# Usage: ./create_superuser.sh
# Or run from host: docker-compose exec web bash -c "python -c '...'"

echo "Creating superuser 'pablo' with password 'laura10'..."

docker-compose exec web python -c "
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'boreas_mediacion.settings')
django.setup()
from django.contrib.auth.models import User

username = 'pablo'
password = 'laura10'
email = 'pablo@example.com'

if not User.objects.filter(username=username).exists():
    User.objects.create_superuser(username, email, password)
    print(f'✅ Superuser {username} created successfully')
    print(f'   Username: {username}')
    print(f'   Email: {email}')
    print(f'   Password: {password}')
else:
    user = User.objects.get(username=username)
    user.set_password(password)
    user.save()
    print(f'✅ User {username} already exists - password updated')
    print(f'   Username: {username}')
    print(f'   Password: {password}')
" 2>&1 | grep -v 'Reported measure'
