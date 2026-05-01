"""Forms for authentication, article publishing, and newsletter creation."""

from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm, UsernameField
from django.forms import inlineformset_factory

from .models import Article, ArticleImage, Newsletter, Publisher, Category

User = get_user_model()


class SignalDailyLoginForm(AuthenticationForm):
    """Custom login form for Signal Daily users."""

    username = UsernameField(widget=forms.TextInput(attrs={'autofocus': True, 'class': 'form-input'}))
    password = forms.CharField(label='Password', strip=False, widget=forms.PasswordInput(attrs={'class': 'form-input'}))


class RegistrationForm(UserCreationForm):
    """User registration form with role and security question fields."""

    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'class': 'form-input'}))
    role = forms.ChoiceField(choices=User.ROLE_CHOICES, widget=forms.Select(attrs={'class': 'form-input'}))
    security_question = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-input'}))
    security_answer = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-input'}))

    class Meta:
        model = User
        fields = ['username', 'email', 'role', 'security_question', 'security_answer', 'password1', 'password2']

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')
        if password1 and password2 and password1 != password2:
            self.add_error('password2', 'Passwords do not match.')
        return cleaned_data


class ArticleForm(forms.ModelForm):
    """Form for creating and editing news articles."""

    class Meta:
        model = Article
        fields = ['title', 'summary', 'content', 'publisher', 'categories', 'approved', 'featured', 'pinned']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-input'}),
            'summary': forms.Textarea(attrs={'class': 'form-input', 'rows': 2}),
            'content': forms.Textarea(attrs={'class': 'form-input editor-textarea'}),
            'publisher': forms.Select(attrs={'class': 'form-input'}),
            'categories': forms.SelectMultiple(attrs={'class': 'form-input'}),
            'approved': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
            'featured': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
            'pinned': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
        }


class ArticleImageForm(forms.ModelForm):
    """Form for uploading and describing an article image."""

    class Meta:
        model = ArticleImage
        fields = ['image', 'caption']
        widgets = {
            'caption': forms.TextInput(attrs={'class': 'form-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make image not required for extra forms in formsets
        if not self.instance.pk:
            self.fields['image'].required = False
            self.fields['caption'].required = False


ArticleImageFormSet = inlineformset_factory(
    Article,
    ArticleImage,
    form=ArticleImageForm,
    fields=['image', 'caption'],
    extra=3,
    can_delete=True,
)


class NewsletterForm(forms.ModelForm):
    """Form for creating and updating newsletters."""

    class Meta:
        model = Newsletter
        fields = ['title', 'description', 'articles']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-input'}),
            'description': forms.Textarea(attrs={'class': 'form-input', 'rows': 4}),
            'articles': forms.SelectMultiple(attrs={'class': 'form-input'}),
        }


class NewsletterSignupForm(forms.Form):
    """Collects an email address for the homepage newsletter signup."""

    email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-input', 'placeholder': 'Enter your email'}))


class PublisherForm(forms.ModelForm):
    """Editor form for creating and editing publisher profiles."""

    class Meta:
        model = Publisher
        fields = ['name', 'description', 'logo', 'editors', 'journalists']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-input'}),
            'description': forms.Textarea(attrs={'class': 'form-input', 'rows': 3}),
            'editors': forms.SelectMultiple(attrs={'class': 'form-input'}),
            'journalists': forms.SelectMultiple(attrs={'class': 'form-input'}),
        }


class CommentForm(forms.Form):
    """Collects a comment for an article."""

    content = forms.CharField(
        label='Comment',
        widget=forms.Textarea(attrs={'class': 'form-input', 'rows': 4, 'placeholder': 'Write your comment here...'}),
    )


class CategoryForm(forms.Form):
    """Allow superusers to create new article categories."""

    name = forms.CharField(label='Category name', max_length=100, widget=forms.TextInput(attrs={'class': 'form-input'}))
    description = forms.CharField(label='Description', required=False, widget=forms.Textarea(attrs={'class': 'form-input', 'rows': 3}))


class UserRoleForm(forms.Form):
    """Allow superusers to update a user's role from the hidden admin panel."""

    user = forms.ModelChoiceField(queryset=User.objects.all(), widget=forms.Select(attrs={'class': 'form-input'}))
    role = forms.ChoiceField(choices=User.ROLE_CHOICES, widget=forms.Select(attrs={'class': 'form-input'}))


class PasswordResetRequestForm(forms.Form):
    """Collects an email address for password reset flow."""

    email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-input'}))


class SecurityAnswerForm(forms.Form):
    """Verifies the user's security answer and accepts a new password."""

    answer = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-input'}))
    new_password1 = forms.CharField(label='New password', widget=forms.PasswordInput(attrs={'class': 'form-input'}))
    new_password2 = forms.CharField(label='Confirm new password', widget=forms.PasswordInput(attrs={'class': 'form-input'}))

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get('new_password1') != cleaned_data.get('new_password2'):
            self.add_error('new_password2', 'Passwords do not match.')
        return cleaned_data
