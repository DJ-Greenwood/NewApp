from django.urls import path
from . import views

app_name = 'conversations'

urlpatterns = [
    path('', views.conversation_list, name='list'),
    path('<int:pk>/', views.conversation_detail, name='detail'),
    path('create/', views.conversation_create, name='create'),
    path('character/<int:character_id>/create/', views.conversation_create_with_character, name='create_with_character'),
    path('<int:pk>/archive/', views.conversation_archive, name='archive'),
    path('<int:pk>/unarchive/', views.conversation_unarchive, name='unarchive'),
    path('<int:pk>/delete/', views.conversation_delete, name='delete'),
    path('<int:pk>/create-summary/', views.create_summary, name='create_summary'),

     # Additional URLs needed based on template references
    path('<int:pk>/send/', views.send_message, name='send_message'),  # Add this for AJAX message sending
    path('<int:conversation_id>/toggle-favorite/', views.toggle_favorite, name='toggle_favorite'),  # Add for favorite functionality
    path('<int:conversation_id>/export/', views.conversation_export, name='export'),  # Add for export functionality
]