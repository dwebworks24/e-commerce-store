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
    path("products//", views.ProductDetailView.as_view(), name="product_detail"),
    path("products//toggle_wishlist/", views.WishlistToggleView.as_view(), name="toggle_wishlist"),
    path("orders/", views.OrderCreateView.as_view(), name="order_create"),  # POST
    path("orders/list/", views.OrderListView.as_view(), name="order_list"),  # GET user orders
    path("orders//", views.OrderDetailView.as_view(), name="order_detail"),
    path("coupons/validate/", views.CouponValidateView.as_view(), name="coupon_validate"),
    path("wishlist/", views.WishlistView.as_view(), name="wishlist"),

    # ── Admin ──
    path("admin/categories/", views.AdminCategoryListCreateView.as_view(), name="admin_categories"),
    path("admin/categories//", views.AdminCategoryDetailView.as_view(), name="admin_category_detail"),
    path("admin/products/", views.AdminProductListCreateView.as_view(), name="admin_products"),
    path("admin/products//", views.AdminProductDetailView.as_view(), name="admin_product_detail"),
    path("admin/orders/", views.AdminOrderListView.as_view(), name="admin_orders"),
    path("admin/orders//", views.AdminOrderDetailView.as_view(), name="admin_order_detail"),
    path("admin/coupons/", views.AdminCouponListCreateView.as_view(), name="admin_coupons"),
    path("admin/coupons//", views.AdminCouponDetailView.as_view(), name="admin_coupon_detail"),
]
