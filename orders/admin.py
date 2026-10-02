from django.contrib import admin
from .models import Order, OrderItem, Payment

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    can_delete = False
    readonly_fields = ["product", "name", "price", "quantity"]
    def has_add_permission(self, request, obj=None):
        return False

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ["id", "full_name", "total", "currency", "status", "created_at"]
    list_filter = ["status", "created_at"]
    search_fields = ["email", "full_name"]
    readonly_fields = [field.name for field in Order._meta.fields]
    inlines = [OrderItemInline]
    def has_add_permission(self, request):
        return False
    def has_delete_permission(self, request, obj=None):
        return False

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ["order", "session_id", "paid_at"]
    readonly_fields = [field.name for field in Payment._meta.fields]
    def has_add_permission(self, request):
        return False
    def has_delete_permission(self, request, obj=None):
        return False
