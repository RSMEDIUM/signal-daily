"""Application views for Signal Daily.

This module contains the frontend page views, authentication flows, subscription
endpoints, and API view classes used by the Django application.
"""

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, get_user_model, login, logout
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Q
from django.http import Http404, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.core.mail import send_mail
from django.urls import reverse

from rest_framework import generics, permissions, status, viewsets
from rest_framework.authentication import TokenAuthentication
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.response import Response
from rest_framework.views import APIView

from .forms import (
    ArticleForm,
    ArticleImageFormSet,
    CategoryForm,
    CommentForm,
    NewsletterForm,
    NewsletterSignupForm,
    PublisherForm,
    PasswordResetRequestForm,
    RegistrationForm,
    SecurityAnswerForm,
    SignalDailyLoginForm,
    UserRoleForm,
)
from .models import Article, Category, Comment, Newsletter, NewsletterSubscriber, Publisher
from .permissions import IsEditorOrJournalist, IsJournalist
from .serializers import (
    ArticleSerializer,
    PublisherSerializer,
    UserSerializer,
    NewsletterSubscriberSerializer,
)

User = get_user_model()


def home(request):
    """Render the homepage with hero, featured articles, and newsletter signup.
    
    Displays a pinned hero article (or featured if no pinned), up to 6 featured
    articles, recent articles, and a newsletter signup form.
    
    Args:
        request: HTTP request object.
    
    Returns:
        HttpResponse: Rendered home page template.
    """
    hero_article = Article.objects.filter(approved=True, pinned=True).order_by('-created_at').first()
    if not hero_article:
        hero_article = Article.objects.filter(approved=True, featured=True).order_by('-created_at').first()
    if hero_article:
        featured_articles = Article.objects.filter(approved=True, featured=True).exclude(pk=hero_article.pk).order_by('-created_at')[:6]
    else:
        featured_articles = Article.objects.filter(approved=True, featured=True).order_by('-created_at')[:6]
    recent_articles = Article.objects.filter(approved=True).order_by('-created_at')
    signup_form = NewsletterSignupForm()
    return render(request, 'newsapp/home.html', {
        'hero_article': hero_article,
        'featured_articles': featured_articles,
        'recent_articles': recent_articles,
        'signup_form': signup_form,
    })


def newsletter_signup(request):
    """Handle newsletter signup form submission from homepage.
    
    Creates a new NewsletterSubscriber record or notifies if already subscribed.
    
    Args:
        request: HTTP POST request with email field.
    
    Returns:
        HttpResponse: Redirect to home page with success/error message.
    """
    if request.method != 'POST':
        return redirect('home')
    form = NewsletterSignupForm(request.POST)
    if form.is_valid():
        email = form.cleaned_data['email'].lower()
        subscriber, created = NewsletterSubscriber.objects.get_or_create(email=email)
        if created:
            messages.success(request, 'Thanks for subscribing to Signal Daily.')
        else:
            messages.info(request, 'You are already subscribed to the newsletter.')
    else:
        messages.error(request, 'Please enter a valid email address.')
    return redirect('home')


def _is_editor(user):
    """Check if user has editor privileges.
    
    Args:
        user: User instance to check.
    
    Returns:
        bool: True if user is authenticated and is superuser or has editor role.
    """
    return user.is_authenticated and (user.is_superuser or user.role == 'editor')


def about(request):
    """Render the about page.
    
    Args:
        request: HTTP request object.
    
    Returns:
        HttpResponse: Rendered about page template.
    """
    return render(request, 'newsapp/about.html')


def article_list(request):
    """Display a list of all approved articles.
    
    Args:
        request: HTTP request object.
    
    Returns:
        HttpResponse: Rendered article list page with approved articles.
    """
    articles = Article.objects.filter(approved=True).order_by('-created_at')
    return render(request, 'newsapp/article_list.html', {'articles': articles})


def article_detail(request, slug):
    """Display a single article and handle comment submissions.
    
    Only approved articles are visible to the public. Unapproved articles can
    only be viewed by their author, editors, or superusers.
    
    Args:
        request: HTTP request object (POST to submit comments).
        slug (str): URL slug identifying the article.
    
    Returns:
        HttpResponse: Rendered article detail page with comments.
    
    Raises:
        Http404: If article is not approved and user lacks permission.
    """
    article = get_object_or_404(Article, slug=slug)
    if not article.approved:
        allowed = (
            request.user.is_authenticated and (
                request.user.is_superuser or
                request.user.role == 'editor' or
                article.author == request.user
            )
        )
        if not allowed:
            raise Http404()
    if request.method == 'POST':
        if not request.user.is_authenticated:
            return HttpResponseForbidden()
        comment_form = CommentForm(request.POST)
        if comment_form.is_valid():
            Comment.objects.create(
                article=article,
                author=request.user,
                content=comment_form.cleaned_data['content'],
            )
            messages.success(request, 'Your comment has been posted.')
            return redirect('article_detail', slug=article.slug)
    else:
        comment_form = CommentForm()
    share_url = request.build_absolute_uri()
    comments = article.comments.select_related('author').all()
    return render(request, 'newsapp/article_detail.html', {
        'article': article,
        'share_url': share_url,
        'comment_form': comment_form,
        'comments': comments,
    })


def category_articles(request, slug):
    """Display all approved articles in a specific category.
    
    Args:
        request: HTTP request object.
        slug (str): Category slug identifier.
    
    Returns:
        HttpResponse: Rendered category page with filtered articles.
    """
    category = get_object_or_404(Category, slug=slug)
    articles = category.articles.filter(approved=True).order_by('-created_at')
    return render(request, 'newsapp/category_articles.html', {'category': category, 'articles': articles})


@login_required
def staff_dashboard(request):
    """Display journalist/editor dashboard with their articles and pending approvals.
    
    Journalists see their own articles. Editors also see all pending articles
    awaiting approval.
    
    Args:
        request: HTTP request object.
    
    Returns:
        HttpResponse: Rendered staff dashboard or 403 if not authorized.
    """
    if not (request.user.is_superuser or request.user.role in ['editor', 'journalist']):
        return HttpResponseForbidden()

    your_articles = Article.objects.filter(author=request.user).order_by('-created_at')
    pending_articles = Article.objects.filter(approved=False).order_by('-created_at') if (request.user.is_superuser or request.user.role == 'editor') else Article.objects.none()

    return render(request, 'newsapp/staff_dashboard.html', {
        'your_articles': your_articles,
        'pending_articles': pending_articles,
    })


@login_required
def secret_admin(request):
    if not request.user.is_superuser:
        return HttpResponseForbidden()

    categories = Category.objects.all()
    if request.method == 'POST':
        cat_form = CategoryForm(request.POST, prefix='cat')
        role_form = UserRoleForm(request.POST, prefix='role')
        if 'create_category' in request.POST and cat_form.is_valid():
            Category.objects.create(
                name=cat_form.cleaned_data['name'],
                description=cat_form.cleaned_data['description'],
            )
            messages.success(request, 'Category created successfully.')
            return redirect('secret_admin')
        if 'change_role' in request.POST and role_form.is_valid():
            user = role_form.cleaned_data['user']
            user.role = role_form.cleaned_data['role']
            user.save()
            messages.success(request, f"Updated role for {user.username}.")
            return redirect('secret_admin')
    else:
        cat_form = CategoryForm(prefix='cat')
        role_form = UserRoleForm(prefix='role')

    return render(request, 'newsapp/secret_admin.html', {
        'categories': categories,
        'cat_form': cat_form,
        'role_form': role_form,
    })


def register_view(request):
    """Handle new user registration and role assignment.
    
    Creates a new user account with selected role and optional security question.
    
    Args:
        request: HTTP request object (POST to submit registration).
    
    Returns:
        HttpResponse: Rendered registration form or redirect to login on success.
    """
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.email = form.cleaned_data['email']
            user.save()
            messages.success(request, 'Account created successfully. Please log in.')
            return redirect('login')
    else:
        form = RegistrationForm()
    return render(request, 'newsapp/register.html', {'form': form})


def login_view(request):
    """Authenticate a user and start a login session.
    
    Args:
        request: HTTP request object (POST to submit credentials).
    
    Returns:
        HttpResponse: Rendered login form or redirect to home on success.
    """
    if request.method == 'POST':
        form = SignalDailyLoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('home')
    else:
        form = SignalDailyLoginForm(request)
    return render(request, 'newsapp/login.html', {'form': form})


@login_required
def logout_view(request):
    """Log out the current user and end their session.
    
    Args:
        request: HTTP request object.
    
    Returns:
        HttpResponse: Redirect to home page with logout confirmation.
    """
    logout(request)
    messages.success(request, 'You are logged out.')
    return redirect('home')


def password_reset_request(request):
    """Handle password reset request via security question.
    
    Validates email and checks if user has a security question configured.
    
    Args:
        request: HTTP request object (POST to submit email).
    
    Returns:
        HttpResponse: Rendered reset form or redirect to security question.
    """
    if request.method == 'POST':
        form = PasswordResetRequestForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            user = User.objects.filter(email=email).first()
            if user and user.security_question:
                request.session['reset_user'] = user.pk
                return redirect('security_question')
            messages.error(request, 'No user found for this email or no security question set.')
    else:
        form = PasswordResetRequestForm()
    return render(request, 'newsapp/password_reset_request.html', {'form': form})


def security_question(request):
    """Verify security answer and allow password reset.
    
    Retrieves user from session, verifies their security answer, and resets
    password if answer is correct.
    
    Args:
        request: HTTP request object (POST to submit answer and new password).
    
    Returns:
        HttpResponse: Rendered security question form or redirect on success.
    """
    user_pk = request.session.get('reset_user')
    if not user_pk:
        return redirect('password_reset_request')
    user = get_object_or_404(User, pk=user_pk)

    if request.method == 'POST':
        form = SecurityAnswerForm(request.POST)
        if form.is_valid():
            answer = form.cleaned_data['answer'].strip().lower()
            if user.security_answer and user.security_answer.strip().lower() == answer:
                user.set_password(form.cleaned_data['new_password1'])
                user.save()
                messages.success(request, 'Password reset successfully. Please log in.')
                return redirect('login')
            messages.error(request, 'Security answer is incorrect.')
    else:
        form = SecurityAnswerForm()

    return render(request, 'newsapp/security_question.html', {'form': form, 'question': user.security_question})


@login_required
def subscribe_publisher(request, pk):
    """Subscribe a reader to a publisher to receive article notifications.
    
    Only users with 'reader' role can subscribe to publishers.
    
    Args:
        request: HTTP request object.
        pk (int): Publisher primary key.
    
    Returns:
        HttpResponse: Redirect to article list with confirmation message.
    """
    publisher = get_object_or_404(Publisher, pk=pk)
    if request.user.role != 'reader':
        return HttpResponseForbidden()
    request.user.subscribed_publishers.add(publisher)
    messages.success(request, f'Subscribed to {publisher.name}.')
    return redirect('article_list')


@login_required
def subscribe_journalist(request, pk):
    """Subscribe a reader to a journalist to receive article notifications.
    
    Only users with 'reader' role can subscribe to journalists.
    
    Args:
        request: HTTP request object.
        pk (int): Journalist user primary key.
    
    Returns:
        HttpResponse: Redirect to article list with confirmation message.
    """
    journalist = get_object_or_404(User, pk=pk, role='journalist')
    if request.user.role != 'reader':
        return HttpResponseForbidden()
    request.user.subscribed_journalists.add(journalist)
    messages.success(request, f'Subscribed to {journalist.username}.')
    return redirect('article_list')


@login_required
def create_article(request):
    """Create an article and associate uploaded images with it.
    
    Journalists and editors can create articles. Journalists' articles require
    editor approval before publication. Uses formsets for multiple image uploads.
    
    Args:
        request: HTTP request object (POST to submit article).
    
    Returns:
        HttpResponse: Rendered article form or redirect to article/dashboard on success.
    """
    if not (request.user.is_superuser or request.user.role in ['journalist', 'editor']):
        return HttpResponseForbidden()

    if request.method == 'POST':
        new_article = Article(author=request.user)
        form = ArticleForm(request.POST, request.FILES, instance=new_article)
        formset = ArticleImageFormSet(request.POST, request.FILES, instance=new_article)
        if not (request.user.is_superuser or request.user.role == 'editor'):
            form.fields.pop('approved', None)
            form.fields.pop('featured', None)
            form.fields.pop('pinned', None)
        if form.is_valid() and formset.is_valid():
            with transaction.atomic():
                article = form.save(commit=False)
                article.author = request.user
                if request.user.role == 'journalist':
                    article.approved = False
                article.save()
                form.save_m2m()
                formset.save()
                if article.approved:
                    messages.success(request, 'Article created and published successfully.')
                    return redirect('article_detail', slug=article.slug)
                messages.success(request, 'Article submitted for editorial review.')
                return redirect('staff_dashboard')
        else:
            messages.error(request, 'Please fix the highlighted fields.')
    else:
        new_article = Article(author=request.user)
        form = ArticleForm(instance=new_article)
        formset = ArticleImageFormSet(instance=new_article)
        if not (request.user.is_superuser or request.user.role == 'editor'):
            form.fields.pop('approved', None)
            form.fields.pop('featured', None)
            form.fields.pop('pinned', None)

    return render(request, 'newsapp/article_form.html', {'form': form, 'formset': formset, 'title': 'Create Article'})


@login_required
def edit_article(request, slug):
    article = get_object_or_404(Article, slug=slug)
    if request.user.role == 'journalist' and article.author != request.user:
        return HttpResponseForbidden()
    if not (request.user.is_superuser or request.user.role in ['editor', 'journalist']):
        return HttpResponseForbidden()
    if request.method == 'POST':
        form = ArticleForm(request.POST, request.FILES, instance=article)
        formset = ArticleImageFormSet(request.POST, request.FILES, instance=article)
        if not (request.user.is_superuser or request.user.role == 'editor'):
            form.fields.pop('approved', None)
            form.fields.pop('featured', None)
            form.fields.pop('pinned', None)
        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            messages.success(request, 'Article updated successfully.')
            return redirect('article_detail', slug=article.slug)
    else:
        form = ArticleForm(instance=article)
        formset = ArticleImageFormSet(instance=article)
        if not (request.user.is_superuser or request.user.role == 'editor'):
            form.fields.pop('approved', None)
            form.fields.pop('featured', None)
            form.fields.pop('pinned', None)
    return render(request, 'newsapp/article_form.html', {'form': form, 'formset': formset, 'title': 'Edit Article'})


@login_required
def delete_article(request, slug):
    article = get_object_or_404(Article, slug=slug)
    if not (request.user.is_superuser or request.user.role in ['editor', 'journalist']):
        return HttpResponseForbidden()
    if request.user.role == 'journalist' and article.author != request.user:
        return HttpResponseForbidden()
    article.delete()
    messages.success(request, 'Article deleted successfully.')
    return redirect('article_list')


@login_required
def approve_article(request, slug):
    """Mark an article approved and trigger the approval signal workflow."""
    if not (request.user.is_superuser or request.user.role == 'editor'):
        return HttpResponseForbidden()
    article = get_object_or_404(Article, slug=slug)
    article.approved = True
    article.save()
    messages.success(request, 'Article approved and shared.')
    return redirect('article_detail', slug=article.slug)


@login_required
def pin_article(request, slug):
    """Toggle the pinned status of an article for the hero section."""
    if not (request.user.is_superuser or request.user.role == 'editor'):
        return HttpResponseForbidden()
    article = get_object_or_404(Article, slug=slug)
    article.pinned = not article.pinned
    article.save()
    action = 'pinned' if article.pinned else 'unpinned'
    messages.success(request, f'Article {action} for hero section.')
    return redirect('article_detail', slug=article.slug)


def newsletter_list(request):
    if not _is_editor(request.user):
        return HttpResponseForbidden()
    newsletters = Newsletter.objects.all().order_by('-created_at')
    subscribers = NewsletterSubscriber.objects.all()
    return render(request, 'newsapp/newsletter_list.html', {
        'newsletters': newsletters,
        'subscribers': subscribers,
    })


def newsletter_detail(request, pk):
    newsletter = get_object_or_404(Newsletter, pk=pk)
    return render(request, 'newsapp/newsletter_detail.html', {'newsletter': newsletter})


@login_required
def create_newsletter(request):
    if not (request.user.is_superuser or request.user.role in ['journalist', 'editor']):
        return HttpResponseForbidden()
    if request.method == 'POST':
        form = NewsletterForm(request.POST)
        if form.is_valid():
            newsletter = form.save(commit=False)
            newsletter.author = request.user
            newsletter.save()
            form.save_m2m()
            messages.success(request, 'Newsletter created successfully.')
            return redirect('newsletter_detail', pk=newsletter.pk)
    else:
        form = NewsletterForm()
    return render(request, 'newsapp/newsletter_form.html', {'form': form, 'title': 'Create Newsletter'})


@login_required
def edit_newsletter(request, pk):
    newsletter = get_object_or_404(Newsletter, pk=pk)
    if request.user.role == 'journalist' and newsletter.author != request.user:
        return HttpResponseForbidden()
    if not (request.user.is_superuser or request.user.role in ['journalist', 'editor']):
        return HttpResponseForbidden()
    if request.method == 'POST':
        form = NewsletterForm(request.POST, instance=newsletter)
        if form.is_valid():
            form.save()
            messages.success(request, 'Newsletter updated successfully.')
            return redirect('newsletter_detail', pk=newsletter.pk)
    else:
        form = NewsletterForm(instance=newsletter)
    return render(request, 'newsapp/newsletter_form.html', {'form': form, 'title': 'Edit Newsletter'})


@login_required
def delete_newsletter(request, pk):
    newsletter = get_object_or_404(Newsletter, pk=pk)
    if request.user.role == 'journalist' and newsletter.author != request.user:
        return HttpResponseForbidden()
    if not (request.user.is_superuser or request.user.role in ['journalist', 'editor']):
        return HttpResponseForbidden()
    newsletter.delete()
    messages.success(request, 'Newsletter deleted successfully.')
    return redirect('newsletter_list')


@login_required
def send_newsletter(request, pk):
    if not _is_editor(request.user):
        return HttpResponseForbidden()
    newsletter = get_object_or_404(Newsletter, pk=pk)
    recipients = list(NewsletterSubscriber.objects.values_list('email', flat=True))
    if recipients:
        subject = f'Signal Daily Newsletter: {newsletter.title}'
        newsletter_url = request.build_absolute_uri(reverse('newsletter_detail', kwargs={'pk': newsletter.pk}))
        html_message = f"""
            <html>
                <body style="font-family:Arial,sans-serif;color:#333;">
                    <div style="max-width:680px;margin:0 auto;padding:24px;">
                        <img src="{settings.SITE_URL}/media/logo.png" alt="Signal Daily" style="max-height:60px;display:block;margin-bottom:24px;" />
                        <h1 style="color:#1a1a1a;">Welcome from Signal Daily</h1>
                        <p style="font-size:16px;line-height:1.6;">{newsletter.description}</p>
                        <p style="font-size:16px;line-height:1.6;">Read the complete newsletter and discover featured stories below.</p>
                        <p><a href="{newsletter_url}" style="display:inline-block;padding:14px 24px;background:#222;color:#fff;text-decoration:none;border-radius:4px;">Read the Newsletter</a></p>
                        <hr style="margin:32px 0;border:none;border-top:1px solid #ddd;" />
                        <p style="font-size:14px;color:#777;">Thank you for following Signal Daily.</p>
                    </div>
                </body>
            </html>
        """
        send_mail(
            subject=subject,
            message=newsletter.description,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=recipients,
            html_message=html_message,
            fail_silently=True,
        )
        messages.success(request, 'Newsletter sent to all subscribers.')
    else:
        messages.info(request, 'No newsletter subscribers are currently signed up.')
    return redirect('newsletter_detail', pk=newsletter.pk)


@login_required
def publisher_list(request):
    if not _is_editor(request.user):
        return HttpResponseForbidden()
    publishers = Publisher.objects.all()
    return render(request, 'newsapp/publisher_list.html', {'publishers': publishers})


@login_required
def create_publisher(request):
    if not _is_editor(request.user):
        return HttpResponseForbidden()
    if request.method == 'POST':
        form = PublisherForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Publication created successfully.')
            return redirect('publisher_list')
    else:
        form = PublisherForm()
    return render(request, 'newsapp/publisher_form.html', {'form': form, 'title': 'Create Publication'})


@login_required
def edit_publisher(request, pk):
    if not _is_editor(request.user):
        return HttpResponseForbidden()
    publisher = get_object_or_404(Publisher, pk=pk)
    if request.method == 'POST':
        form = PublisherForm(request.POST, request.FILES, instance=publisher)
        if form.is_valid():
            form.save()
            messages.success(request, 'Publication updated successfully.')
            return redirect('publisher_list')
    else:
        form = PublisherForm(instance=publisher)
    return render(request, 'newsapp/publisher_form.html', {'form': form, 'title': 'Edit Publication'})


class CustomAuthToken(ObtainAuthToken):
    """Issue token authentication credentials for API users."""

        def post(self, request, *args, **kwargs):
        """Authenticate and return API token for the user.
        
        Args:
            request: HTTP request with username and password.
        
        Returns:
            Response: JSON with token, user_id, and role.
        """
        serializer = self.serializer_class(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token, _ = Token.objects.get_or_create(user=user)
        return Response({'token': token.key, 'user_id': user.pk, 'role': user.role})


class ArticleViewSet(viewsets.ModelViewSet):
    """REST API endpoint for CRUD operations on articles.
    
    Provides list, retrieve, create, update, and delete operations for articles.
    Only approved articles are visible in list/retrieve. Creation requires
    journalist role. Update/delete require editor or ownership.
    """
    queryset = Article.objects.all().select_related('author', 'publisher').prefetch_related('images')
    serializer_class = ArticleSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get_permissions(self):
        """Return appropriate permission classes based on the action.
        
        Returns:
            list: Permission class instances for the current action.
        """
        if self.action == 'create':
            permission_classes = [permissions.IsAuthenticated, IsJournalist]
        elif self.action in ['update', 'partial_update', 'destroy']:
            permission_classes = [permissions.IsAuthenticated, IsEditorOrJournalist]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]

        def get_queryset(self):
        """Filter articles based on action - only approved for list/retrieve.
        
        Returns:
            QuerySet: Filtered article queryset.
        """
        queryset = super().get_queryset()
        if self.action in ['list', 'retrieve']:
            return queryset.filter(approved=True)
        return queryset

        def perform_create(self, serializer):
        """Set author and approval status when creating articles via API.
        
        Args:
            serializer: Validated article serializer.
        """
        article = serializer.save(author=self.request.user)
        if self.request.user.role == 'journalist':
            article.approved = False
            article.save()


class PublisherViewSet(viewsets.ReadOnlyModelViewSet):
    """REST API endpoint for publications."""
    queryset = Publisher.objects.all()
    serializer_class = PublisherSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]


class JournalistViewSet(viewsets.ReadOnlyModelViewSet):
    """REST API endpoint for registered journalists."""
    queryset = User.objects.filter(role=User.ROLE_JOURNALIST)
    serializer_class = UserSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]


class NewsletterSubscriberViewSet(viewsets.ReadOnlyModelViewSet):
    """REST API endpoint for newsletter email subscribers."""
    queryset = NewsletterSubscriber.objects.all()
    serializer_class = NewsletterSubscriberSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]


class SubscribedArticleListAPIView(generics.ListAPIView):
    """Return articles for the requesting reader's subscriptions.
    
    Filters approved articles to only those from publishers or journalists
    the reader has subscribed to.
    """
    serializer_class = ArticleSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

        def get_queryset(self):
        """Return articles from user's subscriptions.
        
        Returns:
            QuerySet: Approved articles from subscribed publishers/journalists.
        """
        user = self.request.user
        if user.role != 'reader':
            return Article.objects.filter(approved=True)
        publisher_ids = user.subscribed_publishers.values_list('pk', flat=True)
        journalist_ids = user.subscribed_journalists.values_list('pk', flat=True)
        return Article.objects.filter(approved=True).filter(
            Q(publisher_id__in=publisher_ids) | Q(author_id__in=journalist_ids)
        ).distinct()


class ApprovedLogAPIView(APIView):
    """Receive approved article logs from internal signal callbacks."""
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        """Log article approval data sent from signal handlers.
        
        Args:
            request: HTTP POST request with article approval data.
        
        Returns:
            Response: JSON confirmation message.
        """
        return Response({'status': 'approved payload received', 'payload': request.data}, status=status.HTTP_200_OK)
