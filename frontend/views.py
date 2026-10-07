import os
import csv
from decimal import Decimal
from functools import wraps
from urllib.parse import quote

import requests
from django.conf import settings
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Count, Sum, F
from django.http import JsonResponse, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods, require_POST

from admin_panel.models import User, Product, Cart, Order, OrderItem, Payment, Notification

from io import BytesIO
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

FASTAPI_BASE_URL = os.getenv("FASTAPI_BASE_URL", "http://127.0.0.1:8000").rstrip("/")


def api_request(path, method="GET", token=None, **kwargs):
    headers = kwargs.pop("headers", {})
    if token:
        headers["Authorization"] = f"Bearer {token}"
    try:
        response = requests.request(method, FASTAPI_BASE_URL + path, headers=headers, timeout=20, **kwargs)
        try:
            data = response.json()
        except ValueError:
            data = {"detail": response.text or "Request failed"}
        return response.status_code, data
    except requests.RequestException as exc:
        return 503, {"detail": f"FastAPI is not reachable: {exc}"}


def current_user(request):
    user_id = request.session.get("user_id")
    if not user_id:
        return None
    try:
        return User.objects.filter(id=user_id).first()
    except Exception:
        return None


def image_url(product):
    name = str(product.image or "")
    name = name.replace("\\", "/")
    if name.startswith("media/"):
        name = name[6:]
    if not name:
        return ""
    return settings.MEDIA_URL + name.lstrip("/")


def product_cards(queryset):
    return [{"obj": p, "image_url": image_url(p)} for p in queryset]


def login_required(view):
    @wraps(view)
    def wrapper(request, *args, **kwargs):
        if not request.session.get("access_token"):
            return redirect("login")
        return view(request, *args, **kwargs)
    return wrapper


def role_required(*roles):
    def decorator(view):
        @wraps(view)
        @login_required
        def wrapper(request, *args, **kwargs):
            role = str(request.session.get("role", "")).upper()
            if role not in roles:
                messages.error(request, "You do not have permission to access this page.")
                return redirect("frontend_dashboard")
            return view(request, *args, **kwargs)
        return wrapper
    return decorator


def common_context(request, **extra):
    user = current_user(request)
    unread = 0
    cart_count = 0
    if user:
        unread = Notification.objects.filter(user_id=user.id, is_read=False).count()
        cart_count = Cart.objects.filter(user_id=user.id).aggregate(total=Sum("quentity"))["total"] or 0
    return {"current_user": user, "unread_count": unread, "cart_count": cart_count, **extra}


def home(request):
    return redirect("frontend_dashboard") if request.session.get("access_token") else redirect("login")


def login_view(request):
    if request.session.get("access_token"):
        return redirect("frontend_dashboard")
    if request.method == "POST":
        status, data = api_request("/login", "POST", json={"email": request.POST.get("email", "").strip(), "password": request.POST.get("password", "")})
        if status == 200:
            request.session["access_token"] = data.get("Access Token") or data.get("access_token")
            request.session["user_id"] = data.get("user_id") or data.get("user", {}).get("id")
            request.session["name"] = data.get("user") or data.get("user", {}).get("name") or "User"
            request.session["email"] = data.get("Email") or data.get("user", {}).get("email")
            request.session["role"] = str(data.get("Role") or data.get("role") or data.get("user", {}).get("role") or "customer").upper()
            request.session.set_expiry(60 * 60)
            messages.success(request, f"Welcome back, {request.session['name']}!")
            return redirect("frontend_dashboard")
        messages.error(request, data.get("detail", "Invalid email or password."))
    return render(request, "frontend/login.html", {"title": "Sign in"})


def register_view(request):
    if request.session.get("access_token"):
        return redirect("frontend_dashboard")
    if request.method == "POST":
        payload = {"name": request.POST.get("name", "").strip(), "email": request.POST.get("email", "").strip(), "password": request.POST.get("password", ""), "role": "customer"}
        if payload["password"] != request.POST.get("confirm_password", ""):
            messages.error(request, "Passwords do not match.")
        else:
            status, data = api_request("/register", "POST", json=payload)
            if status in (200, 201):
                messages.success(request, "Account created successfully. Please sign in.")
                return redirect("login")
            messages.error(request, data.get("detail", "Registration failed."))
    return render(request, "frontend/register.html", {"title": "Create account"})


def logout_view(request):
    token = request.session.get("access_token")
    if token:
        api_request("/logout", "POST", token=token)
    request.session.flush()
    messages.success(request, "You have been logged out safely.")
    return redirect("login")


@login_required
def dashboard(request):
    role = str(request.session.get("role", "customer")).upper()
    if role == "ADMIN":
        return redirect("admin_dashboard")
    if role == "SELLER":
        return redirect("seller_dashboard")
    return redirect("customer_dashboard")


@role_required("CUSTOMER", "USER")
def customer_dashboard(request):
    user = current_user(request)
    products = Product.objects.all().order_by("-created_at")[:8]
    orders = Order.objects.filter(user_id=user.id).order_by("-created_at")[:5]
    context = common_context(request, title="Customer Dashboard", products=product_cards(products), orders=orders, order_count=Order.objects.filter(user_id=user.id).count())
    return render(request, "frontend/customer_dashboard.html", context)


@role_required("SELLER")
def seller_dashboard(request):
    user = current_user(request)
    products = Product.objects.filter(user_id=user.id).order_by("-created_at")
    product_ids = list(products.values_list("id", flat=True))
    order_ids = list(OrderItem.objects.filter(product_id__in=product_ids).values_list("order_id", flat=True))
    seller_orders = Order.objects.filter(id__in=order_ids).order_by("-created_at")
    revenue = OrderItem.objects.filter(product_id__in=product_ids).aggregate(total=Sum(F("price") * F("quantity")))["total"] or Decimal("0")
    low_stock = products.filter(stock__lte=5).count()
    context = common_context(request, title="Seller Dashboard", products=product_cards(products[:8]), product_count=products.count(), low_stock=low_stock, seller_orders=seller_orders[:8], seller_order_count=seller_orders.count(), revenue=revenue)
    return render(request, "frontend/seller_dashboard.html", context)


@role_required("ADMIN")
def admin_dashboard(request):
    total_sales = Payment.objects.filter(status__iexact="success").aggregate(total=Sum("amount"))["total"] or Decimal("0")
    order_status = {x["order_status"]: x["total"] for x in Order.objects.values("order_status").annotate(total=Count("id"))}
    categories = list(Product.objects.values("category").annotate(total=Count("id")).order_by("category"))
    payments = list(Payment.objects.values("status").annotate(total=Count("id")).order_by("status"))
    sales = list(Payment.objects.filter(status__iexact="success").values("created_at").order_by("created_at"))
    context = common_context(request, title="Admin Dashboard", total_users=User.objects.count(), total_products=Product.objects.count(), total_orders=Order.objects.count(), total_payments=Payment.objects.count(), total_sales=total_sales, pending=order_status.get("Pending", 0), shipped=order_status.get("Shipped", 0), delivered=order_status.get("Delivered", 0), cancelled=order_status.get("Cancelled", 0), categories=categories, payments=payments, recent_orders=Order.objects.order_by("-created_at")[:8])
    return render(request, "frontend/admin_dashboard.html", context)


@login_required
def products(request):
    qs = Product.objects.all().order_by("-created_at")
    search = request.GET.get("q", "").strip()
    category = request.GET.get("category", "").strip()
    sort = request.GET.get("sort", "latest")
    if search:
        qs = qs.filter(product_name__icontains=search)
    if category:
        qs = qs.filter(category__icontains=category)
    if sort == "price_low": qs = qs.order_by("product_price")
    elif sort == "price_high": qs = qs.order_by("-product_price")
    elif sort == "popular": qs = qs.filter(popularity=True).order_by("-created_at")
    paginator = Paginator(qs, 12)
    page = paginator.get_page(request.GET.get("page"))
    categories = Product.objects.values_list("category", flat=True).distinct().order_by("category")
    return render(request, "frontend/products.html", common_context(request, title="Shop", products=product_cards(page.object_list), page=page, categories=categories, search=search, selected_category=category, sort=sort))


@login_required
def product_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    related = Product.objects.filter(category=product.category).exclude(id=product.id).order_by("-created_at")[:4]
    return render(request, "frontend/product_detail.html", common_context(request, title=product.product_name, product=product, product_image=image_url(product), related=product_cards(related)))


@role_required("CUSTOMER", "USER")
def cart_view(request):
    user = current_user(request)

    items = list(
        Cart.objects
        .filter(user_id=user.id)
        .order_by("id")
    )

    rows = []
    total = Decimal("0")

    for item in items:
        product = Product.objects.filter(id=item.product_id).first()

        if not product:
            continue

        subtotal = product.product_price * item.quentity
        total += subtotal

        rows.append({
            "item": item,
            "product": product,
            "subtotal": subtotal,
            "image_url": image_url(product),
        })

    return render(
        request,
        "frontend/cart.html",
        common_context(
            request,
            title="Your Cart",
            cart_items=rows,
            cart_total=total
        )
    )


@role_required("CUSTOMER", "USER")
def orders_view(request):
    user = current_user(request)

    orders = list(
        Order.objects
        .filter(user_id=user.id)
        .order_by("-created_at")
    )

    for order in orders:
        order_items = OrderItem.objects.filter(order_id=order.id).order_by("id")

        items_display = []

        for item in order_items:
            product = Product.objects.filter(id=item.product_id).first()

            if product:
                item.product = product
                items_display.append(item)

        order.items_display = items_display

    return render(
        request,
        "frontend/orders.html",
        common_context(
            request,
            title="My Orders",
            orders=orders
        )
    )


@role_required("CUSTOMER", "USER")
def notifications_view(request):
    user = current_user(request)
    notifications = Notification.objects.filter(user_id=user.id).order_by("-created_at")
    return render(request, "frontend/notifications.html", common_context(request, title="Notifications", notifications=notifications))


@login_required
def profile_view(request):
    user = current_user(request)
    if request.method == "POST":
        payload = {"name": request.POST.get("name", "").strip(), "email": request.POST.get("email", "").strip(), "password": request.POST.get("password", ""), "role": user.role}
        status, data = api_request(f"/update-profile/{user.id}", "PUT", token=request.session.get("access_token"), json=payload)
        if status == 200:
            request.session["name"] = payload["name"]
            request.session["email"] = payload["email"]
            messages.success(request, "Profile updated successfully.")
            return redirect("profile")
        messages.error(request, data.get("detail", "Unable to update profile."))
    return render(request, "frontend/profile.html", common_context(request, title="Profile", profile=user))


@role_required("SELLER")
def seller_products(request):
    user = current_user(request)
    products = Product.objects.filter(user_id=user.id).order_by("-created_at")
    return render(request, "frontend/seller_products.html", common_context(request, title="My Products", products=product_cards(products)))


@role_required("SELLER")
def seller_add_product(request):
    if request.method == "POST":

        uploaded_image = request.FILES.get("image")

        if not uploaded_image:
            messages.error(request, "Please select a product image.")
            return render(
                request,
                "frontend/seller_product_form.html",
                common_context(
                    request,
                    title="Add Product",
                    editing=False
                )
            )

        # Get the correct MIME type
        content_type = uploaded_image.content_type

        if not content_type or not content_type.startswith("image/"):
            messages.error(
                request,
                f"Invalid image type: {content_type}. Please select a PNG, JPG or JPEG image."
            )
            return render(
                request,
                "frontend/seller_product_form.html",
                common_context(
                    request,
                    title="Add Product",
                    editing=False
                )
            )

        # Send the file to FastAPI with filename + MIME type explicitly
        files = {
            "image": (
                uploaded_image.name,
                uploaded_image.file,
                content_type
            )
        }

        data = {
            "product_name": request.POST.get("product_name", "").strip(),
            "product_desc": request.POST.get("product_desc", "").strip(),
            "product_price": request.POST.get("product_price"),
            "category": request.POST.get("category", "").strip(),
            "stock": request.POST.get("stock"),
            "popularity": request.POST.get("popularity", "false")
        }

        status, result = api_request(
            "/products/create-product",
            "POST",
            token=request.session.get("access_token"),
            data=data,
            files=files
        )

        if status in (200, 201):
            messages.success(
                request,
                "Product added successfully."
            )
            return redirect("seller_products")

        messages.error(
            request,
            result.get(
                "detail",
                "Could not create product."
            )
        )

    return render(
        request,
        "frontend/seller_product_form.html",
        common_context(
            request,
            title="Add Product",
            editing=False
        )
    )

@role_required("SELLER", "ADMIN")
def seller_edit_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    if str(request.session.get("role", "")).upper() == "SELLER" and product.user_id != request.session.get("user_id"):
        messages.error(request, "You can edit only your own products.")
        return redirect("seller_products")
    if request.method == "POST":
        payload = {"product_name": request.POST.get("product_name"), "product_desc": request.POST.get("product_desc"), "product_price": request.POST.get("product_price"), "category": request.POST.get("category"), "stock": request.POST.get("stock"), "popularity": request.POST.get("popularity") == "on"}
        status, result = api_request(f"/products/edit_product/{product_id}", "PUT", token=request.session.get("access_token"), json=payload)
        if status == 200:
            messages.success(request, "Product updated successfully.")
            return redirect("seller_products" if request.session.get("role") == "SELLER" else "admin_products")
        messages.error(request, result.get("detail", "Could not update product."))
    return render(request, "frontend/seller_product_form.html", common_context(request, title="Edit Product", editing=True, product=product, product_image=image_url(product)))


@role_required("ADMIN")
def admin_users(request):
    if request.method == "POST":
        action = request.POST.get("action")
        user_id = int(request.POST.get("user_id"))
        if user_id == request.session.get("user_id"):
            messages.error(request, "You cannot change or delete your own admin account here.")
            return redirect("admin_users")
        user = get_object_or_404(User, id=user_id)
        if action == "role":
            new_role = request.POST.get("role", "customer").upper()
            if new_role not in {"CUSTOMER", "SELLER", "ADMIN"}:
                messages.error(request, "Invalid role.")
            else:
                user.role = new_role
                user.save(update_fields=["role"])
                messages.success(request, f"{user.name}'s role was updated to {new_role}.")
        elif action == "delete":
            try:
                user.delete()
                messages.success(request, "User deleted successfully.")
            except Exception as exc:
                messages.error(request, f"Unable to delete user because related records exist: {exc}")
        return redirect("admin_users")
    users = User.objects.all().order_by("id")
    return render(request, "frontend/admin_users.html", common_context(request, title="Users", users=users))


@role_required("ADMIN")
def admin_products(request):
    products = Product.objects.all().order_by("-created_at")
    return render(request, "frontend/admin_products.html", common_context(request, title="Products", products=product_cards(products)))


@role_required("ADMIN")
def admin_orders(request):
    orders = Order.objects.all().order_by("-created_at")
    return render(request, "frontend/admin_orders.html", common_context(request, title="Orders", orders=orders))

@role_required("ADMIN")
def export_users_csv(request):
    users = User.objects.all().order_by("id")

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="users.csv"'

    writer = csv.writer(response)

    writer.writerow([
        "User ID",
        "Name",
        "Email",
        "Role",
    ])

    for user in users:
        writer.writerow([
            user.id,
            user.name,
            user.email,
            user.role,
        ])

    return response


@role_required("ADMIN")
def export_products_csv(request):
    products = Product.objects.all().order_by("id")

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="products.csv"'

    writer = csv.writer(response)

    writer.writerow([
        "Product ID",
        "Product Name",
        "Description",
        "Price",
        "Category",
        "Stock",
        "Popularity",
        "Created At",
    ])

    for product in products:
        writer.writerow([
            product.id,
            product.product_name,
            product.product_desc,
            product.product_price,
            product.category,
            product.stock,
            product.popularity,
            product.created_at.strftime("%Y-%m-%d %H:%M:%S"),
        ])

    return response


@role_required("ADMIN")
def export_orders_csv(request):
    orders = Order.objects.all().order_by("-created_at")

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="orders.csv"'

    writer = csv.writer(response)

    writer.writerow([
        "Order ID",
        "User ID",
        "Total Amount",
        "Payment Status",
        "Order Status",
        "Created At",
    ])

    for order in orders:
        writer.writerow([
            order.id,
            order.user_id,
            order.total_amount,
            order.payment_status,
            order.order_status,
            order.created_at.strftime("%Y-%m-%d %H:%M:%S"),
        ])

    return response


@role_required("ADMIN")
def export_payments_csv(request):
    payments = Payment.objects.all().order_by("-created_at")

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="payments.csv"'

    writer = csv.writer(response)

    writer.writerow([
        "Payment ID",
        "Order ID",
        "Amount",
        "Payment Method",
        "Transaction ID",
        "Status",
        "Created At",
    ])

    for payment in payments:
        writer.writerow([
            payment.id,
            payment.order_id,
            payment.amount,
            payment.payment_method,
            payment.transaction_id or "",
            payment.status,
            payment.created_at.strftime("%Y-%m-%d %H:%M:%S"),
        ])

    return response
@role_required("ADMIN")
def export_orders_pdf(request):

    orders = Order.objects.all().order_by("-created_at")

    buffer = BytesIO()

    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=15 * mm,
        leftMargin=15 * mm,
        topMargin=15 * mm,
        bottomMargin=15 * mm,
    )

    styles = getSampleStyleSheet()

    elements = []

    elements.append(
        Paragraph(
            "SmartCart - Orders Report",
            styles["Title"]
        )
    )

    elements.append(
        Paragraph(
            "Complete order report",
            styles["Normal"]
        )
    )

    elements.append(Spacer(1, 10))

    data = [
        [
            "Order ID",
            "User ID",
            "Amount",
            "Payment",
            "Status",
            "Date",
        ]
    ]

    for order in orders:
        data.append([
            str(order.id),
            str(order.user_id),
            f"Rs. {order.total_amount}",
            str(order.payment_status),
            str(order.order_status),
            order.created_at.strftime("%d-%m-%Y"),
        ])

    table = Table(
        data,
        repeatRows=1,
        colWidths=[
            20 * mm,
            20 * mm,
            30 * mm,
            30 * mm,
            30 * mm,
            30 * mm,
        ],
    )

    table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#5948d5")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [
                colors.white,
                colors.HexColor("#f7f7fb"),
            ]),
        ])
    )

    elements.append(table)

    document.build(elements)

    buffer.seek(0)

    response = HttpResponse(
        buffer.getvalue(),
        content_type="application/pdf"
    )

    response["Content-Disposition"] = (
        'attachment; filename="orders_report.pdf"'
    )

    return response
@role_required("ADMIN")
def export_sales_pdf(request):

    payments = Payment.objects.filter(
        status__iexact="success"
    ).order_by("-created_at")

    total_sales = (
        payments.aggregate(total=Sum("amount"))["total"]
        or Decimal("0")
    )

    buffer = BytesIO()

    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=15 * mm,
        leftMargin=15 * mm,
        topMargin=15 * mm,
        bottomMargin=15 * mm,
    )

    styles = getSampleStyleSheet()

    elements = []

    elements.append(
        Paragraph(
            "SmartCart - Sales Report",
            styles["Title"]
        )
    )

    elements.append(Spacer(1, 8))

    elements.append(
        Paragraph(
            f"Total Successful Sales: Rs. {total_sales}",
            styles["Heading2"]
        )
    )

    elements.append(Spacer(1, 12))

    data = [
        [
            "Payment ID",
            "Order ID",
            "Amount",
            "Method",
            "Transaction ID",
            "Date",
        ]
    ]

    for payment in payments:
        data.append([
            str(payment.id),
            str(payment.order_id),
            f"Rs. {payment.amount}",
            str(payment.payment_method),
            str(payment.transaction_id or "-"),
            payment.created_at.strftime("%d-%m-%Y"),
        ])

    table = Table(
        data,
        repeatRows=1,
        colWidths=[
            20 * mm,
            20 * mm,
            25 * mm,
            30 * mm,
            45 * mm,
            25 * mm,
        ],
    )

    table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#5948d5")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 7),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [
                colors.white,
                colors.HexColor("#f7f7fb"),
            ]),
        ])
    )

    elements.append(table)

    document.build(elements)

    buffer.seek(0)

    response = HttpResponse(
        buffer.getvalue(),
        content_type="application/pdf"
    )

    response["Content-Disposition"] = (
        'attachment; filename="sales_report.pdf"'
    )

    return response
@role_required("ADMIN")
def export_analytics_pdf(request):

    total_users = User.objects.count()
    total_products = Product.objects.count()
    total_orders = Order.objects.count()
    total_payments = Payment.objects.count()

    total_sales = (
        Payment.objects
        .filter(status__iexact="success")
        .aggregate(total=Sum("amount"))["total"]
        or Decimal("0")
    )

    order_status = {
        item["order_status"]: item["total"]
        for item in (
            Order.objects
            .values("order_status")
            .annotate(total=Count("id"))
        )
    }

    categories = (
        Product.objects
        .values("category")
        .annotate(total=Count("id"))
        .order_by("category")
    )

    payment_status = (
        Payment.objects
        .values("status")
        .annotate(total=Count("id"))
        .order_by("status")
    )

    buffer = BytesIO()

    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=20 * mm,
        leftMargin=20 * mm,
        topMargin=20 * mm,
        bottomMargin=20 * mm,
    )

    styles = getSampleStyleSheet()

    elements = []

    elements.append(
        Paragraph(
            "SmartCart - Analytics Report",
            styles["Title"]
        )
    )

    elements.append(Spacer(1, 15))

    elements.append(
        Paragraph(
            "Business Summary",
            styles["Heading2"]
        )
    )

    summary_data = [
        ["Metric", "Value"],
        ["Total Users", str(total_users)],
        ["Total Products", str(total_products)],
        ["Total Orders", str(total_orders)],
        ["Total Payments", str(total_payments)],
        ["Total Successful Sales", f"Rs. {total_sales}"],
    ]

    summary_table = Table(
        summary_data,
        colWidths=[90 * mm, 60 * mm],
    )

    summary_table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#5948d5")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [
                colors.white,
                colors.HexColor("#f7f7fb"),
            ]),
        ])
    )

    elements.append(summary_table)

    elements.append(Spacer(1, 20))

    # Order Status

    elements.append(
        Paragraph(
            "Order Status",
            styles["Heading2"]
        )
    )

    order_data = [
        ["Status", "Orders"]
    ]

    for status, count in order_status.items():
        order_data.append([
            str(status),
            str(count),
        ])

    order_table = Table(
        order_data,
        colWidths=[90 * mm, 60 * mm],
    )

    order_table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#5948d5")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
        ])
    )

    elements.append(order_table)

    elements.append(Spacer(1, 20))

    # Products by Category

    elements.append(
        Paragraph(
            "Products by Category",
            styles["Heading2"]
        )
    )

    category_data = [
        ["Category", "Products"]
    ]

    for item in categories:
        category_data.append([
            str(item["category"]),
            str(item["total"]),
        ])

    category_table = Table(
        category_data,
        colWidths=[90 * mm, 60 * mm],
    )

    category_table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#5948d5")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
        ])
    )

    elements.append(category_table)

    elements.append(Spacer(1, 20))

    # Payment Status

    elements.append(
        Paragraph(
            "Payment Status",
            styles["Heading2"]
        )
    )

    payment_data = [
        ["Status", "Payments"]
    ]

    for item in payment_status:
        payment_data.append([
            str(item["status"]),
            str(item["total"]),
        ])

    payment_table = Table(
        payment_data,
        colWidths=[90 * mm, 60 * mm],
    )

    payment_table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#5948d5")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
        ])
    )

    elements.append(payment_table)

    document.build(elements)

    buffer.seek(0)

    response = HttpResponse(
        buffer.getvalue(),
        content_type="application/pdf"
    )

    response["Content-Disposition"] = (
        'attachment; filename="analytics_report.pdf"'
    )

    return response
@require_POST
@role_required("CUSTOMER", "USER")
def add_cart(request):
    status, data = api_request("/cart/add-cart/", "POST", token=request.session.get("access_token"), json={"product_id": int(request.POST.get("product_id")), "quantity": int(request.POST.get("quantity", 1))})
    if status in (200, 201): messages.success(request, "Product added to cart.")
    else: messages.error(request, data.get("detail", "Unable to add product to cart."))
    return redirect(request.POST.get("next") or "products")


@require_POST
@role_required("CUSTOMER", "USER")
def remove_cart(request, cart_id):
    status, data = api_request(f"/cart/delete-cart/{cart_id}", "DELETE", token=request.session.get("access_token"))
    messages.success(request, "Item removed from cart.") if status == 200 else messages.error(request, data.get("detail", "Unable to remove item."))
    return redirect("cart")


@require_POST
@role_required("CUSTOMER", "USER")
def create_order(request):
    status, data = api_request("/orders/create-order", "POST", token=request.session.get("access_token"))
    if status in (200, 201):
        messages.success(request, f"Order #{data.get('id')} created successfully.")
        return redirect("orders")
    messages.error(request, data.get("detail", "Unable to create order."))
    return redirect("cart")


@require_POST
@role_required("CUSTOMER", "USER")
def make_payment(request, order_id):
    status, data = api_request(
        "/orders/make-payment",
        "POST",
        token=request.session.get("access_token"),
        json={
            "order_id": order_id,
            "payment_method": "Stripe",
            "transaction_id": None,
            "status": "Pending"
        }
    )

    if status in (200, 201):
        client_secret = data.get("client_secret")
        amount = data.get("amount")

        if not client_secret:
            messages.error(
                request,
                "Payment was created but Stripe client secret was not returned."
            )
            return redirect("orders")

        request.session["payment_client_secret"] = client_secret
        request.session["payment_order_id"] = order_id

        return render(
            request,
            "frontend/payment.html",
            common_context(
                request,
                title="Secure Payment",
                order_id=order_id,
                amount=amount,
                client_secret=client_secret,
                stripe_publishable_key=settings.STRIPE_PUBLISHABLE_KEY
            )
        )

    messages.error(
        request,
        data.get("detail", "Unable to start payment.")
    )

    return redirect("orders")


@require_POST
@role_required("CUSTOMER", "USER")
def cancel_order_item(request):
    status, data = api_request("/orders/delete-order", "DELETE", token=request.session.get("access_token"), params={"order_id": request.POST.get("order_id"), "product_id": request.POST.get("product_id")})
    messages.success(request, "Order item cancelled and stock restored.") if status == 200 else messages.error(request, data.get("detail", "Unable to cancel item."))
    return redirect("orders")


@require_POST
@login_required
def read_notification(request, notification_id):
    status, data = api_request(f"/orders/mark-read/{notification_id}", "PUT", token=request.session.get("access_token"))
    messages.success(request, "Notification marked as read.") if status == 200 else messages.error(request, data.get("detail", "Unable to update notification."))
    return redirect("notifications")


@require_POST
@role_required("ADMIN")
def update_order_status(request, order_id):
    status_value = request.POST.get("status")
    status, data = api_request(f"/orders/update-order-status/{order_id}", "PUT", token=request.session.get("access_token"), params={"status": status_value})
    messages.success(request, "Order status updated.") if status == 200 else messages.error(request, data.get("detail", "Unable to update order status."))
    return redirect("admin_orders")


@require_POST
@role_required("SELLER", "ADMIN")
def delete_product(request, product_id):
    status, data = api_request(f"/products/delete-product/{product_id}", "DELETE", token=request.session.get("access_token"))
    messages.success(request, "Product deleted.") if status == 200 else messages.error(request, data.get("detail", "Unable to delete product."))
    return redirect("seller_products" if str(request.session.get("role")).upper() == "SELLER" else "admin_products")


