from rest_framework import serializers
from .models import Users
from .models import *

# ── Auth ──────────────────────────────────────────────

class RegisterSerializer(serializers.ModelSerializer):
    confirm_password = serializers.CharField(write_only=True)

    class Meta:
        model = Users
        fields = ["username", "email", "first_name",'phone',"last_name","password", "confirm_password"]
        extra_kwargs = {"password": {"write_only": True}}

    def validate(self, data):
        if data["password"] != data.pop("confirm_password"):
            raise serializers.ValidationError({"confirm_password": "Passwords do not match."})
        return data

    def create(self, validated_data):
        return Users.objects.create_user(**validated_data)

class UserLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    
class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Users
        fields = ["id", "username", "email", "first_name", "last_name"]
        read_only_fields = ["id", "username"]

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

    class Meta:
        model = Category
        fields = ["id", "name", "slug", "description", "image", "status", "product_count", "subcategories"]

    def get_product_count(self, obj):
        return obj.products.count()

class CategoryCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["name", "slug", "description", "status", "image"]

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
    class Meta:
        model = ProductImage
        fields = ["id", "image", "alt_text"]

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
            "description", "short_description", "is_new", "is_featured", "in_stock",
            "stock", "sku", "status", "meta_title", "meta_description", "created_at",
        ]

    def get_primary_image(self, obj):
        img = obj.images.first()
        if img:
            request = self.context.get("request")
            return request.build_absolute_uri(img.image.url) if request else img.image.url
        return None

class ProductCreateSerializer(serializers.ModelSerializer):
    colors = serializers.PrimaryKeyRelatedField(queryset=Color.objects.all(), many=True, required=False)
    fabric = serializers.PrimaryKeyRelatedField(queryset=Fabric.objects.all(), required=False, allow_null=True)

    class Meta:
        model = Product
        fields = [
            "name", "price", "original_price", "description", "short_description",
            "category", "subcategory", "sizes", "colors", "fabric",
            "sku", "stock", "status", "meta_title", "meta_description",
        ]

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
        return f"{obj.users.first_name} {obj.users.last_name}".strip() or obj.users.username

    def get_customer_email(self, obj):
        return obj.users.email

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
    coupon_code = serializers.CharField(required=False, default="")
    items = OrderItemCreateSerializer(many=True)

    def create(self, validated_data):
        items_data = validated_data.pop("items")
        user = self.context["request"].users
        total = 0

        order = Order.objects.create(users=Users, total=0, **validated_data)

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
                coupon = Coupon.objects.get(code=coupon_code)
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
