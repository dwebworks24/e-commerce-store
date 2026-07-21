from rest_framework import generics, status, permissions, filters
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import action
from store.models import Users
from django.db.models import Q
from .models import Category, Product, Order, Coupon, Wishlist, Notification
from .serializers import *

from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from django.contrib.auth.hashers import check_password

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

        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)

        return Response(
            {
                "message": "Registration successful",
                "access_token": access_token,
                "refresh_token": refresh_token,
                "user": UserProfileSerializer(user).data,
            },
            status=status.HTTP_201_CREATED,
        )

class LoginView(generics.GenericAPIView):
    serializer_class = UserLoginSerializer
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        raw_id = request.data.get("email") or request.data.get("username") or request.data.get("login")
        password = request.data.get("password")

        identifier = str(raw_id).strip() if raw_id else ""

        # Validate input
        if not identifier or not password:
            return Response(
                {
                    "error": "validation_error",
                    "message": "Email/Username and password are required"
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check user by email, username, or phone
        user = Users.objects.filter(
            Q(email__iexact=identifier) | Q(username__iexact=identifier) | Q(phone=identifier)
        ).first()

        if not user:
            return Response(
                {
                    "error": "invalid_credentials",
                    "message": "Invalid email/username or password"
                },
                status=status.HTTP_401_UNAUTHORIZED
            )

        # Check active
        if not user.is_active:
            return Response(
                {
                    "error": "account_deactivated",
                    "message": "Your account has been deactivated. Please contact support."
                },
                status=status.HTTP_403_FORBIDDEN
            )

        # Check password
        if not check_password(password, user.password):
            return Response(
                {
                    "error": "invalid_credentials",
                    "message": "Invalid email/username or password"
                },
                status=status.HTTP_401_UNAUTHORIZED
            )

        # Generate Tokens
        refresh = RefreshToken.for_user(user)

        access_token = str(refresh.access_token)
        refresh_token = str(refresh)

        return Response(
            {
                "message": "Login successful",
                "access_token": access_token,
                "refresh_token": refresh_token,
                "user": UserProfileSerializer(user).data,
            },
            status=status.HTTP_200_OK
        )


class RefreshTokenView(APIView):

    def post(self, request):

        refresh_token = request.data.get("refresh_token")

        if not refresh_token:
            return Response(
                {
                    "error": "validation_error",
                    "message": "Refresh token required"
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            refresh = RefreshToken(refresh_token)

            return Response(
                {
                    "access_token": str(refresh.access_token)
                },
                status=status.HTTP_200_OK
            )

        except TokenError:
            return Response(
                {
                    "error": "invalid_token",
                    "message": "Invalid or expired refresh token"
                },
                status=status.HTTP_401_UNAUTHORIZED
            )


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
        if not user.check_password(serializer.validated_data["old_password"]):
            return Response({"old_password": "Incorrect password."}, status=400)
        user.set_password(serializer.validated_data["new_password"])
        user.save()
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
    pagination_class = None

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
        
        payment_method = request.data.get("payment_method", "cod")
        order = serializer.save()

        if payment_method != "cod":
            import razorpay
            from django.conf import settings
            try:
                client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
                razorpay_amount = int(order.total * 100)
                razorpay_order = client.order.create({
                    "amount": razorpay_amount,
                    "currency": "INR",
                    "receipt": str(order.order_number),
                    "payment_capture": 1
                })
                order.razorpay_order_id = razorpay_order["id"]
                order.save()

                return Response({
                    "order": OrderSerializer(order).data,
                    "razorpay_order_id": order.razorpay_order_id,
                    "razorpay_key_id": settings.RAZORPAY_KEY_ID,
                    "amount": razorpay_amount,
                    "currency": "INR",
                }, status=status.HTTP_201_CREATED)
            except Exception as e:
                print(f"Razorpay Order creation failed: {e}")
                
        return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)

class OrderListView(generics.ListAPIView):
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = None

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
        subtotal_val = request.data.get("subtotal")
        
        try:
            coupon = Coupon.objects.get(code__iexact=code)
            
            # 1. Check status
            if coupon.status != "active":
                return Response({"valid": False, "message": "This coupon code is inactive."})
                
            # 2. Check dates
            from django.utils import timezone
            now = timezone.now()
            if now < coupon.start_date:
                return Response({"valid": False, "message": "This coupon code is not active yet."})
            if now > coupon.end_date:
                return Response({"valid": False, "message": "This coupon code has expired."})
                
            # 3. Check total uses
            if coupon.max_uses > 0 and coupon.used_count >= coupon.max_uses:
                return Response({"valid": False, "message": "This coupon has reached its maximum usage limit."})
                
            # 4. Check min order requirement
            if subtotal_val is not None:
                try:
                    subtotal_num = float(subtotal_val)
                    if subtotal_num < float(coupon.min_order):
                        return Response({
                            "valid": False,
                            "message": f"This coupon requires a minimum purchase of ₹{coupon.min_order}."
                        })
                except (ValueError, TypeError):
                    pass
                    
            # 5. Check WELCOME20 user-specific limits
            if code.upper() == "WELCOME20":
                if not request.user or not request.user.is_authenticated:
                    return Response({
                        "valid": False,
                        "message": "Please log in to apply this coupon."
                    })
                # Check if this user has already used WELCOME20
                used = Order.objects.filter(user=request.user, coupon_code__iexact="WELCOME20").exists()
                if used:
                    return Response({
                        "valid": False,
                        "message": "The WELCOME20 coupon can only be used once per customer."
                    })
                    
            # Coupon is valid!
            return Response({
                "valid": True,
                "discount_type": coupon.type,
                "discount_value": str(coupon.value),
                "message": f"Coupon applied! {'{}% off'.format(coupon.value) if coupon.type == 'percentage' else '₹{} off'.format(coupon.value)}",
            })
            
        except Coupon.DoesNotExist:
            return Response({"valid": False, "message": "Invalid coupon code."})

class WishlistView(generics.ListAPIView):
    serializer_class = WishlistSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = None

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
        return bool(
            request.user and (
                request.user.is_staff or 
                request.user.is_superuser or 
                (hasattr(request.user, "role") and request.user.role and request.user.role.role_category in ["admin", "staff"])
            )
        )

# ── Admin Categories ──
class AdminCategoryListCreateView(generics.ListCreateAPIView):
    queryset = Category.objects.all()
    permission_classes = [IsAdminUser]
    pagination_class = None

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
    pagination_class = None

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
    pagination_class = None

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

# ── Admin Users ──
class AdminUserListCreateView(generics.ListCreateAPIView):
    queryset = Users.objects.all().order_by("-created_at")
    serializer_class = AdminUserSerializer
    permission_classes = [IsAdminUser]
    pagination_class = None

class AdminUserDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Users.objects.all()
    serializer_class = AdminUserSerializer
    permission_classes = [IsAdminUser]

class VerifyPaymentView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        razorpay_order_id = request.data.get("razorpay_order_id")
        razorpay_payment_id = request.data.get("razorpay_payment_id")
        razorpay_signature = request.data.get("razorpay_signature")

        if not razorpay_order_id or not razorpay_payment_id or not razorpay_signature:
            return Response({"error": "Missing payment verification parameters"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            order = Order.objects.get(razorpay_order_id=razorpay_order_id, user=request.user)
        except Order.DoesNotExist:
            return Response({"error": "Order not found"}, status=status.HTTP_404_NOT_FOUND)

        import razorpay
        from django.conf import settings
        
        try:
            client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
            params_dict = {
                'razorpay_order_id': razorpay_order_id,
                'razorpay_payment_id': razorpay_payment_id,
                'razorpay_signature': razorpay_signature
            }
            client.utility.verify_payment_signature(params_dict)
            
            order.payment_status = "paid"
            order.status = "confirmed"
            order.razorpay_payment_id = razorpay_payment_id
            order.save()
            return Response({"message": "Payment verified successfully", "status": "success"})
        except Exception as e:
            print(f"Payment verification failed: {e}")
            order.payment_status = "failed"
            order.save()
            return Response({"error": "Payment signature verification failed", "status": "failed"}, status=status.HTTP_400_BAD_REQUEST)

class NotificationListView(generics.ListAPIView):
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = None

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user)

class NotificationMarkReadView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk=None):
        if pk == "all":
            Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
            return Response({"status": "success", "message": "All notifications marked as read"})
        
        try:
            notification = Notification.objects.get(pk=pk, user=request.user)
            notification.is_read = True
            notification.save()
            return Response({"status": "success", "message": "Notification marked as read"})
        except Notification.DoesNotExist:
            return Response({"error": "Notification not found"}, status=status.HTTP_404_NOT_FOUND)
