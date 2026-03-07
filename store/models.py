from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from simple_history.models import HistoricalRecords, settings

from django.contrib.auth.models import User
from django.utils.text import slugify
import uuid

# User Manager
class UserManager(BaseUserManager):
    # use_in_migrations = True
    def create_user(self, email, username, phone, password=None):
        if not email:
            raise ValueError("Email is required")
        if not username:
            raise ValueError("Username is required")
        if not phone:
            raise ValueError("Phone number is required")

        user = self.model(
            email=self.normalize_email(email),
            username=username,
            phone=phone
        )

        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, username, phone, password=None):
        user = self.create_user(email, username, phone, password)
        user.is_active = True
        user.is_superuser = True
        user.is_staff = True
        user.save(using=self._db)
        return user


# Role Model
class Role(models.Model):
    ROLE_CATEGORIES = [
        ("admin", "Admin"),
        ("staff", "Staff"),
        ("customer", "Customer"),
    ]
    
    role_name = models.CharField(max_length=100, unique=True)
    role_category = models.CharField(max_length=100, choices=ROLE_CATEGORIES, default="customer")
    created_at = models.DateTimeField(auto_now_add=True)

    history = HistoricalRecords()

    def __str__(self):
        return self.role_name

    class Meta:
        db_table = 'role'




#  User Model with Role
class Users(AbstractBaseUser, PermissionsMixin):
    first_name = models.CharField(max_length=100, blank=True, null=True)
    last_name = models.CharField(max_length=100, blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True, unique=True)
    email = models.EmailField(max_length=100, blank=True, null=True, unique=True)
    username = models.CharField(max_length=100, unique=True, blank=False, null=False)
    profile_image = models.ImageField(upload_to='profile_img/', blank=True, null=True)
    firebase_id = models.TextField(blank=True, null=True, default=None)
    date_of_birth = models.DateField(blank=True, null=True, default=None)
    
    address = models.TextField(blank=True, null=True, default=None)
    city = models.CharField(blank=True, null=True, default=None)
    district = models.CharField(blank=True, null=True, default=None)
    state = models.CharField(blank=True, null=True, default=None)
    pincode = models.IntegerField(blank=True, null=True, default=None)
   
    otp = models.IntegerField(blank=True, null=True,default=None)
    role = models.ForeignKey(Role, on_delete=models.SET_NULL, null=True, blank=True, related_name="users")
    
    is_active = models.BooleanField(default=True)
    is_superuser = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username", "phone"]

    objects = UserManager()
    history = HistoricalRecords()

    def __str__(self):
        return self.username

    class Meta:
        db_table = 'users'


# User Role Assignment Model (Many-to-Many)
class UserRole(models.Model):
    user = models.ForeignKey(Users, on_delete=models.CASCADE, related_name="user_roles")
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name="role_users")
    created_by = models.ForeignKey(Users, on_delete=models.SET_NULL, null=True, related_name="created_roles")
    created_at = models.DateTimeField(auto_now_add=True)

    history = HistoricalRecords()

    def __str__(self):
        return f"{self.user.username} - {self.role.role_name}"

    class Meta:
        db_table = 'user_role'
        unique_together = ("user", "role")








class Fabric(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

class Color(models.Model):
    name = models.CharField(max_length=50)
    hex_code = models.CharField(max_length=7, default="#000000")

    def __str__(self):
        return self.name

class Category(models.Model):
    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True, default="")
    image = models.ImageField(upload_to="categories/", null=True, blank=True)
    status = models.CharField(max_length=20, choices=[("active", "Active"), ("inactive", "Inactive")], default="active")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "categories"
        ordering = ["name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

class SubCategory(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="subcategories")
    name = models.CharField(max_length=200)
    slug = models.SlugField()

    class Meta:
        verbose_name_plural = "subcategories"
        unique_together = ("category", "slug")

    def __str__(self):
        return f"{self.category.name} → {self.name}"

class Product(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=300)
    slug = models.SlugField(unique=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    original_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    description = models.TextField(blank=True, default="")
    short_description = models.CharField(max_length=500, blank=True, default="")
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name="products")
    subcategory = models.ForeignKey(SubCategory, on_delete=models.SET_NULL, null=True, blank=True, related_name="products")
    colors = models.ManyToManyField(Color, blank=True)
    sizes = models.JSONField(default=list)  # ["S", "M", "L", "XL"]
    fabric = models.ForeignKey(Fabric, on_delete=models.SET_NULL, null=True, blank=True)
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=0)
    review_count = models.PositiveIntegerField(default=0)
    is_new = models.BooleanField(default=False)
    is_featured = models.BooleanField(default=False)
    in_stock = models.BooleanField(default=True)
    stock = models.PositiveIntegerField(default=0)
    sku = models.CharField(max_length=50, unique=True)
    status = models.CharField(max_length=20, choices=[("active", "Active"), ("draft", "Draft"), ("archived", "Archived")], default="active")
    meta_title = models.CharField(max_length=200, blank=True, default="")
    meta_description = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    @property
    def primary_image(self):
        img = self.images.first()
        return img.image.url if img else None

class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField(upload_to="products/")
    alt_text = models.CharField(max_length=200, blank=True, default="")
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return f"Image for {self.product.name}"

class Order(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("confirmed", "Confirmed"),
        ("processing", "Processing"),
        ("shipped", "Shipped"),
        ("delivered", "Delivered"),
        ("cancelled", "Cancelled"),
    ]
    PAYMENT_STATUS_CHOICES = [
        ("pending", "Pending"),
        ("paid", "Paid"),
        ("failed", "Failed"),
        ("refunded", "Refunded"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="orders")
    order_number = models.CharField(max_length=20, unique=True, editable=False)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default="pending")
    total = models.DecimalField(max_digits=10, decimal_places=2)
    shipping_address = models.TextField()
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    pincode = models.CharField(max_length=10)
    phone = models.CharField(max_length=15)
    tracking_number = models.CharField(max_length=100, blank=True, default="")
    coupon_code = models.CharField(max_length=50, blank=True, default="")
    razorpay_order_id = models.CharField(max_length=100, blank=True, default="")
    razorpay_payment_id = models.CharField(max_length=100, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.order_number

    def save(self, *args, **kwargs):
        if not self.order_number:
            import random, string
            self.order_number = "ORD-" + "".join(random.choices(string.digits, k=8))
        super().save(*args, **kwargs)

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
    product_name = models.CharField(max_length=300)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    size = models.CharField(max_length=20, blank=True, default="")
    color = models.CharField(max_length=50, blank=True, default="")

    def __str__(self):
        return f"{self.product_name} x{self.quantity}"

class Coupon(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=50, unique=True)
    type = models.CharField(max_length=20, choices=[("percentage", "Percentage"), ("fixed", "Fixed")])
    value = models.DecimalField(max_digits=10, decimal_places=2)
    min_order = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    max_uses = models.PositiveIntegerField(default=0)
    used_count = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=20, choices=[("active", "Active"), ("inactive", "Inactive")], default="active")
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    description = models.TextField(blank=True, default="")

    def __str__(self):
        return self.code

    @property
    def is_valid(self):
        from django.utils import timezone
        now = timezone.now()
        return (
            self.status == "active"
            and self.start_date <= now <= self.end_date
            and (self.max_uses == 0 or self.used_count < self.max_uses)
        )

class Wishlist(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="wishlist")
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "product")

    def __str__(self):
        return f"{self.user.username} → {self.product.name}"
