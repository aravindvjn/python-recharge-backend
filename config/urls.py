"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

schema_view = get_schema_view(
    openapi.Info(
        title="Recharge Backend - Mobile Recharge API",
        default_version='v1',
        description="""
        ## Welcome to Recharge Backend API 🚀
        
        A comprehensive REST API for mobile recharge management system with advanced user roles and wallet functionality. 
        Recharge Backend provides a seamless platform for mobile recharge services with multi-level user management.
        
        ## ✨ Key Features
        - 🔐 **Secure Authentication**: JWT tokens with email/OTP login
        - 👥 **Multi-Role System**: Admin, Distributor, Retailer, and Client roles
        - 💰 **Advanced Wallet Management**: Real-time balance tracking and transactions
        - 📊 **Margin Management**: Configurable profit margins for distributors and retailers
        - 📱 **Multi-Provider Support**: Airtel, Jio, Vi, BSNL and more
        - 💳 **Smart Purchase System**: Real-time transaction processing with wallet deduction
        - 🔍 **Advanced Search**: Filter plans by provider, price, validity
        - 📈 **Transaction History**: Complete purchase and wallet transaction tracking
        - 🛡️ **Security**: Role-based access control and encrypted transactions
        
        ## 👤 User Roles
        - **Admin (1)**: Full system control, user management, wallet operations
        - **Distributor (2)**: Manage retailers, handle bulk transactions
        - **Retailer (3)**: Serve end customers, process recharges
        - **Client (4)**: End users who purchase recharge plans
        
        ## 🔑 Authentication
        Click the 'Authorize' button above to add your JWT token.
        **Format:** `Bearer <your_jwt_token>`
        
        ## 🚀 Quick Start Guide
        1. **Admin Setup**: Create admin account and configure system
        2. **User Management**: Add distributors and retailers via admin panel
        3. **Wallet Funding**: Add money to distributor/retailer wallets
        4. **Set Margins**: Configure profit margins for each user type
        5. **Start Trading**: Begin processing recharge transactions
        
        ## 📊 API Categories
        - **Authentication**: User registration, login, OTP verification
        - **Admin Management**: User CRUD operations, password reset
        - **Wallet Management**: Balance operations, transaction history
        - **Recharge Plans**: Browse and search available plans
        - **Purchase System**: Process transactions with wallet integration
        
        ## 📞 Support
        For technical support, please contact the development team.
        """,
        terms_of_service="https://rechargebackend.com/terms/",
        contact=openapi.Contact(
            name="Recharge Backend Support",
            email="support@rechargebackend.com",
            url="https://rechargebackend.com/support/"
        ),
        license=openapi.License(name="MIT License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('accounts.urls')),
    path('api/plans/', include('plans.urls')),
    path('api/purchases/', include('purchases.urls')),
    path('api/wallet/', include('wallet.urls')),
    path('api/support/',include('support.urls')),
    path('api/notifications/',include('notifications.urls')),
    path('api/payment/', include('payment.urls')),

    
    # Swagger Documentation URLs
    re_path(r'^swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    path('', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),  # Default to Swagger UI
    
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)