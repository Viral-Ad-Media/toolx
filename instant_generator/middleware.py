import hashlib
import time
from datetime import timedelta

from django.db.models import F
from django.http import HttpResponse
from django.utils import timezone

from .models import RateLimitBucket


class RateLimitMiddleware:
    """Shared database counters; trust only REMOTE_ADDR, never arbitrary forwarded headers."""
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path.rstrip('/')
        policy = None
        identity = request.META.get('REMOTE_ADDR', 'unknown')
        if request.method == 'POST' and path in ('/login', '/admin/login', '/signup', '/password_reset', '/activation_resend'):
            policy = (10, 60) if path in ('/login', '/admin/login') else (5, 3600)
        elif request.user.is_authenticated:
            identity = f'user:{request.user.pk}'
            if path.startswith(('/pdf/', '/docx/')):
                policy = (20, 60)
                path = '/exports'
            elif request.method == 'POST' and path in ('/create', '/create_paraphrase', '/profile/edit'):
                policy = (30, 3600)
            elif request.method == 'POST' and path.startswith('/draft/edit/'):
                policy = (30, 3600)
                path = '/draft/edit'
        if policy:
            limit, period = policy
            now = int(time.time())
            key = hashlib.sha256(f'{path}:{identity}'.encode()).hexdigest()
            row, _ = RateLimitBucket.objects.get_or_create(
                key=key, bucket=now // period,
                defaults={'expires_at': timezone.now() + timedelta(seconds=period)},
            )
            RateLimitBucket.objects.filter(pk=row.pk).update(count=F('count') + 1)
            row.refresh_from_db(fields=['count'])
            if row.count > limit:
                response = HttpResponse('Too many requests. Please try again later.', status=429)
                response['Retry-After'] = str(period - now % period)
                return response
        return self.get_response(request)
