from django.urls import path
from . import views

app_name = 'characters'

urlpatterns = [
    path('', views.character_list, name='list'),
    path('<int:pk>/', views.character_detail, name='detail'),
    path('create/', views.character_create, name='create'),
    path('<int:pk>/edit/', views.character_edit, name='edit'),
    path('<int:pk>/delete/', views.character_delete, name='delete'),
    path('<int:pk>/archive/', views.character_archive, name='archive'),
    path('<int:pk>/unarchive/', views.character_unarchive, name='unarchive'),
    path('generate/', views.character_generate, name='generate'),
    path('<int:pk>/add-memory/', views.add_character_memory, name='add_memory'),
]