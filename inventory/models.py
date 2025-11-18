from django.db import models
from django.utils import timezone


class StorageLocation(models.Model):
    """
    Represents physical storage areas (Pantry, Fridge, Freezer, etc.)
    """
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class Category(models.Model):
    """
    Organizes items into logical groupings (Dairy, Produce, Canned Goods, etc.)
    """
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['name']
        verbose_name_plural = 'Categories'

    def __str__(self):
        return self.name


class Item(models.Model):
    """
    Represents a type of food product
    """
    name = models.CharField(max_length=200)
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name='items'
    )
    default_storage_location = models.ForeignKey(
        StorageLocation,
        on_delete=models.PROTECT,
        related_name='default_items'
    )
    preferred_store = models.CharField(max_length=100, blank=True, null=True)
    typical_quantity_unit = models.CharField(max_length=50, default='unit')
    low_stock_threshold = models.IntegerField(
        blank=True,
        null=True,
        help_text='Alert when total quantity falls below this number'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

    def get_total_quantity(self):
        """Calculate total quantity across all storage locations"""
        return sum(entry.quantity for entry in self.inventory_entries.all())

    def is_low_stock(self):
        """Check if item is below low stock threshold"""
        if self.low_stock_threshold is None:
            return False
        return self.get_total_quantity() < self.low_stock_threshold


class InventoryEntry(models.Model):
    """
    Represents a specific instance of an item in storage
    """
    item = models.ForeignKey(
        Item,
        on_delete=models.CASCADE,
        related_name='inventory_entries'
    )
    quantity = models.IntegerField(default=1)
    storage_location = models.ForeignKey(
        StorageLocation,
        on_delete=models.PROTECT,
        related_name='inventory_entries'
    )
    purchase_date = models.DateField(default=timezone.now)
    expiration_date = models.DateField()
    notes = models.TextField(blank=True, null=True)
    date_added = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['expiration_date', 'item__name']
        verbose_name_plural = 'Inventory Entries'

    def __str__(self):
        return f"{self.item.name} ({self.quantity} {self.item.typical_quantity_unit}) - {self.storage_location.name}"

    def days_until_expiration(self):
        """Calculate days until expiration"""
        from datetime import date
        delta = self.expiration_date - date.today()
        return delta.days

    def is_expiring_soon(self, days=7):
        """Check if item is expiring within specified days"""
        return 0 <= self.days_until_expiration() <= days

    def is_expired(self):
        """Check if item has expired"""
        return self.days_until_expiration() < 0


class UsageLog(models.Model):
    """
    Tracks when and how items are used
    """
    inventory_entry = models.ForeignKey(
        InventoryEntry,
        on_delete=models.CASCADE,
        related_name='usage_logs'
    )
    quantity_used = models.IntegerField()
    usage_date = models.DateField(default=timezone.now)
    notes = models.TextField(
        blank=True,
        null=True,
        help_text='What was made with this item'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-usage_date', '-created_at']

    def __str__(self):
        return f"{self.quantity_used} {self.inventory_entry.item.typical_quantity_unit} of {self.inventory_entry.item.name} used on {self.usage_date}"
