from django.urls import path
from . import views

app_name = 'worlds'

urlpatterns = [
    path('', views.world_list, name='list'),
    path('<int:pk>/', views.world_detail, name='detail'),
    path('create/', views.world_create, name='create'),
    path('<int:pk>/edit/', views.world_edit, name='edit'),
    path('<int:pk>/archive/', views.world_archive, name='archive'),
    path('<int:pk>/unarchive/', views.world_unarchive, name='unarchive'),
    path('<int:pk>/delete/', views.world_delete, name='delete'),
    
    # Location URLs
    path('<int:world_pk>/locations/create/', views.location_create, name='location_create'),
    path('<int:world_pk>/locations/<int:location_pk>/', views.location_detail, name='location_detail'),
    path('<int:world_pk>/locations/<int:location_pk>/edit/', views.location_edit, name='location_edit'),
    path('<int:world_pk>/locations/<int:location_pk>/delete/', views.location_delete, name='location_delete'),
    path('<int:world_pk>/locations/<int:location_pk>/add-character/', views.location_add_character, name='location_add_character'),
    
    # Faction URLs
    path('<int:world_pk>/factions/create/', views.faction_create, name='faction_create'),
    path('<int:world_pk>/factions/<int:faction_pk>/', views.faction_detail, name='faction_detail'),
    path('<int:world_pk>/factions/<int:faction_pk>/edit/', views.faction_edit, name='faction_edit'),
    path('<int:world_pk>/factions/<int:faction_pk>/delete/', views.faction_delete, name='faction_delete'),
    path('<int:world_pk>/factions/<int:faction_pk>/add-member/', views.faction_add_member, name='faction_add_member'),
    
    # Event URLs
    path('<int:world_pk>/events/create/', views.event_create, name='event_create'),
    path('<int:world_pk>/events/<int:event_pk>/edit/', views.event_edit, name='event_edit'),
    path('<int:world_pk>/events/<int:event_pk>/delete/', views.event_delete, name='event_delete'),
    
    # Item URLs
    path('<int:world_pk>/items/create/', views.item_create, name='item_create'),
    path('<int:world_pk>/items/<int:item_pk>/edit/', views.item_edit, name='item_edit'),
    path('<int:world_pk>/items/<int:item_pk>/delete/', views.item_delete, name='item_delete'),
    
    # Culture URLs
    path('<int:world_pk>/cultures/create/', views.culture_create, name='culture_create'),
    path('<int:world_pk>/cultures/<int:culture_pk>/edit/', views.culture_edit, name='culture_edit'),
    path('<int:world_pk>/cultures/<int:culture_pk>/delete/', views.culture_delete, name='culture_delete'),
    
    # Notes URLs
    path('<int:world_pk>/notes/create/', views.notes_create, name='notes_create'),
    path('<int:world_pk>/notes/<int:notes_pk>/edit/', views.notes_edit, name='notes_edit'),
    path('<int:world_pk>/notes/<int:notes_pk>/delete/', views.notes_delete, name='notes_delete'),
]