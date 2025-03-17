from django.urls import path
from . import views

app_name = 'journals'

urlpatterns = [
    path('', views.journal_list, name='list'),
    path('<int:pk>/', views.journal_detail, name='detail'),
    path('create/', views.journal_create, name='create'),
    path('<int:pk>/edit/', views.journal_edit, name='edit'),
    path('<int:pk>/archive/', views.journal_archive, name='archive'),
    path('<int:pk>/unarchive/', views.journal_unarchive, name='unarchive'),
    path('<int:pk>/delete/', views.journal_delete, name='delete'),
    
    # Entry URLs
    path('<int:journal_pk>/entries/create/', views.entry_create, name='entry_create'),
    path('<int:journal_pk>/entries/<int:entry_pk>/', views.entry_detail, name='entry_detail'),
    path('<int:journal_pk>/entries/<int:entry_pk>/edit/', views.entry_edit, name='entry_edit'),
    path('<int:journal_pk>/entries/<int:entry_pk>/delete/', views.entry_delete, name='entry_delete'),
    
    # Template URLs
    path('templates/', views.template_list, name='template_list'),
    path('templates/create/', views.template_create, name='template_create'),
    path('templates/<int:pk>/edit/', views.template_edit, name='template_edit'),
    path('templates/<int:pk>/delete/', views.template_delete, name='template_delete'),
    
    # Prompt URLs
    path('prompts/', views.prompt_list, name='prompt_list'),
    path('prompts/create/', views.prompt_create, name='prompt_create'),
    path('prompts/<int:pk>/delete/', views.prompt_delete, name='prompt_delete'),
    path('prompts/random/', views.random_prompt, name='random_prompt'),
]