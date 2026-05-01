"""Signal handlers for permissions setup and article approval actions."""

import requests
from django.conf import settings
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.core.mail import send_mail
from django.db import OperationalError
from django.db.models.signals import post_migrate, post_save, pre_save
from django.dispatch import receiver
from django.urls import reverse

from .models import Article, Newsletter, Publisher, SignalDailyUser


DEFAULT_USERS = [
    ('demo_reader', 'demo_reader@example.com', 'readerpass', 'reader', False),
    ('demo_writer', 'demo_writer@example.com', 'writerpass', 'journalist', False),
    ('demo_editor', 'demo_editor@example.com', 'editorpass', 'editor', False),
    ('ryan', 'ryan@example.com', 'ryanpass', 'editor', True),
]


def create_default_users():
    for username, email, password, role, is_superuser in DEFAULT_USERS:
        if not SignalDailyUser.objects.filter(username=username).exists():
            if is_superuser:
                user = SignalDailyUser.objects.create_superuser(username=username, email=email, password=password)
                user.role = role
            else:
                user = SignalDailyUser.objects.create_user(username=username, email=email, password=password, role=role)
            user.save()


@receiver(post_migrate)
def create_default_groups(sender, **kwargs):
    """Ensure Reader, Journalist, and Editor groups exist after migrations."""
    if sender.name != 'newsapp':
        return

    article_ct = ContentType.objects.get_for_model(Article)
    newsletter_ct = ContentType.objects.get_for_model(Newsletter)

    reader, _ = Group.objects.get_or_create(name='Reader')
    journalist, _ = Group.objects.get_or_create(name='Journalist')
    editor, _ = Group.objects.get_or_create(name='Editor')

    reader_permissions = Permission.objects.filter(
        content_type__in=[article_ct, newsletter_ct], codename__startswith='view'
    )
    journalist_permissions = Permission.objects.filter(
        content_type__in=[article_ct, newsletter_ct], codename__in=[
            'add_article', 'change_article', 'delete_article', 'view_article',
            'add_newsletter', 'change_newsletter', 'delete_newsletter', 'view_newsletter',
        ]
    )
    editor_permissions = Permission.objects.filter(
        content_type__in=[article_ct, newsletter_ct], codename__in=[
            'change_article', 'delete_article', 'view_article',
            'change_newsletter', 'delete_newsletter', 'view_newsletter',
        ]
    )

    reader.permissions.set(reader_permissions)
    journalist.permissions.set(journalist_permissions)
    editor.permissions.set(editor_permissions)

    try:
        create_default_users()
    except OperationalError:
        pass


@receiver(pre_save, sender=Article)
def cache_article_status(sender, instance, **kwargs):
    """Cache whether an article was previously approved before save."""
    if instance.pk:
        old = Article.objects.filter(pk=instance.pk).first()
        instance._was_approved = old.approved if old else False
    else:
        instance._was_approved = False


@receiver(post_save, sender=Article)
def handle_article_approval(sender, instance, created, **kwargs):
    """Email subscribers and log approval to the internal API after article approval."""
    if instance._was_approved or not instance.approved:
        return

    subscriber_emails = set()
    if instance.publisher:
        subscriber_emails.update(instance.publisher.subscribers.values_list('email', flat=True))
    else:
        subscriber_emails.update(instance.author.journalist_subscribers.values_list('email', flat=True))

    subscriber_emails = {email for email in subscriber_emails if email}
    if subscriber_emails:
        article_url = f"{settings.SITE_URL}{reverse('article_detail', kwargs={'slug': instance.slug})}"
        html_message = f"""
            <html>
                <body style="font-family:Arial,sans-serif;color:#333;">
                    <div style="max-width:680px;margin:0 auto;padding:24px;">
                        <img src="{settings.SITE_URL}/media/logo.png" alt="Signal Daily" style="max-height:60px;display:block;margin-bottom:24px;" />
                        <h1 style="color:#1a1a1a;">Welcome from Signal Daily</h1>
                        <p style="font-size:16px;line-height:1.6;">A new article has just been approved.</p>
                        <h2 style="margin-top:24px;">{instance.title}</h2>
                        <p style="font-size:15px;line-height:1.7;">{instance.summary or instance.content[:220]}</p>
                        <p><a href="{article_url}" style="display:inline-block;padding:14px 24px;background:#222;color:#fff;text-decoration:none;border-radius:4px;">Read the full article</a></p>
                        <hr style="margin:32px 0;border:none;border-top:1px solid #ddd;" />
                        <p style="font-size:14px;color:#777;">Sent by Signal Daily</p>
                    </div>
                </body>
            </html>
        """
        send_mail(
            subject=f'New approved article on Signal Daily: {instance.title}',
            message=f"{instance.summary or instance.title}\nRead more at {article_url}",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=list(subscriber_emails),
            html_message=html_message,
            fail_silently=True,
        )

    try:
        api_url = f'{settings.SITE_URL}{reverse('api-approved')}'
        requests.post(api_url, json={
            'title': instance.title,
            'summary': instance.summary,
            'author': instance.author.username,
            'publisher': instance.publisher.name if instance.publisher else None,
            'approved_at': instance.created_at.isoformat(),
        }, timeout=5)
    except requests.RequestException:
        pass
