from django.contrib import admin
from .models import Category, Product, ProductImage
class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ["name", "price", "active", "featured", "is_gift_box"]
    list_filter = ["active", "category", "is_gift_box"]
    search_fields = ["name"]
    prepopulated_fields = {"slug": ("name",)}
    inlines = [ProductImageInline]
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ("name",)}
