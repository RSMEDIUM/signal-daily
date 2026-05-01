"""URL patterns for the Signal Daily frontend and API endpoints."""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register(r'articles', views.ArticleViewSet, basename='article')
router.register(r'publications', views.PublisherViewSet, basename='publication')
router.register(r'journalists', views.JournalistViewSet, basename='journalist')
router.register(r'subscribers', views.NewsletterSubscriberViewSet, basename='subscriber')

urlpatterns = [
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('articles/', views.article_list, name='article_list'),
    path('articles/create/', views.create_article, name='create_article'),
    path('articles/<slug:slug>/', views.article_detail, name='article_detail'),
    path('articles/<slug:slug>/edit/', views.edit_article, name='edit_article'),
    path('articles/<slug:slug>/delete/', views.delete_article, name='delete_article'),
    path('articles/<slug:slug>/approve/', views.approve_article, name='approve_article'),
    path('articles/<slug:slug>/pin/', views.pin_article, name='pin_article'),
    path('newsletters/', views.newsletter_list, name='newsletter_list'),
    path('newsletters/create/', views.create_newsletter, name='create_newsletter'),
    path('newsletters/<int:pk>/', views.newsletter_detail, name='newsletter_detail'),
    path('newsletters/<int:pk>/edit/', views.edit_newsletter, name='edit_newsletter'),
    path('newsletters/<int:pk>/delete/', views.delete_newsletter, name='delete_newsletter'),
    path('newsletters/<int:pk>/send/', views.send_newsletter, name='send_newsletter'),
    path('newsletter/signup/', views.newsletter_signup, name='newsletter_signup'),
    path('publications/', views.publisher_list, name='publisher_list'),
    path('publications/create/', views.create_publisher, name='create_publisher'),
    path('publications/<int:pk>/edit/', views.edit_publisher, name='edit_publisher'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('password-reset/', views.password_reset_request, name='password_reset_request'),
    path('security-question/', views.security_question, name='security_question'),
    path('subscribe/publisher/<int:pk>/', views.subscribe_publisher, name='subscribe_publisher'),
    path('subscribe/journalist/<int:pk>/', views.subscribe_journalist, name='subscribe_journalist'),
    path('categories/<slug:slug>/', views.category_articles, name='category_articles'),
    path('staff/', views.staff_dashboard, name='staff_dashboard'),
    path('secret-admin/', views.secret_admin, name='secret_admin'),
    path('api/approved/', views.ApprovedLogAPIView.as_view(), name='api-approved'),
    path('api/token/', views.CustomAuthToken.as_view(), name='api_token_auth'),
    path('api/articles/subscribed/', views.SubscribedArticleListAPIView.as_view(), name='api-articles-subscribed'),
    path('api/', include(router.urls)),
]
