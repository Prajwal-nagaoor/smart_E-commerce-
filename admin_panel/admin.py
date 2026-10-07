from django.contrib import admin

from .models import (
    User,
    Product,
    Cart,
    Order,
    OrderItem,
    Payment,
    Notification,
)


@admin.register(User)
class UserAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "name",
        "email",
        "role",
    )

    search_fields = (
        "name",
        "email",
    )

    list_filter = (
        "role",
    )


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "product_name",
        "category",
        "product_price",
        "stock",
        "popularity",
        "image",
        "created_at",
    )

    search_fields = (
        "product_name",
        "category",
    )

    list_filter = (
        "category",
        "popularity",
    )
    
    ordering = (
        "-created_at",
    )


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "user_id",
        "product_id",
        "quentity",
    )

    search_fields = (
        "user_id",
        "product_id",
    )


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "user_id",
        "total_amount",
        "payment_status",
        "order_status",
        "created_at",
    )

    search_fields = (
        "id",
        "user_id",
    )

    list_filter = (
        "payment_status",
        "order_status",
    )

    list_editable = (
        "payment_status",
        "order_status",
    )

    ordering = (
        "-created_at",
    )
@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "order_id",
        "product_id",
        "quantity",
        "price",
    )

    search_fields = (
        "order_id",
        "product_id",
    )


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "order_id",
        "amount",
        "payment_method",
        "transaction_id",
        "status",
        "created_at",
    )

    search_fields = (
        "order_id",
        "transaction_id",
    )

    list_filter = (
        "status",
        "payment_method",
    )

    list_editable = (
        "status",
    )

    ordering = (
        "-created_at",
    )

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "user_id",
        "type",
        "message",
        "is_read",
        "created_at",
    )

    search_fields = (
        "user_id",
        "type",
        "message",
    )

    list_filter = (
        "type",
        "is_read",
    )

    ordering = (
        "-created_at",
    )