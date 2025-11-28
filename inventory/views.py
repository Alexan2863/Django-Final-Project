from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Sum, Count, Q
from django.utils import timezone
from datetime import date, timedelta
from .models import Item, InventoryEntry, UsageLog, StorageLocation, Category
from .forms import ItemForm, InventoryEntryForm, UsageLogForm, StorageLocationForm, CategoryForm


# Dashboard View
def dashboard(request):
    """
    Main dashboard showing summary statistics and alerts
    """
    # Calculate summary statistics
    total_items = InventoryEntry.objects.aggregate(total=Sum('quantity'))['total'] or 0
    unique_items = InventoryEntry.objects.values('item').distinct().count()

    # Items expiring within 7 days
    today = date.today()
    seven_days = today + timedelta(days=7)
    expiring_soon = InventoryEntry.objects.filter(
        expiration_date__gte=today,
        expiration_date__lte=seven_days,
        quantity__gt=0
    ).select_related('item', 'storage_location').order_by('expiration_date')[:5]

    # Expired items
    expired_items = InventoryEntry.objects.filter(
        expiration_date__lt=today,
        quantity__gt=0
    ).select_related('item', 'storage_location').count()

    # Low stock items
    low_stock_items = []
    for item in Item.objects.filter(low_stock_threshold__isnull=False):
        if item.is_low_stock():
            low_stock_items.append({
                'item': item,
                'current_quantity': item.get_total_quantity(),
                'threshold': item.low_stock_threshold
            })
    low_stock_items = low_stock_items[:5]

    # Storage location summary
    storage_summary = StorageLocation.objects.annotate(
        item_count=Count('inventory_entries', filter=Q(inventory_entries__quantity__gt=0))
    ).order_by('-item_count')

    context = {
        'total_items': total_items,
        'unique_items': unique_items,
        'expiring_soon': expiring_soon,
        'expiring_soon_count': expiring_soon.count() if expiring_soon else 0,
        'expired_count': expired_items,
        'low_stock_items': low_stock_items,
        'low_stock_count': len(low_stock_items),
        'storage_summary': storage_summary,
    }

    return render(request, 'inventory/dashboard.html', context)


# Inventory Entry Views
def inventory_list(request):
    """
    List all inventory entries with filtering
    """
    entries = InventoryEntry.objects.select_related(
        'item', 'storage_location', 'item__category'
    ).order_by('expiration_date')

    # Apply filters
    search = request.GET.get('search')
    if search:
        entries = entries.filter(
            Q(item__name__icontains=search) | Q(notes__icontains=search)
        )

    category = request.GET.get('category')
    if category:
        entries = entries.filter(item__category_id=category)

    location = request.GET.get('location')
    if location:
        entries = entries.filter(storage_location_id=location)

    status = request.GET.get('status')
    today = date.today()
    if status == 'expiring':
        seven_days = today + timedelta(days=7)
        entries = entries.filter(expiration_date__gte=today, expiration_date__lte=seven_days)
    elif status == 'expired':
        entries = entries.filter(expiration_date__lt=today)
    elif status == 'fresh':
        seven_days = today + timedelta(days=7)
        entries = entries.filter(expiration_date__gt=seven_days)

    # Get filter options
    categories = Category.objects.all()
    locations = StorageLocation.objects.all()

    context = {
        'entries': entries,
        'categories': categories,
        'locations': locations,
        'search': search or '',
        'selected_category': category or '',
        'selected_location': location or '',
        'selected_status': status or '',
    }

    return render(request, 'inventory/inventory_list.html', context)


def inventory_entry_create(request):
    """Create a new inventory entry"""
    if request.method == 'POST':
        form = InventoryEntryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Inventory entry added successfully!')
            return redirect('inventory:inventory_list')
    else:
        form = InventoryEntryForm()

    return render(request, 'inventory/inventory_entry_form.html', {
        'form': form,
        'title': 'Add Inventory Entry'
    })


def inventory_entry_update(request, pk):
    """Update an existing inventory entry"""
    entry = get_object_or_404(InventoryEntry, pk=pk)

    if request.method == 'POST':
        form = InventoryEntryForm(request.POST, instance=entry)
        if form.is_valid():
            form.save()
            messages.success(request, 'Inventory entry updated successfully!')
            return redirect('inventory:inventory_list')
    else:
        form = InventoryEntryForm(instance=entry)

    return render(request, 'inventory/inventory_entry_form.html', {
        'form': form,
        'title': 'Edit Inventory Entry',
        'entry': entry
    })


def inventory_entry_delete(request, pk):
    """Delete an inventory entry"""
    entry = get_object_or_404(InventoryEntry, pk=pk)

    if request.method == 'POST':
        entry.delete()
        messages.success(request, 'Inventory entry deleted successfully!')
        return redirect('inventory:inventory_list')

    return render(request, 'inventory/inventory_entry_confirm_delete.html', {
        'entry': entry
    })


# Item Views
def item_list(request):
    """List all items"""
    items = Item.objects.select_related(
        'category', 'default_storage_location'
    ).order_by('name')

    # Apply search filter
    search = request.GET.get('search')
    if search:
        items = items.filter(Q(name__icontains=search) | Q(preferred_store__icontains=search))

    # Apply category filter
    category = request.GET.get('category')
    if category:
        items = items.filter(category_id=category)

    categories = Category.objects.all()

    context = {
        'items': items,
        'categories': categories,
        'search': search or '',
        'selected_category': category or '',
    }

    return render(request, 'inventory/item_list.html', context)


def item_detail(request, pk):
    """Display item details with inventory and usage history"""
    item = get_object_or_404(Item.objects.select_related('category', 'default_storage_location'), pk=pk)

    inventory_entries = item.inventory_entries.filter(
        quantity__gt=0
    ).select_related('storage_location').order_by('expiration_date')

    recent_usage = UsageLog.objects.filter(
        inventory_entry__item=item
    ).select_related('inventory_entry').order_by('-usage_date')[:10]

    context = {
        'item': item,
        'total_quantity': item.get_total_quantity(),
        'inventory_entries': inventory_entries,
        'recent_usage': recent_usage,
        'is_low_stock': item.is_low_stock(),
    }

    return render(request, 'inventory/item_detail.html', context)


def item_create(request):
    """Create a new item"""
    if request.method == 'POST':
        form = ItemForm(request.POST)
        if form.is_valid():
            item = form.save()
            messages.success(request, f'Item "{item.name}" created successfully!')
            return redirect('inventory:item_detail', pk=item.pk)
    else:
        form = ItemForm()

    return render(request, 'inventory/item_form.html', {
        'form': form,
        'title': 'Add New Item'
    })


def item_update(request, pk):
    """Update an existing item"""
    item = get_object_or_404(Item, pk=pk)

    if request.method == 'POST':
        form = ItemForm(request.POST, instance=item)
        if form.is_valid():
            form.save()
            messages.success(request, f'Item "{item.name}" updated successfully!')
            return redirect('inventory:item_detail', pk=item.pk)
    else:
        form = ItemForm(instance=item)

    return render(request, 'inventory/item_form.html', {
        'form': form,
        'title': f'Edit {item.name}',
        'item': item
    })


def item_delete(request, pk):
    """Delete an item"""
    item = get_object_or_404(Item, pk=pk)

    if request.method == 'POST':
        item_name = item.name
        item.delete()
        messages.success(request, f'Item "{item_name}" deleted successfully!')
        return redirect('inventory:item_list')

    return render(request, 'inventory/item_confirm_delete.html', {
        'item': item
    })


# Storage Location Views
def location_list(request):
    """List all storage locations"""
    locations = StorageLocation.objects.annotate(
        item_count=Count('inventory_entries', filter=Q(inventory_entries__quantity__gt=0))
    ).order_by('name')

    return render(request, 'inventory/location_list.html', {
        'locations': locations
    })


def location_create(request):
    """Create a new storage location"""
    if request.method == 'POST':
        form = StorageLocationForm(request.POST)
        if form.is_valid():
            location = form.save()
            messages.success(request, f'Storage location "{location.name}" created successfully!')
            return redirect('inventory:location_list')
    else:
        form = StorageLocationForm()

    return render(request, 'inventory/location_form.html', {
        'form': form,
        'title': 'Add Storage Location'
    })


def location_update(request, pk):
    """Update an existing storage location"""
    location = get_object_or_404(StorageLocation, pk=pk)

    if request.method == 'POST':
        form = StorageLocationForm(request.POST, instance=location)
        if form.is_valid():
            form.save()
            messages.success(request, f'Storage location "{location.name}" updated successfully!')
            return redirect('inventory:location_list')
    else:
        form = StorageLocationForm(instance=location)

    return render(request, 'inventory/location_form.html', {
        'form': form,
        'title': f'Edit {location.name}',
        'location': location
    })


def location_delete(request, pk):
    """Delete a storage location"""
    location = get_object_or_404(StorageLocation, pk=pk)

    if request.method == 'POST':
        location_name = location.name
        try:
            location.delete()
            messages.success(request, f'Storage location "{location_name}" deleted successfully!')
        except Exception as e:
            messages.error(request, f'Cannot delete storage location. It may be in use by items or inventory entries.')
        return redirect('inventory:location_list')

    return render(request, 'inventory/location_confirm_delete.html', {
        'location': location
    })


# Category Views
def category_list(request):
    """List all categories"""
    categories = Category.objects.annotate(
        item_count=Count('items')
    ).order_by('name')

    return render(request, 'inventory/category_list.html', {
        'categories': categories
    })


def category_create(request):
    """Create a new category"""
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            category = form.save()
            messages.success(request, f'Category "{category.name}" created successfully!')
            return redirect('inventory:category_list')
    else:
        form = CategoryForm()

    return render(request, 'inventory/category_form.html', {
        'form': form,
        'title': 'Add Category'
    })


def category_update(request, pk):
    """Update an existing category"""
    category = get_object_or_404(Category, pk=pk)

    if request.method == 'POST':
        form = CategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            messages.success(request, f'Category "{category.name}" updated successfully!')
            return redirect('inventory:category_list')
    else:
        form = CategoryForm(instance=category)

    return render(request, 'inventory/category_form.html', {
        'form': form,
        'title': f'Edit {category.name}',
        'category': category
    })


def category_delete(request, pk):
    """Delete a category"""
    category = get_object_or_404(Category, pk=pk)

    if request.method == 'POST':
        category_name = category.name
        try:
            category.delete()
            messages.success(request, f'Category "{category_name}" deleted successfully!')
        except Exception as e:
            messages.error(request, f'Cannot delete category. It may be in use by items.')
        return redirect('inventory:category_list')

    return render(request, 'inventory/category_confirm_delete.html', {
        'category': category
    })


# Usage Log Views
def usage_log_create(request):
    """Create a new usage log entry"""
    if request.method == 'POST':
        form = UsageLogForm(request.POST)
        if form.is_valid():
            usage_log = form.save()
            # Update the inventory entry quantity
            inventory_entry = usage_log.inventory_entry
            inventory_entry.quantity -= usage_log.quantity_used
            inventory_entry.save()

            messages.success(request, 'Usage logged successfully!')
            return redirect('inventory:inventory_list')
    else:
        form = UsageLogForm()

    return render(request, 'inventory/usage_log_form.html', {
        'form': form,
        'title': 'Log Item Usage'
    })


def usage_log_list(request):
    """List all usage logs"""
    logs = UsageLog.objects.select_related(
        'inventory_entry__item', 'inventory_entry__storage_location'
    ).order_by('-usage_date', '-created_at')

    return render(request, 'inventory/usage_log_list.html', {
        'logs': logs
    })
