from django.urls import path
from . import views

app_name = 'stories'

urlpatterns = [
    path('', views.story_list, name='list'),
    path('<int:pk>/', views.story_detail, name='detail'),
    path('create/', views.story_create, name='create'),
    path('<int:pk>/edit/', views.story_edit, name='edit'),
    path('<int:pk>/write/', views.story_write, name='write'),
    path('<int:pk>/archive/', views.story_archive, name='archive'),
    path('<int:pk>/unarchive/', views.story_unarchive, name='unarchive'),
    path('<int:pk>/delete/', views.story_delete, name='delete'),
    path('<int:pk>/assistance/', views.story_assistance, name='assistance'),
    
    # Chapter URLs
    path('<int:story_pk>/chapters/create/', views.chapter_create, name='chapter_create'),
    path('<int:story_pk>/chapters/<int:chapter_pk>/edit/', views.chapter_edit, name='chapter_edit'),
    
    # Note URLs
    path('<int:story_pk>/notes/create/', views.note_create, name='note_create'),
    path('<int:story_pk>/notes/<int:note_pk>/edit/', views.note_edit, name='note_edit'),
    path('<int:story_pk>/notes/<int:note_pk>/delete/', views.note_delete, name='note_delete'),
]