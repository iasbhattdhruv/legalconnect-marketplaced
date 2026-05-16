import os

from django.contrib.auth.models import User
from django.utils.text import slugify

from .models import BlogPost


LAWYERS = [
    {
        'username': 'criminal_lawyer',
        'email': 'criminal@example.com',
        'first_name': 'Aarav',
        'last_name': 'Mehta',
        'specialization': 'Criminal Law',
        'experience': 8,
        'consultation_fee': 1500,
        'bio': 'Criminal defense, bail matters, FIR guidance, and court representation.',
    },
    {
        'username': 'family_lawyer',
        'email': 'family@example.com',
        'first_name': 'Nisha',
        'last_name': 'Rao',
        'specialization': 'Family Law',
        'experience': 6,
        'consultation_fee': 1200,
        'bio': 'Divorce, custody, maintenance, mediation, and family settlement matters.',
    },
    {
        'username': 'corporate_lawyer',
        'email': 'corporate@example.com',
        'first_name': 'Kabir',
        'last_name': 'Shah',
        'specialization': 'Corporate Law',
        'experience': 10,
        'consultation_fee': 2500,
        'bio': 'Company registration, contracts, compliance, startup, and business disputes.',
    },
    {
        'username': 'property_lawyer',
        'email': 'property@example.com',
        'first_name': 'Priya',
        'last_name': 'Iyer',
        'specialization': 'Property Law',
        'experience': 9,
        'consultation_fee': 1800,
        'bio': 'Property documents, land disputes, sale deeds, rentals, and real estate checks.',
    },
]

BLOG_POSTS = [
    {
        'title': 'How to Prepare for a Legal Consultation',
        'summary': 'Simple steps clients can take before meeting a lawyer.',
        'content': 'Bring your documents, write down dates, list the people involved, and prepare clear questions for your lawyer.',
    },
    {
        'title': 'Why Legal Documents Matter',
        'summary': 'A quick guide to keeping documents ready and organized.',
        'content': 'Well-organized documents help your lawyer understand your case faster and give more accurate guidance.',
    },
]


def ensure_demo_data(create_admin=False):
    admin_created = False
    if create_admin:
        admin_username = os.getenv('DJANGO_SUPERUSER_USERNAME', 'admin')
        admin_email = os.getenv('DJANGO_SUPERUSER_EMAIL', 'admin@example.com')
        admin_password = os.getenv('DJANGO_SUPERUSER_PASSWORD', 'admin12345')
        admin_user, admin_created = User.objects.get_or_create(
            username=admin_username,
            defaults={'email': admin_email}
        )
        admin_user.email = admin_email
        admin_user.is_staff = True
        admin_user.is_superuser = True
        admin_user.set_password(admin_password)
        admin_user.save()
        admin_user.profile.user_type = 'admin'
        admin_user.profile.save()

    created_lawyers = 0
    for item in LAWYERS:
        user, created = User.objects.get_or_create(
            username=item['username'],
            defaults={
                'email': item['email'],
                'first_name': item['first_name'],
                'last_name': item['last_name'],
            }
        )
        if created:
            user.set_unusable_password()
            user.save()
            created_lawyers += 1

        profile = user.profile
        profile.user_type = 'lawyer'
        profile.specialization = item['specialization']
        profile.experience = item['experience']
        profile.consultation_fee = item['consultation_fee']
        profile.bio = item['bio']
        profile.save()

    created_posts = 0
    for item in BLOG_POSTS:
        _, created = BlogPost.objects.get_or_create(
            slug=slugify(item['title']),
            defaults={
                'title': item['title'],
                'summary': item['summary'],
                'content': item['content'],
                'is_published': True,
            }
        )
        if created:
            created_posts += 1

    return {
        'admin_created': admin_created,
        'created_lawyers': created_lawyers,
        'created_posts': created_posts,
    }
