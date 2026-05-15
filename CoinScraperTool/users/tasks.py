from celery import shared_task
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings


# ✅ Sending emails asynchronously
@shared_task
def send_welcome_email(user_email, username):
    subject = "Welcome to Coinlytics"
    from_email = settings.EMAIL_HOST_USER
    recipient_list = [user_email]

    # rendering the template with context
    html_content = render_to_string(
        "emails/welcome_email.html", {"username": username})

    # fallback text when html is not rendered
    text_context = f"Hi {username}, \n\nThanks for signing up with CoinScraper!"

    # building the mail
    msg = EmailMultiAlternatives(
        subject, text_context, from_email, recipient_list)
    msg.attach_alternative(html_content, "text/html")
    msg.send()


# ✅ sending reset passwords emails asynchronously
# BUG FIX: Missing @shared_task decorator. Without it, calling
# send_password_reset_email.delay(...) raises AttributeError because plain
# Python functions have no .delay() or .apply_async() methods — those are
# added by Celery when the decorator registers the function as a task.
# The function was therefore always running synchronously (blocking the
# Django request/response cycle) or crashing outright when .delay() was used.
@shared_task
def send_password_reset_email(user_email, reset_link, username):
    subject = "Password Reset Request 🔑"
    from_email = settings.EMAIL_HOST_USER
    recipient_list = [user_email]

    html_content = render_to_string(
        "emails/password_reset.html", {"username": username,
                                       "reset_link": reset_link}
    )

    text_content = f"Hi {username},\nClick here to reset your password: {reset_link}"

    msg = EmailMultiAlternatives(
        subject, text_content, from_email, recipient_list)
    msg.attach_alternative(html_content, "text/html")
    msg.send()
