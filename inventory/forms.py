from django import forms
from django.core.exceptions import ValidationError
from .models import Item, InventoryEntry, UsageLog, StorageLocation, Category


class StorageLocationForm(forms.ModelForm):
    """Form for creating and editing storage locations"""

    class Meta:
        model = StorageLocation
        fields = ['name', 'description']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }


class CategoryForm(forms.ModelForm):
    """Form for creating and editing categories"""

    class Meta:
        model = Category
        fields = ['name', 'description']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }


class ItemForm(forms.ModelForm):
    """Form for creating and editing items"""

    class Meta:
        model = Item
        fields = [
            'name',
            'category',
            'default_storage_location',
            'preferred_store',
            'typical_quantity_unit',
            'low_stock_threshold',
        ]
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'e.g., Whole Milk, Chicken Breast'}),
            'preferred_store': forms.TextInput(attrs={'placeholder': 'e.g., Costco, Trader Joe\'s'}),
            'typical_quantity_unit': forms.TextInput(attrs={'placeholder': 'e.g., gallon, lb, package'}),
        }
        help_texts = {
            'low_stock_threshold': 'Leave blank for no alerts',
        }

    def clean_low_stock_threshold(self):
        """Ensure low_stock_threshold is positive if provided"""
        threshold = self.cleaned_data.get('low_stock_threshold')
        if threshold is not None and threshold <= 0:
            raise ValidationError('Low stock threshold must be greater than 0')
        return threshold


class InventoryEntryForm(forms.ModelForm):
    """Form for adding items to inventory"""

    class Meta:
        model = InventoryEntry
        fields = [
            'item',
            'quantity',
            'storage_location',
            'purchase_date',
            'expiration_date',
            'notes',
        ]
        widgets = {
            'purchase_date': forms.DateInput(attrs={'type': 'date'}),
            'expiration_date': forms.DateInput(attrs={'type': 'date'}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }

    def clean_quantity(self):
        """Ensure quantity is positive"""
        quantity = self.cleaned_data.get('quantity')
        if quantity <= 0:
            raise ValidationError('Quantity must be greater than 0')
        return quantity

    def clean(self):
        """Validate that expiration date is after purchase date"""
        cleaned_data = super().clean()
        purchase_date = cleaned_data.get('purchase_date')
        expiration_date = cleaned_data.get('expiration_date')

        if purchase_date and expiration_date:
            if expiration_date < purchase_date:
                raise ValidationError({
                    'expiration_date': 'Expiration date cannot be before purchase date'
                })

        return cleaned_data


class UsageLogForm(forms.ModelForm):
    """Form for logging item usage"""

    class Meta:
        model = UsageLog
        fields = [
            'inventory_entry',
            'quantity_used',
            'usage_date',
            'notes',
        ]
        widgets = {
            'usage_date': forms.DateInput(attrs={'type': 'date'}),
            'notes': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': 'What did you make with this item?'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only show inventory entries with quantity > 0
        self.fields['inventory_entry'].queryset = InventoryEntry.objects.filter(
            quantity__gt=0
        ).select_related('item', 'storage_location')

    def clean_quantity_used(self):
        """Ensure quantity_used is positive"""
        quantity = self.cleaned_data.get('quantity_used')
        if quantity <= 0:
            raise ValidationError('Quantity used must be greater than 0')
        return quantity

    def clean(self):
        """Validate that quantity_used doesn't exceed available quantity"""
        cleaned_data = super().clean()
        inventory_entry = cleaned_data.get('inventory_entry')
        quantity_used = cleaned_data.get('quantity_used')

        if inventory_entry and quantity_used:
            if quantity_used > inventory_entry.quantity:
                raise ValidationError({
                    'quantity_used': f'Cannot use more than available quantity ({inventory_entry.quantity})'
                })

        return cleaned_data
