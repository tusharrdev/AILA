from django.core.mail import send_mail
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

def send_answer_notification(question, answer):
    """Send email notification when a lawyer answers a question"""
    
    subject = f"Your legal question has been answered - {question.area_of_law}"
    
    # HTML email template
    html_message = f"""
    <html>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
        <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
            <h2 style="color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px;">
                Your Legal Question Has Been Answered
            </h2>
            
            <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0;">
                <h3 style="color: #2c3e50; margin-top: 0;">Your Question:</h3>
                <p style="font-style: italic; color: #666;">"{question.question_text}"</p>
                <p><strong>Area of Law:</strong> {question.area_of_law}</p>
            </div>
            
            <div style="background-color: #e8f5e8; padding: 15px; border-radius: 5px; margin: 20px 0;">
                <h3 style="color: #27ae60; margin-top: 0;">Answer by {answer.lawyer.full_name}:</h3>
                <p>{answer.answer_text}</p>
            </div>
            
            <div style="margin-top: 30px; padding: 15px; background-color: #f1f2f6; border-radius: 5px;">
                <p><strong>Answered on:</strong> {answer.created_at.strftime('%B %d, %Y at %I:%M %p')}</p>
                <p style="font-size: 12px; color: #666; margin-top: 15px;">
                    <em>Disclaimer: This answer is for informational purposes only and does not constitute legal advice. 
                    Please consult with a qualified attorney for specific legal guidance.</em>
                </p>
            </div>
            
            <div style="text-align: center; margin-top: 30px;">
                <p style="color: #7f8c8d;">Thank you for using AILA Legal Services</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    # Plain text version
    plain_message = f"""
Your Legal Question Has Been Answered

Your Question: "{question.question_text}"
Area of Law: {question.area_of_law}

Answer by {answer.lawyer.full_name}:
{answer.answer_text}

Answered on: {answer.created_at.strftime('%B %d, %Y at %I:%M %p')}

Disclaimer: This answer is for informational purposes only and does not constitute legal advice. Please consult with a qualified attorney for specific legal guidance.

Thank you for using AILA Legal Services
    """
    
    try:
        result = send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[question.email],
            html_message=html_message,
            fail_silently=False,
        )
        
        if result:
            logger.info(f"Email sent successfully to {question.email}")
            return True
        else:
            logger.warning(f"Email sending returned 0 for {question.email}")
            return False
            
    except Exception as e:
        logger.error(f"Failed to send email to {question.email}: {str(e)}")
        print(f"Email Error Details: {str(e)}")
        return False