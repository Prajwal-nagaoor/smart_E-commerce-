from django.db import models


class User(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=50)
    email = models.CharField(max_length=30, unique=True)
    password = models.CharField(max_length=255)
    role = models.CharField(max_length=10, default="customer")

    class Meta:
        managed = False
        db_table = "users"

    def __str__(self):
        return self.email


class Product(models.Model):
    id = models.IntegerField(primary_key=True)
    user_id = models.IntegerField()
    product_name = models.CharField(max_length=200)
    product_desc = models.CharField(max_length=400)
    product_price = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.CharField(max_length=200)
    stock = models.IntegerField(default=0)
    popularity = models.BooleanField(default=True)
    image = models.ImageField(
    upload_to="products/",
    null=True,
    blank=True
)
    created_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = "Product"

    

    def __str__(self):
        return self.product_name


class Cart(models.Model):
    id = models.IntegerField(primary_key=True)
    user_id = models.IntegerField()
    product_id = models.IntegerField()
    quentity = models.IntegerField()

    class Meta:
        managed = False
        db_table = "Cart"

    def __str__(self):
        return f"Cart {self.id}"


class Order(models.Model):
    id = models.IntegerField(primary_key=True)
    user_id = models.IntegerField()
    total_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )
    payment_status = models.CharField(
        max_length=200,
        default="Pending"
    )
    order_status = models.CharField(
        max_length=200,
        default="Pending"
    )
    created_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = "Orders"

    def __str__(self):
        return f"Order #{self.id}"


class OrderItem(models.Model):
    id = models.IntegerField(primary_key=True)
    order_id = models.IntegerField()
    product_id = models.IntegerField()
    quantity = models.IntegerField()
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    class Meta:
        managed = False
        db_table = "orderitem"

    def __str__(self):
        return f"Order Item {self.id}"


class Payment(models.Model):
    id = models.IntegerField(primary_key=True)
    order_id = models.IntegerField()
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )
    payment_method = models.CharField(max_length=200)
    transaction_id = models.CharField(
        max_length=200,
        null=True,
        blank=True
    )
    status = models.CharField(
        max_length=200,
        default="Pending"
    )
    created_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = "payments"

    def __str__(self):
        return f"Payment #{self.id}"


class Notification(models.Model):
    id = models.IntegerField(primary_key=True)
    user_id = models.IntegerField()
    type = models.CharField(max_length=100)
    message = models.CharField(max_length=500)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = "notifications"

    def __str__(self):
        return self.message