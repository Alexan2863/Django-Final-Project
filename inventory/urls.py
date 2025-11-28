from django.urls import path
from . import views

app_name = 'inventory'

urlpatterns = [
    # Dashboard
    path('', views.dashboard, name='dashboard'),

    # Inventory Entry URLs
    path('inventory/', views.inventory_list, name='inventory_list'),
    path('inventory/add/', views.inventory_entry_create, name='inventory_entry_create'),
    path('inventory/<int:pk>/edit/', views.inventory_entry_update, name='inventory_entry_update'),
    path('inventory/<int:pk>/delete/', views.inventory_entry_delete, name='inventory_entry_delete'),

    # Item URLs
    path('items/', views.item_list, name='item_list'),
    path('items/add/', views.item_create, name='item_create'),
    path('items/<int:pk>/', views.item_detail, name='item_detail'),
    path('items/<int:pk>/edit/', views.item_update, name='item_update'),
    path('items/<int:pk>/delete/', views.item_delete, name='item_delete'),

    # Storage Location URLs
    path('locations/', views.location_list, name='location_list'),
    path('locations/add/', views.location_create, name='location_create'),
    path('locations/<int:pk>/edit/', views.location_update, name='location_update'),
    path('locations/<int:pk>/delete/', views.location_delete, name='location_delete'),

    # Category URLs
    path('categories/', views.category_list, name='category_list'),
    path('categories/add/', views.category_create, name='category_create'),
    path('categories/<int:pk>/edit/', views.category_update, name='category_update'),
    path('categories/<int:pk>/delete/', views.category_delete, name='category_delete'),

    # Usage Log URLs
    path('usage/add/', views.usage_log_create, name='usage_log_create'),
    path('usage/', views.usage_log_list, name='usage_log_list'),
]
