from django.contrib import admin
from django.contrib.auth import get_user_model
from django.db.models import Sum
from orders.models import Order
from shop.models import Product

def dashboard_context(user):
    context = {}
    if user.has_perm('shop.view_product'):
        context['product_total'] = Product.objects.count()
        context['stock_total'] = Product.objects.aggregate(total=Sum('stock_quantity'))['total'] or 0
        context['low_stock'] = Product.objects.filter(stock_quantity__lte=5).order_by('stock_quantity', 'name')[:8]
    if user.has_perm('orders.view_order'):
        context['order_total'] = Order.objects.count()
        context['pending_total'] = Order.objects.filter(status=Order.Status.PENDING).count()
        context['recent_orders'] = Order.objects.order_by('-created_at')[:8]
    if user.has_perm('auth.view_user'):
        context['customer_total'] = get_user_model().objects.filter(is_staff=False, is_superuser=False).count()
    return context

_original_index = admin.site.index

def dashboard_index(request, extra_context=None):
    context = dashboard_context(request.user)
    context.update(extra_context or {})
    return _original_index(request, extra_context=context)

admin.site.index_template = 'admin/dashboard.html'
admin.site.site_header = 'Cocoa Bliss administration'
admin.site.site_title = 'Cocoa Bliss'
admin.site.index_title = 'Store overview'
admin.site.index = dashboard_index
