from django.contrib import admin
from .models import Profile, Appointment, Review, AppointmentDocument, Invoice, BlogPost, ChatMessage, AvailabilitySlot


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'unique_id',
        'user_type',
        'gender',
        'birthdate',
        'profession',
        'specialization',
        'experience',
        'consultation_fee',
    )


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = (
        'client',
        'lawyer',
        'appointment_date',
        'appointment_time',
        'status',
        'mobile_number',
    )
    list_filter = ('status',)


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('appointment', 'user', 'lawyer', 'rating', 'created_at')
    list_filter = ('rating',)


@admin.register(AppointmentDocument)
class AppointmentDocumentAdmin(admin.ModelAdmin):
    list_display = ('appointment', 'title', 'uploaded_at')


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ('invoice_number', 'appointment', 'amount', 'status', 'issued_at', 'due_date')
    list_filter = ('status',)


@admin.register(BlogPost)
class BlogPostAdmin(admin.ModelAdmin):
    list_display = ('title', 'slug', 'published_at', 'is_published')
    prepopulated_fields = {'slug': ('title',)}


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ('appointment', 'sender', 'receiver', 'created_at')


@admin.register(AvailabilitySlot)
class AvailabilitySlotAdmin(admin.ModelAdmin):
    list_display = ('lawyer', 'day', 'start_time', 'end_time', 'is_active')
