from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render

from .models import (
    User,
    Product,
    Order,
    Payment,
)


@staff_member_required
def dashboard(request):

    total_users = User.objects.count()

    total_products = Product.objects.count()

    total_orders = Order.objects.count()

    total_payments = Payment.objects.count()

    total_sales = 0

    for payment in Payment.objects.filter(status="Success"):
        total_sales += payment.amount

    pending_orders = Order.objects.filter(
        order_status="Pending"
    ).count()

    shipped_orders = Order.objects.filter(
        order_status="Shipped"
    ).count()

    delivered_orders = Order.objects.filter(
        order_status="Delivered"
    ).count()

    context = {
        "total_users": total_users,
        "total_products": total_products,
        "total_orders": total_orders,
        "total_payments": total_payments,
        "total_sales": total_sales,
        "pending_orders": pending_orders,
        "shipped_orders": shipped_orders,
        "delivered_orders": delivered_orders,
    }

    return render(
        request,
        "admin_panel/dashboard.html",
        context
    )