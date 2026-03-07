from rest_framework import generics, status, permissions, filters
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import action
from store.models import Users
from django.db.models import Q
from .models import Category, Product, Order, Coupon, Wishlist
from .serializers import *



# ══════════════════════════════════════════════════════
# AUTH VIEWS
# ══════════════════════════════════════════════════════

class RegisterView(generics.CreateAPIView):
    queryset = Users.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(UserProfileSerializer(user).data, status=status.HTTP_201_CREATED)

class ProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user

class ChangePasswordView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = request.user
        if not Users.check_password(serializer.validated_data["old_password"]):
            return Response({"old_password": "Incorrect password."}, status=400)
        Users.set_password(serializer.validated_data["new_password"])
        Users.save()
        return Response({"detail": "Password changed successfully."})

class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        # With SimpleJWT, logout is client-side (remove tokens)
        # Optionally blacklist the refresh token here
        return Response({"detail": "Logged out."})

# ══════════════════════════════════════════════════════
# PUBLIC VIEWS
# ══════════════════════════════════════════════════════

class CategoryListView(generics.ListAPIView):
    queryset = Category.objects.filter(status="active")
    serializer_class = CategorySerializer
    permission_classes = [permissions.AllowAny]

class ProductListView(generics.ListAPIView):
    serializer_class = ProductSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        qs = Product.objects.filter(status="active")
        params = self.request.query_params

        if params.get("category"):
            qs = qs.filter(category__slug=params["category"])
        if params.get("subcategory"):
            qs = qs.filter(subcategory__slug=params["subcategory"])
        if params.get("fabric"):
            qs = qs.filter(fabric__name__iexact=params["fabric"])
        if params.get("min_price"):
            qs = qs.filter(price__gte=params["min_price"])
        if params.get("max_price"):
            qs = qs.filter(price__lte=params["max_price"])
        if params.get("search"):
            qs = qs.filter(Q(name__icontains=params["search"]) | Q(description__icontains=params["search"]))
        if params.get("is_featured"):
            qs = qs.filter(is_featured=True)
        if params.get("is_new"):
            qs = qs.filter(is_new=True)
        if params.get("ordering"):
            qs = qs.order_by(params["ordering"])

        return qs

class ProductDetailView(generics.RetrieveAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [permissions.AllowAny]

class OrderCreateView(generics.CreateAPIView):
    serializer_class = OrderCreateSerializer
    permission_classes = [permissions.IsAuthenticated]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        order = serializer.save()
        return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)

class OrderListView(generics.ListAPIView):
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user)

class OrderDetailView(generics.RetrieveAPIView):
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user)

class CouponValidateView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        code = request.data.get("code", "")
        try:
            coupon = Coupon.objects.get(code__iexact=code)
            if coupon.is_valid:
                return Response({
                    "valid": True,
                    "discount_type": coupon.type,
                    "discount_value": str(coupon.value),
                    "message": f"Coupon applied! {'{}% off'.format(coupon.value) if coupon.type == 'percentage' else '₹{} off'.format(coupon.value)}",
                })
            return Response({"valid": False, "message": "Coupon has expired or reached max uses."})
        except Coupon.DoesNotExist:
            return Response({"valid": False, "message": "Invalid coupon code."})

class WishlistView(generics.ListAPIView):
    serializer_class = WishlistSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Wishlist.objects.filter(user=self.request.user)

class WishlistToggleView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, product_id):
        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            return Response({"detail": "Product not found."}, status=404)

        wishlist_item, created = Wishlist.objects.get_or_create(user=request.user, product=product)
        if not created:
            wishlist_item.delete()
            return Response({"status": "removed"})
        return Response({"status": "added"})

# ══════════════════════════════════════════════════════
# ADMIN VIEWS (staff only)
# ══════════════════════════════════════════════════════

class IsAdminUser(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user and request.Users.is_staff

# ── Admin Categories ──
class AdminCategoryListCreateView(generics.ListCreateAPIView):
    queryset = Category.objects.all()
    permission_classes = [IsAdminUser]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return CategoryCreateSerializer
        return CategorySerializer

class AdminCategoryDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Category.objects.all()
    permission_classes = [IsAdminUser]

    def get_serializer_class(self):
        if self.request.method in ("PATCH", "PUT"):
            return CategoryCreateSerializer
        return CategorySerializer

# ── Admin Products ──
class AdminProductListCreateView(generics.ListCreateAPIView):
    queryset = Product.objects.all()
    permission_classes = [IsAdminUser]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return ProductCreateSerializer
        return ProductSerializer

class AdminProductDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Product.objects.all()
    permission_classes = [IsAdminUser]

    def get_serializer_class(self):
        if self.request.method in ("PATCH", "PUT"):
            return ProductCreateSerializer
        return ProductSerializer

# ── Admin Orders ──
class AdminOrderListView(generics.ListAPIView):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [IsAdminUser]

class AdminOrderDetailView(generics.RetrieveUpdateAPIView):
    queryset = Order.objects.all()
    permission_classes = [IsAdminUser]

    def get_serializer_class(self):
        if self.request.method in ("PATCH", "PUT"):
            return OrderStatusUpdateSerializer
        return OrderSerializer

    def update(self, request, *args, **kwargs):
        order = self.get_object()
        serializer = OrderStatusUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        order.status = serializer.validated_data["status"]
        order.save()
        return Response(OrderSerializer(order).data)

# ── Admin Coupons ──
class AdminCouponListCreateView(generics.ListCreateAPIView):
    queryset = Coupon.objects.all()
    permission_classes = [IsAdminUser]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return CouponCreateSerializer
        return CouponSerializer

class AdminCouponDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Coupon.objects.all()
    permission_classes = [IsAdminUser]

    def get_serializer_class(self):
        if self.request.method in ("PATCH", "PUT"):
            return CouponCreateSerializer
        return CouponSerializer
