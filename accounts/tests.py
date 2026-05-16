from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone

from .models import AIConversation, Appointment


class AIBookingChatTests(TestCase):
    def setUp(self):
        self.client_user = User.objects.create_user(
            username='client',
            email='client@example.com',
            password='pass12345'
        )
        self.client_user.profile.user_type = 'client'
        self.client_user.profile.save()

        self.lawyer_user = User.objects.create_user(
            username='lawyer',
            email='lawyer@example.com',
            password='pass12345',
            first_name='Legal',
            last_name='Expert'
        )
        self.lawyer_user.profile.user_type = 'lawyer'
        self.lawyer_user.profile.specialization = 'Criminal Law'
        self.lawyer_user.profile.experience = 5
        self.lawyer_user.profile.consultation_fee = 1000
        self.lawyer_user.profile.save()

    def test_ai_booking_creates_pending_appointment(self):
        self.client.login(username='client', password='pass12345')

        self.client.post('/ai-booking-chat/', {
            'action': 'select_option',
            'option_type': 'category',
            'option_id': 'criminal',
        })
        self.client.post('/ai-booking-chat/', {
            'action': 'select_option',
            'option_type': 'lawyer',
            'option_id': str(self.lawyer_user.profile.id),
        })
        self.client.post('/ai-booking-chat/', {
            'action': 'select_option',
            'option_type': 'date',
            'option_id': timezone.localdate().isoformat(),
        })
        self.client.post('/ai-booking-chat/', {
            'action': 'select_option',
            'option_type': 'time',
            'option_id': '10:00',
        })
        response = self.client.post('/ai-booking-chat/', {
            'action': 'select_option',
            'option_type': 'confirm',
            'option_id': 'yes',
        })

        appointment = Appointment.objects.get()
        conversation = AIConversation.objects.get(user=self.client_user)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], f'/appointment/{appointment.id}/confirmation/')
        self.assertEqual(appointment.status, 'pending')
        self.assertEqual(appointment.client, self.client_user)
        self.assertEqual(appointment.lawyer, self.lawyer_user)
        self.assertEqual(conversation.state, 'completed')
