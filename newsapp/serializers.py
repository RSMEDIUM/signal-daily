"""DRF serializers for the Signal Daily REST API."""

from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import Article, ArticleImage, Newsletter, NewsletterSubscriber, Publisher

User = get_user_model()


class ArticleImageSerializer(serializers.ModelSerializer):
    """Serialize article images with captions."""

    class Meta:
        model = ArticleImage
        fields = ['id', 'image', 'caption']


class PublisherSerializer(serializers.ModelSerializer):
    """Serialize publisher details for article metadata."""

    class Meta:
        model = Publisher
        fields = ['id', 'name', 'description', 'logo']


class UserSerializer(serializers.ModelSerializer):
    """Serialize basic user information used in article endpoints."""

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'role']


class ArticleSerializer(serializers.ModelSerializer):
    """Serialize articles and include nested author, publisher, and image data."""
    author = UserSerializer(read_only=True)
    publisher = PublisherSerializer(read_only=True)
    images = ArticleImageSerializer(many=True, read_only=True)

    class Meta:
        model = Article
        fields = ['id', 'title', 'summary', 'content', 'author', 'publisher', 'approved', 'created_at', 'slug', 'images']
        read_only_fields = ['approved', 'created_at', 'slug', 'images']


class NewsletterSerializer(serializers.ModelSerializer):
    """Serialize newsletters with nested article data."""
    author = UserSerializer(read_only=True)
    articles = ArticleSerializer(many=True, read_only=True)

    class Meta:
        model = Newsletter
        fields = ['id', 'title', 'description', 'created_at', 'author', 'articles']


class NewsletterSubscriberSerializer(serializers.ModelSerializer):
    """Serialize anonymous newsletter email subscribers."""

    class Meta:
        model = NewsletterSubscriber
        fields = ['id', 'email', 'created_at']
