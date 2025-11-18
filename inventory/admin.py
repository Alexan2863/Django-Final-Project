from django.contrib import admin
from .models import StorageLocation, Category, Item, InventoryEntry, UsageLog


@admin.register(StorageLocation)
class StorageLocationAdmin(admin.ModelAdmin):
    list_display = ['name', 'description']
    search_fields = ['name', 'description']


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'description']
    search_fields = ['name', 'description']


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = [
        'name',
        'category',
        'default_storage_location',
        'typical_quantity_unit',
        'low_stock_threshold',
        'preferred_store',
        'created_at'
    ]
    list_filter = ['category', 'default_storage_location', 'created_at']
    search_fields = ['name', 'preferred_store']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'category', 'typical_quantity_unit')
        }),
        ('Storage', {
            'fields': ('default_storage_location', 'preferred_store')
        }),
        ('Inventory Management', {
            'fields': ('low_stock_threshold',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(InventoryEntry)
class InventoryEntryAdmin(admin.ModelAdmin):
    list_display = [
        'item',
        'quantity',
        'storage_location',
        'purchase_date',
        'expiration_date',
        'days_until_expiration',
        'date_added'
    ]
    list_filter = [
        'storage_location',
        'purchase_date',
        'expiration_date',
        'item__category'
    ]
    search_fields = ['item__name', 'notes']
    readonly_fields = ['date_added', 'days_until_expiration']
    date_hierarchy = 'expiration_date'

    fieldsets = (
        ('Item Information', {
            'fields': ('item', 'quantity', 'storage_location')
        }),
        ('Dates', {
            'fields': ('purchase_date', 'expiration_date', 'days_until_expiration')
        }),
        ('Additional Information', {
            'fields': ('notes', 'date_added')
        }),
    )

    def days_until_expiration(self, obj):
        days = obj.days_until_expiration()
        if days < 0:
            return f"Expired {abs(days)} days ago"
        elif days == 0:
            return "Expires today"
        else:
            return f"{days} days"
    days_until_expiration.short_description = 'Days Until Expiration'


@admin.register(UsageLog)
class UsageLogAdmin(admin.ModelAdmin):
    list_display = [
        'inventory_entry',
        'quantity_used',
        'usage_date',
        'created_at'
    ]
    list_filter = ['usage_date', 'created_at']
    search_fields = ['inventory_entry__item__name', 'notes']
    readonly_fields = ['created_at']
    date_hierarchy = 'usage_date'

    fieldsets = (
        ('Usage Information', {
            'fields': ('inventory_entry', 'quantity_used', 'usage_date')
        }),
        ('Notes', {
            'fields': ('notes',)
        }),
        ('Metadata', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
