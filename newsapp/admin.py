"""Django admin definitions for the Signal Daily app."""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .forms import ArticleImageForm
from .models import Article, ArticleImage, Newsletter, Publisher, SignalDailyUser


class ArticleImageInline(admin.TabularInline):
    """Inline editor for article image uploads in the Django admin."""

    model = ArticleImage
    form = ArticleImageForm
    extra = 1


class ArticleAdmin(admin.ModelAdmin):
    """Admin configuration for managing articles."""

    list_display = ['title', 'author', 'approved', 'created_at']
    list_filter = ['approved', 'created_at', 'publisher']
    search_fields = ['title', 'content']
    inlines = [ArticleImageInline]


class NewsletterAdmin(admin.ModelAdmin):
    """Admin configuration for newsletter management."""

    list_display = ['title', 'author', 'created_at']
    filter_horizontal = ['articles']


class PublisherAdmin(admin.ModelAdmin):
    """Admin configuration for publishers."""

    list_display = ['name']
    filter_horizontal = ['editors', 'journalists']


class SignalDailyUserAdmin(UserAdmin):
    """Admin user configuration with custom subscriptions and security fields."""
    fieldsets = UserAdmin.fieldsets + (
        ('Subscriptions & Security', {
            'fields': ('role', 'subscribed_publishers', 'subscribed_journalists', 'security_question', 'security_answer')
        }),
    )
    filter_horizontal = ['groups', 'user_permissions', 'subscribed_publishers', 'subscribed_journalists']


admin.site.register(SignalDailyUser, SignalDailyUserAdmin)
admin.site.register(Article, ArticleAdmin)
admin.site.register(ArticleImage)
admin.site.register(Newsletter, NewsletterAdmin)
admin.site.register(Publisher, PublisherAdmin)
