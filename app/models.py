from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.conf import settings
import json

# Remove this line - it's causing the circular import
# User = get_user_model()


class CustomUserManager(BaseUserManager):
    def create_user(self, email, full_name, password=None):
        if not email:
            raise ValueError('Users must have an email address')
        user = self.model(email=self.normalize_email(email), full_name=full_name)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, full_name, password=None):
        user = self.create_user(email, full_name, password)
        user.is_superuser = True
        user.is_staff = True
        user.role = 'admin'
        user.save(using=self._db)
        return user


class CustomUser(AbstractBaseUser, PermissionsMixin):
    ROLE_CHOICES = (
        ('user', 'User'),
        ('lawyer', 'Lawyer'),
        ('admin', 'Admin'),
    )

    email = models.EmailField(unique=True)
    full_name = models.CharField(max_length=255)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='user')
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    
    otp = models.CharField(max_length=6, blank=True, null=True)

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['full_name']

    def __str__(self):
        return self.email

class LawyerProfile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    phone = models.CharField(max_length=15)
    city = models.CharField(max_length=50)
    experience = models.PositiveIntegerField()
    language = models.TextField(null=True, blank=True)
    practice_area = models.TextField(null=True, blank=True)
    enrollment_number = models.CharField(max_length=50)
    photo = models.ImageField(upload_to='lawyer_photos/')
    is_approved = models.BooleanField(default=False)

    def __str__(self):
        return self.user.full_name

class Hire(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='hires')
    lawyer = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='hired_by')
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.full_name} hired {self.lawyer.full_name}"

class Message(models.Model):
    sender = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='sent_messages')
    receiver = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='received_messages')
    content = models.TextField(blank=True)
    file = models.FileField(upload_to='chat_files/', null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    deleted_by_sender = models.BooleanField(default=False)
    deleted_by_receiver = models.BooleanField(default=False)
    is_read = models.BooleanField(default=False)
    
    def __str__(self):
        return f"From {self.sender.full_name} to {self.receiver.full_name}"
    
class LawyerReview(models.Model):
    lawyer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="lawyer_reviews")
    reviewer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="reviewer_reviews")

    review = models.TextField()
    rating = models.IntegerField()  # 1 to 5
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Review for {self.lawyer} by {self.reviewer}"

class Question(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='questions',
        null=True,  
        blank=True  
    )
    name = models.CharField(max_length=100)
    email = models.EmailField()
    area_of_law = models.CharField(max_length=100)
    question_text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_answered = models.BooleanField(default=False) 

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.area_of_law} - {self.question_text[:50]}"
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.is_answered = self.answers.exists()
        if 'update_fields' not in kwargs:
            super().save(update_fields=['is_answered'])

class Answer(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='answers')
    lawyer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='answers')
    answer_text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"Answer by {self.lawyer.full_name} to question {self.question.id}"
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.question.is_answered = True
        self.question.save(update_fields=['is_answered'])

class Blog(models.Model):
    lawyer = models.ForeignKey(CustomUser, on_delete=models.CASCADE, limit_choices_to={'role': 'lawyer'})
    title = models.CharField(max_length=200)
    content = models.TextField()
    image = models.ImageField(upload_to='blog_images/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

class Case(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    lawyer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='cases_as_lawyer'
    )
    case_name = models.CharField(max_length=255)
    client_name = models.CharField(max_length=255, blank=True, null=True)
    description = models.TextField()
    status = models.CharField(max_length=50, choices=[
        ("Reviewing", "Reviewing"),
        ("Filed", "Filed"),
        ("In Court", "In Court"),
        ("Closed", "Closed"),
    ])
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.case_name} ({self.status})"
        
class CaseDocument(models.Model):
    case = models.ForeignKey(Case, on_delete=models.CASCADE, related_name='documents')
    document = models.FileField(upload_to='case_documents/')
    document_name = models.CharField(max_length=255)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.document_name} - {self.case.case_name}"

class AvailableSlot(models.Model):
    lawyer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()

class Appointment(models.Model):
    slot = models.ForeignKey(AvailableSlot, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)  
    booked_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        user_name = self.user.full_name if self.user else "Unknown User"
        return f"Appointment for {self.slot} by {user_name}"
    
class UploadedDocument(models.Model):
    """Model to track uploaded documents for analysis"""
    # Changed from User to settings.AUTH_USER_MODEL for consistency
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='uploaded_documents')
    original_filename = models.CharField(max_length=255)
    file_size = models.PositiveIntegerField()  # Size in bytes
    file_type = models.CharField(max_length=10)  # pdf, docx, etc.
    upload_date = models.DateTimeField(auto_now_add=True)
    session_key = models.CharField(max_length=40)
    is_processed = models.BooleanField(default=False)
    processing_error = models.TextField(blank=True, null=True)
    
    class Meta:
        ordering = ['-upload_date']
    
    def __str__(self):
        return f"{self.original_filename} - {self.user.email}"

class GeneratedDocument(models.Model):
    """Model to track generated legal documents"""
    DOCUMENT_TYPES = [
        ('contract', 'Contract'),
        ('lease', 'Lease Agreement'),
        ('nda', 'Non-Disclosure Agreement'),
        ('power_of_attorney', 'Power of Attorney'),
        ('legal_notice', 'Legal Notice'),
        ('will', 'Will/Testament'),
    ]
    
    # Changed from User to settings.AUTH_USER_MODEL for consistency
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='generated_documents')
    document_type = models.CharField(max_length=20, choices=DOCUMENT_TYPES)
    document_id = models.CharField(max_length=100, unique=True)  
    answers_json = models.TextField()  
    file_path = models.CharField(max_length=500)
    created_at = models.DateTimeField(auto_now_add=True)
    downloaded_at = models.DateTimeField(null=True, blank=True)
    download_count = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)  
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.get_document_type_display()} - {self.user.email}"
    
    @property
    def answers(self):
        """Return parsed answers as dictionary"""
        try:
            return json.loads(self.answers_json)
        except json.JSONDecodeError:
            return {}
    
    def set_answers(self, answers_dict):
        """Set answers from dictionary"""
        self.answers_json = json.dumps(answers_dict)

class ChatSession(models.Model):
    """Model to track chat sessions and history"""
    # Changed from User to settings.AUTH_USER_MODEL for consistency
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='chat_sessions', null=True, blank=True)
    session_key = models.CharField(max_length=40)
    mode = models.CharField(max_length=20, default='general')  
    created_at = models.DateTimeField(auto_now_add=True)
    last_activity = models.DateTimeField(auto_now=True)
    uploaded_document = models.ForeignKey(UploadedDocument, on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        ordering = ['-last_activity']
    
    def __str__(self):
        user_info = self.user.email if self.user else f"Anonymous ({self.session_key[:8]})"
        return f"Chat Session - {user_info}"

class ChatMessage(models.Model):
    """Model to store individual chat messages"""
    MESSAGE_TYPES = [
        ('user', 'User'),
        ('bot', 'Bot'),
        ('system', 'System'),
    ]
    
    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name='messages')
    message_type = models.CharField(max_length=10, choices=MESSAGE_TYPES)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['timestamp']
    
    def __str__(self):
        return f"{self.get_message_type_display()}: {self.content[:50]}..."

class DocumentTemplate(models.Model):
    """Model for storing document templates"""
    name = models.CharField(max_length=100)
    document_type = models.CharField(max_length=20)
    template_content = models.TextField() 
    # Changed from User to settings.AUTH_USER_MODEL for consistency
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, limit_choices_to={'role': 'admin'})
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.document_type})"

class DocumentDownloadLog(models.Model):
    """Model to track document downloads"""
    document = models.ForeignKey(GeneratedDocument, on_delete=models.CASCADE, related_name='download_logs')
    # Changed from User to settings.AUTH_USER_MODEL for consistency
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    downloaded_at = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    
    def __str__(self):
        return f"Download: {self.document.document_type} by {self.user.email}"

class Feedback(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE,
        null=True,  
        blank=True
    )
    subject = models.CharField(max_length=255)
    message = models.TextField()
    submitted_at = models.DateTimeField(auto_now_add=True)
    anonymous_name = models.CharField(max_length=100, null=True, blank=True)
    anonymous_email = models.EmailField(null=True, blank=True)
    user_type = models.CharField(
        max_length=20, 
        choices=[
            ('lawyer', 'Lawyer'),
            ('visitor', 'Visitor'),  
        ],
        default='visitor'
    )

    def __str__(self):
        if self.user:
            return f"Feedback from {self.user.email} (Lawyer) on {self.submitted_at}"
        else:
            return f"Anonymous feedback from {self.anonymous_name or 'Unknown'} (Visitor) on {self.submitted_at}"

    @property
    def feedback_author(self):
        """Return the author name for display purposes"""
        if self.user:
            return self.user.full_name or self.user.email
        elif self.anonymous_name:
            return self.anonymous_name
        else:
            return "Anonymous Visitor"

    @property
    def author_email(self):
        """Return the author email for display purposes"""
        if self.user:
            return self.user.email
        elif self.anonymous_email:
            return self.anonymous_email
        else:
            return "No email provided"
        
    @property
    def is_from_lawyer(self):
        """Check if feedback is from a lawyer"""
        return self.user is not None and self.user_type == 'lawyer'