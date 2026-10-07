from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("login/", views.login_view, name="login"),
    path("register/", views.register_view, name="register"),
    path("logout/", views.logout_view, name="frontend_logout"),
    path("dashboard/", views.dashboard, name="frontend_dashboard"),
    path("customer/", views.customer_dashboard, name="customer_dashboard"),
    path("seller/", views.seller_dashboard, name="seller_dashboard"),
    path("admin-dashboard/", views.admin_dashboard, name="admin_dashboard"),
    path("products/", views.products, name="products"),
    path("products/<int:product_id>/", views.product_detail, name="product_detail"),
    path("cart/", views.cart_view, name="cart"),
    path("orders/", views.orders_view, name="orders"),
    path("notifications/", views.notifications_view, name="notifications"),
    path("profile/", views.profile_view, name="profile"),
    path("seller/products/", views.seller_products, name="seller_products"),
    path("seller/products/add/", views.seller_add_product, name="seller_add_product"),
    path("seller/products/<int:product_id>/edit/", views.seller_edit_product, name="seller_edit_product"),
    path("admin/users/", views.admin_users, name="admin_users"),
    path("admin/products/", views.admin_products, name="admin_products"),
    path("admin/orders/", views.admin_orders, name="admin_orders"),
    path("action/add-cart/", views.add_cart, name="add_cart"),
    path("action/remove-cart/<int:cart_id>/", views.remove_cart, name="remove_cart"),
    path("action/create-order/", views.create_order, name="create_order"),
    path("action/pay/<int:order_id>/", views.make_payment, name="make_payment"),
    path("action/cancel-item/", views.cancel_order_item, name="cancel_order_item"),
    path("action/read-notification/<int:notification_id>/", views.read_notification, name="read_notification"),
    path("action/order-status/<int:order_id>/", views.update_order_status, name="update_order_status"),
    path("action/delete-product/<int:product_id>/", views.delete_product, name="delete_product"),
    path("export/users/csv/", views.export_users_csv, name="export_users_csv"),
    path("export/products/csv/", views.export_products_csv, name="export_products_csv"),
    path("export/orders/csv/", views.export_orders_csv, name="export_orders_csv"),
    path("export/payments/csv/", views.export_payments_csv, name="export_payments_csv"),
    path(
    "export/orders/pdf/",
    views.export_orders_pdf,
    name="export_orders_pdf"
),

path(
    "export/sales/pdf/",
    views.export_sales_pdf,
    name="export_sales_pdf"
),

path(
    "export/analytics/pdf/",
    views.export_analytics_pdf,
    name="export_analytics_pdf"
),
]
