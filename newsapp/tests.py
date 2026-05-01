"""Automated unit tests for the Signal Daily news API and security flows."""

from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from .models import Article, Newsletter, NewsletterSubscriber, Publisher

User = get_user_model()


class NewsAppApiTests(TestCase):
    """Test the API, subscription behavior, approval flow, and security reset."""

    def setUp(self):
        self.reader = User.objects.create_user(
            username='reader1', email='reader@example.com', password='readerpass', role='reader', security_question='City?', security_answer='Paris'
        )
        self.journalist = User.objects.create_user(
            username='writer1', email='writer@example.com', password='writerpass', role='journalist', security_question='Pet?', security_answer='Fluffy'
        )
        self.editor = User.objects.create_user(
            username='editor1', email='editor@example.com', password='editorpass', role='editor')
        self.publisher = Publisher.objects.create(name='Rolling Digital', description='A technology publisher')
        self.article_public = Article.objects.create(
            title='Publisher announcement', summary='A publisher story.', content='Publisher content', author=self.editor, publisher=self.publisher, approved=True
        )
        self.article_independent = Article.objects.create(
            title='Journalist insight', summary='A deep dive.', content='Journalist content', author=self.journalist, approved=True
        )
        self.newsletter = Newsletter.objects.create(title='Weekly Beat', description='Curated stories', author=self.journalist)
        self.newsletter.articles.add(self.article_public)
        self.reader.subscribed_journalists.add(self.journalist)
        self.reader.subscribed_publishers.add(self.publisher)

        for user in [self.reader, self.journalist, self.editor]:
            Token.objects.create(user=user)

        self.client = APIClient()

    def test_reader_can_retrieve_subscribed_articles(self):
        token = Token.objects.get(user=self.reader)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')
        url = reverse('api-articles-subscribed')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        titles = [item['title'] for item in response.json()]
        self.assertIn(self.article_public.title, titles)
        self.assertIn(self.article_independent.title, titles)

    def test_journalist_can_create_article(self):
        token = Token.objects.get(user=self.journalist)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')
        url = reverse('article-list')
        response = self.client.post(url, {'title': 'New Story', 'summary': 'A new story', 'content': 'Content...'})
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['author']['username'], self.journalist.username)

    def test_editor_can_approve_and_delete_article(self):
        token = Token.objects.get(user=self.editor)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')
        article = Article.objects.create(title='Pending', content='Pending content', author=self.journalist)
        url = reverse('article-detail', kwargs={'pk': article.pk})
        response = self.client.put(url, {'title': 'Pending', 'summary': '', 'content': 'Updated'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['title'], 'Pending')
        delete_response = self.client.delete(url)
        self.assertEqual(delete_response.status_code, 204)

    def test_newsletter_api_represents_articles(self):
        self.assertEqual(self.newsletter.articles.count(), 1)
        self.assertEqual(self.newsletter.author, self.journalist)

    @patch('newsapp.signals.send_mail')
    @patch('newsapp.signals.requests.post')
    def test_signal_approval_logs_and_emails(self, mock_post, mock_send):
        article = Article.objects.create(title='Approval test', content='Test', author=self.journalist)
        article.approved = True
        article.save()
        mock_send.assert_called()
        mock_post.assert_called()

    def test_password_reset_requires_security_answer(self):
        response = self.client.post(reverse('password_reset_request'), {'email': self.reader.email})
        self.assertEqual(response.status_code, 302)
        session_key = self.client.session.get('reset_user')
        self.assertIsNotNone(session_key)

    def test_newsletter_signup_stores_subscriber_email(self):
        response = self.client.post(reverse('newsletter_signup'), {'email': 'newreader@example.com'})
        self.assertEqual(response.status_code, 302)
        self.assertTrue(NewsletterSubscriber.objects.filter(email='newreader@example.com').exists())

    def test_api_publications_endpoint_returns_data(self):
        token = Token.objects.get(user=self.reader)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')
        response = self.client.get('/api/publications/')
        self.assertEqual(response.status_code, 200)
        self.assertGreaterEqual(len(response.json()), 1)

    def test_api_subscribers_endpoint_returns_data(self):
        NewsletterSubscriber.objects.create(email='apiuser@example.com')
        token = Token.objects.get(user=self.reader)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')
        response = self.client.get('/api/subscribers/')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(any(item['email'] == 'apiuser@example.com' for item in response.json()))
