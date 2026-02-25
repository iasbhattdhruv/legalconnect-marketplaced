from django.urls import path
from .views import (
    home_view,
    register_view,
    login_view,
    logout_view,
    dashboard_view,
    lawyer_list_view,
    lawyer_detail_view,
    book_appointment_view,
)

urlpatterns = [
    path('', home_view, name='home'),
    path('register/', register_view, name='register'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('dashboard/', dashboard_view, name='dashboard'),

    # Marketplace URLs
    path('lawyers/', lawyer_list_view, name='lawyers'),
    path('lawyer/<int:pk>/', lawyer_detail_view, name='lawyer_detail'),
    path('book/<int:pk>/', book_appointment_view, name='book'),
]