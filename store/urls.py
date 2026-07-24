from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from . import views

urlpatterns = [
    # ── Auth ──
    # path("auth/login/", TokenObtainPairView.as_view(), name="token_obtain"),
    # path("auth/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("auth/login/", views.LoginView.as_view(), name="login"),
    path("auth/refresh/", views.RefreshTokenView.as_view(), name="refresh"),
    path("auth/register/", views.RegisterView.as_view(), name="register"),
    path("auth/profile/", views.ProfileView.as_view(), name="profile"),
    path("auth/change-password/", views.ChangePasswordView.as_view(), name="change_password"),
    path("auth/logout/", views.LogoutView.as_view(), name="logout"),

    # ── Public ──
    path("categories/", views.CategoryListView.as_view(), name="categories"),
    path("products/", views.ProductListView.as_view(), name="products"),
    path("products/<uuid:pk>/", views.ProductDetailView.as_view(), name="product_detail"),
    path("products/<uuid:product_id>/toggle_wishlist/", views.WishlistToggleView.as_view(), name="toggle_wishlist"),
    path("products/<uuid:product_id>/reviews/", views.ProductReviewView.as_view(), name="product_reviews"),
    path("orders/", views.OrderCreateView.as_view(), name="order_create"),  # POST
    path("orders/list/", views.OrderListView.as_view(), name="order_list"),  # GET user orders
    path("orders/verify-payment/", views.VerifyPaymentView.as_view(), name="order_verify_payment"),
    path("orders/razorpay-webhook/", views.RazorpayWebhookView.as_view(), name="razorpay_webhook"),
    path("orders/<uuid:pk>/", views.OrderDetailView.as_view(), name="order_detail"),
    path("coupons/validate/", views.CouponValidateView.as_view(), name="coupon_validate"),
    path("shipping/check-pincode/", views.CheckPincodeView.as_view(), name="check_pincode"),
    path("payment/config/", views.PublicPaymentConfigView.as_view(), name="public_payment_config"),
    path("wishlist/", views.WishlistView.as_view(), name="wishlist"),
    path("notifications/", views.NotificationListView.as_view(), name="notification_list"),
    path("notifications/<str:pk>/mark-read/", views.NotificationMarkReadView.as_view(), name="notification_mark_read"),
    path("notifications/clear/", views.NotificationClearView.as_view(), name="notification_clear"),

    # ── Admin ──
    path("admin/categories/", views.AdminCategoryListCreateView.as_view(), name="admin_categories"),
    path("admin/categories/<int:pk>/", views.AdminCategoryDetailView.as_view(), name="admin_category_detail"),
    path("admin/products/", views.AdminProductListCreateView.as_view(), name="admin_products"),
    path("admin/products/<uuid:pk>/", views.AdminProductDetailView.as_view(), name="admin_product_detail"),
    path("admin/orders/", views.AdminOrderListView.as_view(), name="admin_orders"),
    path("admin/orders/<uuid:pk>/", views.AdminOrderDetailView.as_view(), name="admin_order_detail"),
    path("admin/coupons/", views.AdminCouponListCreateView.as_view(), name="admin_coupons"),
    path("admin/coupons/<uuid:pk>/", views.AdminCouponDetailView.as_view(), name="admin_coupon_detail"),
    path("admin/users/", views.AdminUserListCreateView.as_view(), name="admin_users"),
    path("admin/users/<int:pk>/", views.AdminUserDetailView.as_view(), name="admin_user_detail"),
    path("admin/shipping-config/", views.AdminShippingConfigView.as_view(), name="admin_shipping_config"),
    path("admin/payment-config/", views.AdminPaymentConfigView.as_view(), name="admin_payment_config"),
]
