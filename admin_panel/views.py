from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render, redirect
from django.db.models import Count

from .models import User, Product, Order, Payment


@staff_member_required
def dashboard(request):

    # Only Django admin/staff users can reach this page

    # ==========================================
    # SUMMARY DATA
    # ==========================================

    total_users = User.objects.count()
    total_products = Product.objects.count()
    total_orders = Order.objects.count()
    total_payments = Payment.objects.count()

    # ==========================================
    # TOTAL SALES
    # ==========================================

    total_sales = 0

    successful_payments = Payment.objects.filter(
        status="Success"
    )

    for payment in successful_payments:
        total_sales += payment.amount

    # ==========================================
    # ORDER STATUS
    # ==========================================

    pending_orders = Order.objects.filter(
        order_status="Pending"
    ).count()

    shipped_orders = Order.objects.filter(
        order_status="Shipped"
    ).count()

    delivered_orders = Order.objects.filter(
        order_status="Delivered"
    ).count()

    cancelled_orders = Order.objects.filter(
        order_status="Cancelled"
    ).count()

    # ==========================================
    # SALES OVER TIME
    # ==========================================

    sales_data = {}

    for payment in successful_payments:

        month = payment.created_at.strftime("%b %Y")

        if month not in sales_data:
            sales_data[month] = 0

        sales_data[month] += float(payment.amount)

    sales_labels = list(sales_data.keys())
    sales_values = list(sales_data.values())

    # ==========================================
    # PRODUCTS BY CATEGORY
    # ==========================================

    category_data = (
        Product.objects
        .values("category")
        .annotate(total=Count("id"))
        .order_by("category")
    )

    category_labels = []
    category_values = []

    for item in category_data:
        category_labels.append(item["category"])
        category_values.append(item["total"])

    # ==========================================
    # PAYMENT STATUS
    # ==========================================

    payment_status_data = (
        Payment.objects
        .values("status")
        .annotate(total=Count("id"))
        .order_by("status")
    )

    payment_status_labels = []
    payment_status_values = []

    for item in payment_status_data:
        payment_status_labels.append(item["status"])
        payment_status_values.append(item["total"])

    # ==========================================
    # CONTEXT
    # ==========================================

    context = {

        "total_users": total_users,
        "total_products": total_products,
        "total_orders": total_orders,
        "total_payments": total_payments,
        "total_sales": total_sales,

        "pending_orders": pending_orders,
        "shipped_orders": shipped_orders,
        "delivered_orders": delivered_orders,
        "cancelled_orders": cancelled_orders,

        "sales_labels": sales_labels,
        "sales_values": sales_values,

        "category_labels": category_labels,
        "category_values": category_values,

        "payment_status_labels": payment_status_labels,
        "payment_status_values": payment_status_values,
    }

    return render(
        request,
        "admin_panel/dashboard.html",
        context
    )