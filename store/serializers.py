from rest_framework import serializers
from django.db import models
from .models import Users
from .models import *

# ── Auth ──────────────────────────────────────────────

# ── Auth ──────────────────────────────────────────────

class RegisterSerializer(serializers.ModelSerializer):
    confirm_password = serializers.CharField(write_only=True)
    username = serializers.CharField(required=False, allow_blank=True)
    phone = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    first_name = serializers.CharField(required=False, allow_blank=True, default="")
    last_name = serializers.CharField(required=False, allow_blank=True, default="")

    class Meta:
        model = Users
        fields = ["username", "email", "first_name", "phone", "last_name", "password", "confirm_password"]
        extra_kwargs = {"password": {"write_only": True}}

    def validate(self, data):
        confirm_password = data.pop("confirm_password", None)
        if data.get("password") != confirm_password:
            raise serializers.ValidationError({"confirm_password": "Passwords do not match."})

        # Sanitize email
        email = data.get("email", "").strip().lower()
        if not email:
            raise serializers.ValidationError({"email": "Email address is required."})
        if Users.objects.filter(email__iexact=email).exists():
            raise serializers.ValidationError({"email": "A user with this email address already exists."})
        data["email"] = email

        # Sanitize phone
        phone = data.get("phone")
        if phone:
            phone_str = str(phone).strip()
            if phone_str:
                if Users.objects.filter(phone=phone_str).exists():
                    raise serializers.ValidationError({"phone": "A user with this phone number already exists."})
                data["phone"] = phone_str
            else:
                data["phone"] = None
        else:
            data["phone"] = None

        # Sanitize username or fallback
        username = data.get("username", "")
        if username:
            username_str = str(username).strip()
            if Users.objects.filter(username__iexact=username_str).exists():
                raise serializers.ValidationError({"username": "A user with this username already exists."})
            data["username"] = username_str
        else:
            base_username = email.split("@")[0]
            candidate = base_username
            counter = 1
            while Users.objects.filter(username__iexact=candidate).exists():
                candidate = f"{base_username}{counter}"
                counter += 1
            data["username"] = candidate

        return data

    def create(self, validated_data):
        return Users.objects.create_user(**validated_data)


class UserLoginSerializer(serializers.Serializer):
    email = serializers.CharField(required=False, allow_blank=True)
    username = serializers.CharField(required=False, allow_blank=True)
    login = serializers.CharField(required=False, allow_blank=True)
    password = serializers.CharField(write_only=True)


class UserProfileSerializer(serializers.ModelSerializer):
    role_name = serializers.SerializerMethodField()

    class Meta:
        model = Users
        fields = [
            "id", "username", "email", "first_name", "last_name", 
            "phone", "address", "city", "state", "pincode",
            "expo_push_token",
            "is_active", "is_staff", "is_superuser", "role_name"
        ]
        read_only_fields = ["id", "username", "is_staff", "is_superuser"]

    def get_role_name(self, obj):
        if obj.role:
            return obj.role.role_name
        if obj.is_superuser or obj.is_staff:
            return "admin"
        return "customer"

class AdminUserSerializer(serializers.ModelSerializer):
    role_name = serializers.CharField(source="role.role_name", read_only=True)

    class Meta:
        model = Users
        fields = [
            "id", "username", "email", "first_name", "last_name", 
            "phone", "is_active", "is_staff", "is_superuser", 
            "created_at", "role_name", "address", "city", "state", "pincode"
        ]
        read_only_fields = ["id", "username", "created_at"]

class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField()
    new_password = serializers.CharField(min_length=8)

# ── Categories ────────────────────────────────────────

class SubCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = SubCategory
        fields = ["id", "name", "slug"]

class CategorySerializer(serializers.ModelSerializer):
    subcategories = SubCategorySerializer(many=True, read_only=True)
    product_count = serializers.SerializerMethodField()
    image = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ["id", "name", "slug", "description", "image", "status", "product_count", "subcategories"]

    def get_product_count(self, obj):
        return obj.products.count()

    def get_image(self, obj):
        if not obj.image:
            return None
        val = obj.image.name or obj.image.url
        if val.startswith("http://") or val.startswith("https://"):
            return val
        request = self.context.get("request")
        return request.build_absolute_uri(obj.image.url) if request else obj.image.url

class CategoryCreateSerializer(serializers.ModelSerializer):
    image = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    subcategories = serializers.JSONField(required=False, default=list)

    class Meta:
        model = Category
        fields = ["name", "slug", "description", "status", "image", "subcategories"]

    def create(self, validated_data):
        subcategories_data = validated_data.pop("subcategories", [])
        image_val = validated_data.pop("image", None)
        category = Category.objects.create(**validated_data)
        if image_val:
            category.image = image_val
            category.save()
            
        for sub_item in subcategories_data:
            if isinstance(sub_item, dict):
                name = sub_item.get("name")
                slug = sub_item.get("slug") or slugify(name)
            else:
                name = sub_item
                slug = slugify(name)
            if name:
                SubCategory.objects.get_or_create(category=category, name=name, defaults={"slug": slug})
                
        return category

    def update(self, instance, validated_data):
        subcategories_data = validated_data.pop("subcategories", [])
        image_val = validated_data.pop("image", None)
        category = super().update(instance, validated_data)
        if image_val is not None:
            category.image = image_val
            category.save()
            
        current_subs = []
        for sub_item in subcategories_data:
            if isinstance(sub_item, dict):
                name = sub_item.get("name")
                slug = sub_item.get("slug") or slugify(name)
            else:
                name = sub_item
                slug = slugify(name)
            if name:
                sub_obj, _ = SubCategory.objects.get_or_create(category=category, name=name, defaults={"slug": slug})
                current_subs.append(sub_obj.id)
                
        SubCategory.objects.filter(category=category).exclude(id__in=current_subs).delete()
        return category

# ── Products ─────────────────────────────────────────

class ColorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Color
        fields = ["id", "name", "hex_code"]

class FabricSerializer(serializers.ModelSerializer):
    class Meta:
        model = Fabric
        fields = ["id", "name"]

class ProductImageSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()
    color = serializers.CharField(source="color.name", read_only=True, allow_null=True)

    class Meta:
        model = ProductImage
        fields = ["id", "image", "alt_text", "color", "size"]

    def get_image(self, obj):
        if not obj.image:
            return None
        
        if isinstance(obj.image, str):
            val = obj.image
        else:
            val = getattr(obj.image, "name", "") or str(obj.image)

        if val.startswith("http://") or val.startswith("https://") or val.startswith("data:"):
            return val
            
        request = self.context.get("request")
        if not isinstance(obj.image, str) and hasattr(obj.image, "url"):
            url = obj.image.url
        else:
            url = f"/media/{val}" if not val.startswith("/") else val
            
        return request.build_absolute_uri(url) if request else url

class ProductSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    subcategory = SubCategorySerializer(read_only=True)
    colors = ColorSerializer(many=True, read_only=True)
    fabric = FabricSerializer(read_only=True)
    images = ProductImageSerializer(many=True, read_only=True)
    primary_image = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            "id", "name", "slug", "price", "original_price", "primary_image", "images",
            "category", "subcategory", "colors", "sizes", "fabric", "rating", "review_count",
            "description", "short_description", "is_new", "is_featured", "tags", "in_stock",
            "stock", "sku", "status", "meta_title", "meta_description", "created_at",
            "discount_percent", "discount_amount", "hsn_code",
        ]

    def get_primary_image(self, obj):
        img = obj.images.first()
        if img:
            if isinstance(img.image, str):
                val = img.image
            else:
                val = getattr(img.image, "name", "") or str(img.image)

            if val.startswith("http://") or val.startswith("https://") or val.startswith("data:"):
                return val
                
            request = self.context.get("request")
            if not isinstance(img.image, str) and hasattr(img.image, "url"):
                url = img.image.url
            else:
                url = f"/media/{val}" if not val.startswith("/") else val
                
            return request.build_absolute_uri(url) if request else url
        return None

class ProductCreateSerializer(serializers.ModelSerializer):
    colors = serializers.PrimaryKeyRelatedField(queryset=Color.objects.all(), many=True, required=False)
    fabric = serializers.PrimaryKeyRelatedField(queryset=Fabric.objects.all(), required=False, allow_null=True)
    tags = serializers.JSONField(required=False, default=list)

    class Meta:
        model = Product
        fields = [
            "name", "price", "original_price", "description", "short_description",
            "category", "subcategory", "sizes", "colors", "fabric", "tags",
            "sku", "stock", "status", "meta_title", "meta_description",
            "discount_percent", "discount_amount", "hsn_code",
        ]

    def to_internal_value(self, data):
        data = data.copy()
        
        # 1. Resolve Category
        if "category" in data and data.get("category"):
            cat_val = data.get("category")
            try:
                cat = Category.objects.filter(models.Q(slug=cat_val) | models.Q(name__iexact=cat_val)).first()
                if cat:
                    data["category"] = cat.id
            except Exception:
                pass
                
        # 2. Resolve Subcategory
        if "subcategory" in data:
            sub_val = data.get("subcategory")
            if sub_val:
                try:
                    sub = SubCategory.objects.filter(models.Q(slug=sub_val) | models.Q(name__iexact=sub_val)).first()
                    data["subcategory"] = sub.id if sub else None
                except Exception:
                    data["subcategory"] = None
            else:
                data["subcategory"] = None

        # 3. Resolve Fabric
        if "fabric" in data:
            fab_val = data.get("fabric")
            if fab_val:
                try:
                    fab, _ = Fabric.objects.get_or_create(name=fab_val)
                    data["fabric"] = fab.id
                except Exception:
                    data["fabric"] = None
            else:
                data["fabric"] = None

        # 4. Resolve Colors
        if "colors" in data:
            colors_val = data.get("colors")
            if colors_val:
                color_ids = []
                for col_name in colors_val:
                    try:
                        col, _ = Color.objects.get_or_create(name=col_name, defaults={"hex_code": "#cccccc"})
                        color_ids.append(col.id)
                    except Exception:
                        pass
                data["colors"] = color_ids
            else:
                data["colors"] = []

        return super().to_internal_value(data)

    def create(self, validated_data):
        images_data = self.initial_data.get("images", [])
        print("CREATE INITIAL DATA IMAGES:", images_data)
        product = super().create(validated_data)
        
        for idx, img_info in enumerate(images_data):
            if isinstance(img_info, dict):
                img_url = img_info.get("image")
                col_name = img_info.get("color")
                size_val = img_info.get("size")
            else:
                img_url = img_info
                col_name = None
                size_val = None
                
            if img_url:
                col = Color.objects.filter(name__iexact=col_name).first() if col_name else None
                ProductImage.objects.create(product=product, image=img_url, color=col, size=size_val, order=idx)
                
        return product

    def update(self, instance, validated_data):
        if "images" in self.initial_data:
            images_data = self.initial_data.get("images", [])
            print("UPDATE INITIAL DATA IMAGES:", images_data)
            ProductImage.objects.filter(product=instance).delete()
            for idx, img_info in enumerate(images_data):
                if isinstance(img_info, dict):
                    img_url = img_info.get("image")
                    col_name = img_info.get("color")
                    size_val = img_info.get("size")
                else:
                    img_url = img_info
                    col_name = None
                    size_val = None
                    
                if img_url:
                    col = Color.objects.filter(name__iexact=col_name).first() if col_name else None
                    ProductImage.objects.create(product=instance, image=img_url, color=col, size=size_val, order=idx)
                    
        return super().update(instance, validated_data)

# ── Orders ───────────────────────────────────────────

class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ["id", "product_name", "quantity", "price", "size", "color"]

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    customer_name = serializers.SerializerMethodField()
    customer_email = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = [
            "id", "order_number", "status", "payment_status", "total",
            "created_at", "customer_name", "customer_email",
            "shipping_address", "tracking_number", "items",
        ]

    def get_customer_name(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}".strip() or obj.user.username

    def get_customer_email(self, obj):
        return obj.user.email

class OrderItemCreateSerializer(serializers.Serializer):
    product_id = serializers.UUIDField()
    quantity = serializers.IntegerField(min_value=1)
    size = serializers.CharField(required=False, default="")
    color = serializers.CharField(required=False, default="")

class OrderCreateSerializer(serializers.Serializer):
    shipping_address = serializers.CharField()
    city = serializers.CharField()
    state = serializers.CharField()
    pincode = serializers.CharField()
    phone = serializers.CharField()
    coupon_code = serializers.CharField(required=False, default="", allow_blank=True)
    payment_method = serializers.CharField(required=False, default="cod")
    items = OrderItemCreateSerializer(many=True)

    def validate(self, data):
        coupon_code = data.get("coupon_code")
        if coupon_code:
            try:
                coupon = Coupon.objects.get(code__iexact=coupon_code)
                if coupon.status != "active":
                    raise serializers.ValidationError({"coupon_code": "This coupon code is inactive."})
                
                from django.utils import timezone
                now = timezone.now()
                if now < coupon.start_date:
                    raise serializers.ValidationError({"coupon_code": "This coupon code is not active yet."})
                if now > coupon.end_date:
                    raise serializers.ValidationError({"coupon_code": "This coupon code has expired."})
                    
                if coupon.max_uses > 0 and coupon.used_count >= coupon.max_uses:
                    raise serializers.ValidationError({"coupon_code": "This coupon has reached its maximum usage limit."})
                
                user = self.context["request"].user
                if coupon_code.upper() == "WELCOME20":
                    if not user or not user.is_authenticated:
                        raise serializers.ValidationError({"coupon_code": "Please log in to apply this coupon."})
                    used = Order.objects.filter(user=user, coupon_code__iexact="WELCOME20").exists()
                    if used:
                        raise serializers.ValidationError({"coupon_code": "The WELCOME20 coupon can only be used once per customer."})
                        
                subtotal = 0
                for item in data.get("items", []):
                    product = Product.objects.get(id=item["product_id"])
                    subtotal += product.price * item["quantity"]
                if subtotal < coupon.min_order:
                    raise serializers.ValidationError({"coupon_code": f"This coupon requires a minimum purchase of ₹{coupon.min_order}."})
            except Coupon.DoesNotExist:
                raise serializers.ValidationError({"coupon_code": "Invalid coupon code."})
        return data

    def create(self, validated_data):
        items_data = validated_data.pop("items")
        payment_method = validated_data.pop("payment_method", "cod")
        user = self.context["request"].user
        total = 0

        order = Order.objects.create(user=user, total=0, **validated_data)

        for item_data in items_data:
            product = Product.objects.get(id=item_data["product_id"])
            line_total = product.price * item_data["quantity"]
            total += line_total
            OrderItem.objects.create(
                order=order,
                product=product,
                product_name=product.name,
                quantity=item_data["quantity"],
                price=product.price,
                size=item_data.get("size", ""),
                color=item_data.get("color", ""),
            )

        # Apply coupon if provided
        coupon_code = validated_data.get("coupon_code")
        if coupon_code:
            try:
                coupon = Coupon.objects.get(code__iexact=coupon_code)
                if coupon.is_valid:
                    if coupon.type == "percentage":
                        total -= total * (coupon.value / 100)
                    else:
                        total -= coupon.value
                    total = max(total, 0)
                    coupon.used_count += 1
                    coupon.save()
            except Coupon.DoesNotExist:
                pass

        order.total = total
        order.save()

        if payment_method == "cod":
            try:
                from .utils import send_order_status_email
                send_order_status_email(order, is_new=True, old_status=None, old_payment_status=None)
            except Exception as e:
                print(f"Error sending COD email: {e}")

        return order

class OrderStatusUpdateSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=Order.STATUS_CHOICES)

# ── Coupons ──────────────────────────────────────────

class CouponSerializer(serializers.ModelSerializer):
    class Meta:
        model = Coupon
        fields = [
            "id", "code", "type", "value", "min_order", "max_uses",
            "used_count", "status", "start_date", "end_date", "description",
        ]

class CouponCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Coupon
        fields = ["code", "type", "value", "min_order", "max_uses", "status", "start_date", "end_date", "description"]

class CouponValidateSerializer(serializers.Serializer):
    code = serializers.CharField()

# ── Wishlist ─────────────────────────────────────────

class WishlistSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)

    class Meta:
        model = Wishlist
        fields = ["id", "product", "created_at"]

class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ["id", "title", "message", "is_read", "created_at"]

class ReviewSerializer(serializers.ModelSerializer):
    user_name = serializers.SerializerMethodField()

    class Meta:
        model = Review
        fields = ["id", "product", "user", "user_name", "rating", "comment", "created_at"]
        read_only_fields = ["id", "user", "product"]

    def get_user_name(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}".strip() or obj.user.username
