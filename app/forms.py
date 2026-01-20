from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser, LawyerProfile

class UserSignupForm(UserCreationForm):
    full_name = forms.CharField()
    email = forms.EmailField()

    class Meta:
        model = CustomUser
        fields = ['full_name', 'email', 'password1', 'password2']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = 'user'
        if commit:
            user.save()
        return user

class LawyerSignupForm(UserCreationForm):
    full_name = forms.CharField()
    email = forms.EmailField()
    phone = forms.CharField()
    city = forms.CharField()
    experience = forms.IntegerField()
    language = forms.CharField()
    practice_area = forms.CharField()
    enrollment_number = forms.CharField()
    image = forms.ImageField()

    class Meta:
        model = CustomUser
        fields = ['full_name', 'email', 'password1', 'password2']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = 'lawyer'
        if commit:
            user.save()
            profile = LawyerProfile.objects.create(
                user=user,
                phone=self.cleaned_data['phone'],
                city=self.cleaned_data['city'],
                experience=self.cleaned_data['experience'],
                language=self.cleaned_data['language'],
                practice_area=self.cleaned_data['practice_area'],
                enrollment_number=self.cleaned_data['enrollment_number'],
                photo=self.cleaned_data['image'],
            )
        return user

class LoginForm(forms.Form):
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput)

from django import forms
from .models import Question

class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = ['question_text', 'area_of_law']  

from django import forms
from django.utils import timezone

class SlotForm(forms.Form):
    new_slot_start = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        label="Start Time"
    )
    new_slot_end = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        label="End Time"
    )
    
    def clean(self):
        cleaned_data = super().clean()
        start = cleaned_data.get('new_slot_start')
        end = cleaned_data.get('new_slot_end')
        
        if start and end:
            if start >= end:
                raise forms.ValidationError("End time must be after start time.")
            
            if start <= timezone.now():
                raise forms.ValidationError("Start time must be in the future.")
             
            duration = end - start
            if duration.total_seconds() < 900:  
                raise forms.ValidationError("Slot must be at least 15 minutes long.")
        
        return cleaned_data

class AppointmentForm(forms.Form):
    appointment_datetime = forms.DateTimeField(widget=forms.DateTimeInput(attrs={'type': 'datetime-local'}))

from django import forms
from .models import LawyerProfile

class LawyerProfileEditForm(forms.ModelForm):
    class Meta:
        model = LawyerProfile
        fields = ['phone', 'city', 'photo', 'experience', 'language', 'practice_area']

from django import forms
from .models import Feedback

class FeedbackForm(forms.ModelForm):
    anonymous_name = forms.CharField(
        max_length=100,
        required=False, 
        widget=forms.TextInput(attrs={
            'placeholder': 'Your name (optional)',
            'class': 'form-input'
        })
    )
    
    anonymous_email = forms.EmailField(
        required=False, 
        widget=forms.EmailInput(attrs={
            'placeholder': 'Your email address (optional)',
            'class': 'form-input'
        })
    )
    
    user_type = forms.ChoiceField(
        choices=[
            ('visitor', 'Visitor'),
            ('lawyer', 'Lawyer'),
        ],
        required=False,
        initial='visitor',
        widget=forms.HiddenInput()
    )

    class Meta:
        model = Feedback
        fields = ['subject', 'message', 'anonymous_name', 'anonymous_email', 'user_type']
        widgets = {
            'subject': forms.TextInput(attrs={
                'placeholder': 'Enter feedback subject',
                'class': 'form-input',
                'required': True
            }),
            'message': forms.Textarea(attrs={
                'placeholder': 'Share your feedback, suggestions, or report issues...',
                'class': 'form-textarea',
                'rows': 5,
                'required': True
            }),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        self.fields['user_type'].widget = forms.HiddenInput()
        
        if (self.user and self.user.is_authenticated and 
            hasattr(self.user, 'role') and self.user.role == 'lawyer'):
            self.fields['anonymous_name'].widget = forms.HiddenInput()
            self.fields['anonymous_email'].widget = forms.HiddenInput()
            self.fields['anonymous_name'].required = False
            self.fields['anonymous_email'].required = False
        else:
            self.fields['anonymous_name'].required = False
            self.fields['anonymous_email'].required = False

    def clean(self):
        cleaned_data = super().clean()
        if (self.user and self.user.is_authenticated and 
            hasattr(self.user, 'role') and self.user.role == 'lawyer'):
            cleaned_data['user_type'] = 'lawyer'
            cleaned_data['anonymous_name'] = ''
            cleaned_data['anonymous_email'] = ''
        else:
            cleaned_data['user_type'] = 'visitor'
            if not cleaned_data.get('anonymous_name', '').strip():
                cleaned_data['anonymous_name'] = 'Anonymous Visitor'
        
        return cleaned_data

from django import forms
from .models import Question

class QuestionForm(forms.ModelForm):
    AREA_CHOICES = [
        ('Civil Law', 'Civil Law'),
        ('Criminal Law', 'Criminal Law'),
        ('Corporate Law', 'Corporate Law'),
        ('Family Law', 'Family Law'),
        ('Property Law', 'Property Law'),
        ('Employment Law', 'Employment Law'),
        ('Tax Law', 'Tax Law'),
        ('Immigration Law', 'Immigration Law'),
        ('Intellectual Property', 'Intellectual Property'),
        ('Constitutional Law', 'Constitutional Law'),
        ('Consumer Protection', 'Consumer Protection'),
        ('Other', 'Other'),
    ]
    
    name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'placeholder': 'Enter your full name',
            'class': 'form-control'
        }),
        help_text='Your name will be visible publicly with your question'
    )
    
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'placeholder': 'Enter your email address',
            'class': 'form-control'
        }),
        help_text='Email will be used for notifications only and will not be displayed publicly'
    )
    
    area_of_law = forms.ChoiceField(
        choices=AREA_CHOICES,
        widget=forms.Select(attrs={
            'class': 'form-control'
        }),
        help_text='Select the most relevant area of law for your question'
    )
    
    question_text = forms.CharField(
        widget=forms.Textarea(attrs={
            'placeholder': 'Describe your legal question in detail...',
            'class': 'form-control',
            'rows': 5
        }),
        help_text='Please provide as much relevant detail as possible for a comprehensive answer'
    )
    
    class Meta:
        model = Question
        fields = ['name', 'email', 'area_of_law', 'question_text']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs.update({
                'required': True,
                'autocomplete': 'off'
            })
            field.label = f"{field.label} *"