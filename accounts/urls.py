from django.urls import path
from . import views
from rest_framework_simplejwt.views import TokenRefreshView
from .views import  user_profile_create_or_update


urlpatterns = [
    path('signup/', views.signup, name='signup'),
    path('login/email/', views.login_email, name='login_email'),
    path('otp/generate/', views.generate_otp, name='generate_otp'),
    path('otp/verify/', views.verify_otp, name='verify_otp'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('profile/', user_profile_create_or_update),

    # Admin Management URLs
    path('admin/users/', views.UserListView.as_view(), name='admin-user-list'),
    path('admin/users/create/', views.create_user, name='admin-create-user'),
    path('admin/users/<int:user_id>/', views.get_user, name='admin-get-user'),
    path('admin/users/<int:user_id>/update/',
         views.update_user, name='admin-update-user'),
    path('admin/users/<int:user_id>/delete/',
         views.delete_user, name='admin-delete-user'),
    path('admin/users/<int:user_id>/reset-password/',
         views.reset_user_password, name='admin-reset-password'),
    path('admin/users/search/', views.search_users, name='admin-user-search'),
]
