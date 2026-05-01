"""Data models for the Signal Daily application.

This module defines the custom user model, publisher, article, image, and newsletter
models used throughout the news platform.
"""

from django.conf import settings
from django.contrib.auth.models import AbstractUser, Group
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from django.utils.text import slugify
from PIL import Image


class SignalDailyUser(AbstractUser):
    """Custom user model with roles and subscription fields."""

    ROLE_READER = 'reader'
    ROLE_JOURNALIST = 'journalist'
    ROLE_EDITOR = 'editor'

    ROLE_CHOICES = [
        (ROLE_READER, 'Reader'),
        (ROLE_JOURNALIST, 'Journalist'),
        (ROLE_EDITOR, 'Editor'),
    ]

    role = models.CharField(max_length=16, choices=ROLE_CHOICES, default=ROLE_READER)
    subscribed_publishers = models.ManyToManyField('Publisher', blank=True, related_name='subscribers')
    subscribed_journalists = models.ManyToManyField('self', blank=True, symmetrical=False, related_name='journalist_subscribers')
    security_question = models.CharField(max_length=255, blank=True, null=True)
    security_answer = models.CharField(max_length=255, blank=True, null=True)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.assign_group()
        if self.role != self.ROLE_READER:
            self.subscribed_publishers.clear()
            self.subscribed_journalists.clear()

    def assign_group(self):
        group_name = self.role.capitalize()
        group, _ = Group.objects.get_or_create(name=group_name)
        allowed_groups = Group.objects.filter(name__in=['Reader', 'Journalist', 'Editor'])
        for existing in allowed_groups:
            if existing != group and existing in self.groups.all():
                self.groups.remove(existing)
        if group not in self.groups.all():
            self.groups.add(group)

    def __str__(self):
        return self.username


class Publisher(models.Model):
    """Publisher entity that can have editors and journalists."""

    name = models.CharField(max_length=128)
    description = models.TextField(blank=True)
    logo = models.ImageField(upload_to='publisher_logos/', blank=True, null=True)
    editors = models.ManyToManyField(settings.AUTH_USER_MODEL, blank=True, related_name='editor_publishers')
    journalists = models.ManyToManyField(settings.AUTH_USER_MODEL, blank=True, related_name='publisher_journalists')

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class Category(models.Model):
    """Topic category for organizing articles."""

    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True, blank=True)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ['name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)[:120]
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Article(models.Model):
    """Article content published by journalists or publishers."""

    title = models.CharField(max_length=255)
    summary = models.CharField(max_length=320, blank=True)
    content = models.TextField()
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='articles')
    publisher = models.ForeignKey(Publisher, null=True, blank=True, on_delete=models.SET_NULL, related_name='articles')
    featured = models.BooleanField(default=False)
    pinned = models.BooleanField(default=False)
    categories = models.ManyToManyField('Category', blank=True, related_name='articles')
    created_at = models.DateTimeField(default=timezone.now)
    approved = models.BooleanField(default=False)
    slug = models.SlugField(max_length=255, blank=True, unique=True)

    class Meta:
        ordering = ['-created_at']

    def clean(self):
        if self.author_id is None:
            return
        if not self.publisher and self.author.role not in [SignalDailyUser.ROLE_JOURNALIST, SignalDailyUser.ROLE_EDITOR] and not self.author.is_superuser:
            raise ValidationError('An independent article must be authored by a journalist, editor, or associated with a publisher.')

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)[:255]
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

    @property
    def headline_image(self):
        first_image = self.images.first()
        return first_image.image.url if first_image else ''


class ArticleImage(models.Model):
    """Additional image assets attached to an article."""

    article = models.ForeignKey(Article, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='article_images/')
    caption = models.CharField(max_length=255, blank=True)

    def clean(self):
        if self.image:
            try:
                image = Image.open(self.image)
                width, height = image.size
                if width < 600 or height < 400:
                    raise ValidationError('Article images must be at least 600x400 pixels.')
            except OSError:
                raise ValidationError('Uploaded file is not a valid image.')

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f'Image for {self.article.title}'


class Newsletter(models.Model):
    """Newsletter collection created by journalists and editors."""

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='newsletters')
    articles = models.ManyToManyField(Article, blank=True, related_name='newsletters')

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title


class Comment(models.Model):
    """Comments left on approved articles by signed-in users."""

    article = models.ForeignKey(Article, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='comments')
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f'Comment by {self.author or "Guest"} on {self.article.title}'


class NewsletterSubscriber(models.Model):
    """Anonymous newsletter signup records for email-only subscribers."""

    email = models.EmailField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.email
