from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import timedelta


# =========================
# PROFILE MODEL
# =========================
class Profile(models.Model):

    USER_TYPE_CHOICES = (
        ('client', 'Client'),
        ('lawyer', 'Lawyer'),
        ('admin', 'Admin'),
    )

    GENDER_CHOICES = (
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE)

    unique_id = models.CharField(max_length=20, unique=True, blank=True, null=True)

    user_type = models.CharField(max_length=10, choices=USER_TYPE_CHOICES, default="client")

    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, blank=True, null=True)
    birthdate = models.DateField(blank=True, null=True)
    profession = models.CharField(max_length=100, blank=True, null=True)

    specialization = models.CharField(max_length=100, blank=True, null=True)
    experience = models.IntegerField(blank=True, null=True)
    consultation_fee = models.IntegerField(blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    photo = models.ImageField(upload_to='profile_photos/', blank=True, null=True)
    signature = models.ImageField(upload_to='signatures/', blank=True, null=True)

    def __str__(self):
        return f"{self.user.username} ({self.unique_id})"

    @property
    def display_fee(self):
        return f"₹{self.consultation_fee}" if self.consultation_fee else "TBD"

    @property
    def rating(self):
        base_rating = 4.2 + (self.experience or 0) * 0.05
        return round(min(base_rating, 5.0), 1)

    @property
    def cases_handled(self):
        return 50 + (self.experience or 0) * 10

    @property
    def summary(self):
        if self.bio:
            return self.bio
        return f"Trusted legal counsel with {self.experience or 'several'} years of experience in {self.specialization or 'multiple practice areas'}."


# =========================
# APPOINTMENT MODEL
# =========================
class Appointment(models.Model):

    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
        ('cancelled', 'Cancelled'),
    )

    client = models.ForeignKey(User, on_delete=models.CASCADE, related_name='client_appointments')
    lawyer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='lawyer_appointments')

    message = models.TextField(blank=True, null=True)

    appointment_date = models.DateField()
    appointment_time = models.TimeField()
    
    mobile_number = models.CharField(max_length=15, blank=True, null=True)
    meeting_link = models.URLField(blank=True, null=True)

    reschedule_request_date = models.DateField(blank=True, null=True)
    reschedule_request_time = models.TimeField(blank=True, null=True)
    reschedule_request_message = models.TextField(blank=True, null=True)
    reschedule_status = models.CharField(max_length=15, choices=(
        ('none', 'None'),
        ('requested', 'Requested'),
        ('approved', 'Approved'),
        ('declined', 'Declined'),
    ), default='none')

    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('lawyer', 'appointment_date', 'appointment_time')
        ordering = ['-appointment_date', '-appointment_time']

    def appointment_datetime(self):
        return timezone.datetime.combine(self.appointment_date, self.appointment_time)

    def can_cancel(self):

        appointment_time = timezone.datetime.combine(self.appointment_date, self.appointment_time)
        appointment_time = timezone.make_aware(appointment_time)

        cancellation_limit = appointment_time - timedelta(hours=12)

        return timezone.now() < cancellation_limit

    def clean(self):

        if self.appointment_date < timezone.now().date():
            raise ValidationError("Cannot book past date.")

        if self.client == self.lawyer:
            raise ValidationError("Cannot book yourself.")

        if hasattr(self.client, 'profile'):
            if self.client.profile.user_type != "client":
                raise ValidationError("Only clients can book.")

    @property
    def whatsapp_message(self):
        """Generate WhatsApp-formatted booking details."""
        lawyer_name = f"{self.lawyer.first_name} {self.lawyer.last_name}".strip() or self.lawyer.username
        return (
            f"📅 *LegalConnect Appointment Confirmation*\n\n"
            f"Lawyer: {lawyer_name}\n"
            f"Date: {self.appointment_date.strftime('%d %B %Y')}\n"
            f"Time: {self.appointment_time.strftime('%I:%M %p')}\n"
            f"Status: {self.status.title()}\n\n"
            f"Case Details: {self.message or 'N/A'}\n\n"
            f"Booking ID: #{self.id}\n"
            f"Booked on: {self.created_at.strftime('%d %b %Y')}\n\n"
            f"Thank you for using LegalConnect!"
        )

    @property
    def whatsapp_link(self):
        """Generate WhatsApp share link for booking details."""
        import urllib.parse
        if not self.mobile_number:
            return None
        phone = self.mobile_number.replace('+', '').replace('-', '').replace(' ', '')
        encoded_msg = urllib.parse.quote(self.whatsapp_message)
        return f"https://wa.me/{phone}?text={encoded_msg}"

    def __str__(self):
        return f"{self.client.username} → {self.lawyer.username} ({self.status})"

    @classmethod
    def is_slot_available(cls, lawyer, appointment_date, appointment_time, exclude_id=None):
        appointments = cls.objects.filter(
            lawyer=lawyer,
            appointment_date=appointment_date,
            appointment_time=appointment_time,
        ).exclude(status__in=['cancelled', 'rejected'])
        if exclude_id:
            appointments = appointments.exclude(id=exclude_id)
        return not appointments.exists()


class Review(models.Model):
    appointment = models.OneToOneField(Appointment, on_delete=models.CASCADE, related_name='review')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews')
    lawyer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='lawyer_reviews')
    rating = models.PositiveSmallIntegerField(default=5)
    comment = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Review {self.rating} for {self.lawyer.username}"


class AppointmentDocument(models.Model):
    appointment = models.ForeignKey(Appointment, on_delete=models.CASCADE, related_name='documents')
    file = models.FileField(upload_to='appointment_documents/')
    title = models.CharField(max_length=200, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title or f"Document {self.id}"


class Invoice(models.Model):
    appointment = models.OneToOneField(Appointment, on_delete=models.CASCADE, related_name='invoice')
    invoice_number = models.CharField(max_length=40, unique=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=(
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('cancelled', 'Cancelled'),
    ), default='pending')
    issued_at = models.DateTimeField(auto_now_add=True)
    due_date = models.DateField(blank=True, null=True)
    paid_at = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return self.invoice_number


class BlogPost(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    summary = models.TextField(blank=True)
    content = models.TextField()
    published_at = models.DateTimeField(auto_now_add=True)
    author = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True)
    is_published = models.BooleanField(default=True)

    def __str__(self):
        return self.title


class ChatMessage(models.Model):
    appointment = models.ForeignKey(Appointment, on_delete=models.CASCADE, related_name='chat_messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_messages')
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Chat {self.id}"


class AvailabilitySlot(models.Model):
    DAYS_OF_WEEK = [
        ('mon', 'Monday'),
        ('tue', 'Tuesday'),
        ('wed', 'Wednesday'),
        ('thu', 'Thursday'),
        ('fri', 'Friday'),
        ('sat', 'Saturday'),
        ('sun', 'Sunday'),
    ]
    lawyer = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='availability_slots')
    day = models.CharField(max_length=3, choices=DAYS_OF_WEEK)
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ('lawyer', 'day', 'start_time', 'end_time')

    def __str__(self):
        return f"{self.lawyer.user.username} - {self.get_day_display()} {self.start_time}-{self.end_time}"


class AIChat(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    question = models.TextField()
    answer = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user.username


class AIConversation(models.Model):
    """Tracks ongoing AI conversations for structured booking flow"""

    CONVERSATION_STATES = (
        ('welcome', 'Welcome'),
        ('lawyer_selection', 'Lawyer Selection'),
        ('date_selection', 'Date Selection'),
        ('time_selection', 'Time Selection'),
        ('confirmation', 'Confirmation'),
        ('completed', 'Completed'),
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    state = models.CharField(max_length=20, choices=CONVERSATION_STATES, default='welcome')
    selected_category = models.CharField(max_length=100, blank=True, null=True)
    selected_lawyer_id = models.IntegerField(blank=True, null=True)
    selected_date = models.DateField(blank=True, null=True)
    selected_time = models.TimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} - {self.state}"

    def reset(self):
        """Reset conversation to welcome state"""
        self.state = 'welcome'
        self.selected_category = None
        self.selected_lawyer_id = None
        self.selected_date = None
        self.selected_time = None
        self.save()

    def get_next_options(self):
        """Get available options for current state"""
        if self.state == 'welcome':
            return {
                'type': 'categories',
                'options': [
                    {'id': 'criminal', 'label': 'Criminal Law', 'icon': '⚖️'},
                    {'id': 'family', 'label': 'Family Law', 'icon': '👨‍👩‍👧‍👦'},
                    {'id': 'corporate', 'label': 'Corporate Law', 'icon': '🏢'},
                    {'id': 'property', 'label': 'Property Law', 'icon': '🏠'},
                    {'id': 'other', 'label': 'Other Legal Issues', 'icon': '📋'},
                ]
            }
        elif self.state == 'lawyer_selection':
            from django.db.models import Q

            category_terms = {
                'criminal': ['criminal', 'crime'],
                'family': ['family', 'divorce', 'custody'],
                'corporate': ['corporate', 'business', 'company'],
                'property': ['property', 'real estate', 'land'],
                'other': [],
            }
            lawyers = Profile.objects.filter(user_type='lawyer').select_related('user')
            terms = category_terms.get(self.selected_category, [self.selected_category])
            if terms:
                query = Q()
                for term in terms:
                    query |= Q(specialization__icontains=term) | Q(bio__icontains=term)
                matched_lawyers = lawyers.filter(query)
                if matched_lawyers.exists():
                    lawyers = matched_lawyers
            lawyers = lawyers.order_by('user__first_name', 'user__username')[:10]

            return {
                'type': 'lawyers',
                'options': [
                    {
                        'id': lawyer.id,
                        'label': f"{lawyer.user.first_name} {lawyer.user.last_name}",
                        'specialization': lawyer.specialization or 'General',
                        'experience': f"{lawyer.experience} years" if lawyer.experience else 'Experience not specified',
                        'fee': f"₹{lawyer.consultation_fee}" if lawyer.consultation_fee else 'Fee not specified'
                    } for lawyer in lawyers
                ]
            }
        elif self.state == 'date_selection':
            from datetime import datetime, timedelta
            today = datetime.now().date()
            dates = []
            for i in range(7):  # Next 7 days
                date = today + timedelta(days=i)
                dates.append({
                    'id': date.isoformat(),
                    'label': date.strftime('%A, %b %d'),
                    'available': True  # Could check availability later
                })

            return {
                'type': 'dates',
                'options': dates
            }
        elif self.state == 'time_selection':
            if not self.selected_lawyer_id or not self.selected_date:
                return {'type': 'times', 'options': []}

            lawyer_profile = Profile.objects.filter(
                id=self.selected_lawyer_id,
                user_type='lawyer'
            ).select_related('user').first()
            if not lawyer_profile:
                return {'type': 'times', 'options': []}

            times = []
            for hour in range(9, 18):  # 9 AM to 5 PM
                for minute in [0, 30]:
                    time_str = f"{hour:02d}:{minute:02d}"
                    from datetime import datetime
                    option_time = datetime.strptime(time_str, '%H:%M').time()
                    times.append({
                        'id': time_str,
                        'label': time_str,
                        'available': Appointment.is_slot_available(
                            lawyer_profile.user,
                            self.selected_date,
                            option_time
                        )
                    })

            return {
                'type': 'times',
                'options': [slot for slot in times if slot['available']]
            }
        elif self.state == 'confirmation':
            return {
                'type': 'confirmation',
                'options': [
                    {'id': 'yes', 'label': '✅ Yes, Confirm Booking', 'type': 'primary'},
                    {'id': 'no', 'label': '❌ Cancel', 'type': 'secondary'}
                ]
            }

        return None 
