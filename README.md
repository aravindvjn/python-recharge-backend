# Recharge Backend 🚀

A comprehensive REST API for mobile recharge management system with advanced user roles and wallet functionality. Built with Django REST Framework and designed for multi-level business operations.

## 🌟 Features

### 🔐 **Authentication & Security**
- JWT token-based authentication
- Email/password and OTP-based login
- Role-based access control
- Secure password management

### 👥 **Multi-Role User System**
- **Admin (1)**: Full system control, user management, wallet operations
- **Distributor (2)**: Manage retailers, handle bulk transactions
- **Retailer (3)**: Serve end customers, process recharges
- **Client (4)**: End users who purchase recharge plans

### 💰 **Advanced Wallet Management**
- Real-time balance tracking
- Automated wallet creation for business users
- Transaction history with full audit trail
- Admin-controlled wallet funding and deduction
- Balance validation and insufficient fund protection

### 📊 **Margin Management**
- Configurable profit margins for distributors and retailers
- Admin-controlled margin setting
- Flexible percentage-based pricing

### 📱 **Recharge System**
- Multi-provider support (Airtel, Jio, Vi, BSNL, etc.)
- Plan browsing and filtering
- Real-time transaction processing
- Purchase history tracking

## 🏗️ Architecture

### **Project Structure**
```
callCenter/
├── accounts/           # User management & authentication
├── wallet/            # Wallet & transaction management
├── plans/             # Recharge plans management
├── purchases/         # Purchase & transaction processing
├── config/            # Django configuration
└── core/              # Shared utilities
```

### **Database Models**
- **User**: Multi-role user system with IntEnum types
- **Wallet**: User wallet with balance tracking
- **WalletTransaction**: Complete transaction history
- **UserMargin**: Configurable profit margins
- **Rechargeplan**: Available recharge plans
- **Purchase**: Transaction records

## 🚀 Quick Start

### **Prerequisites**
- Python 3.8+
- Django 5.2+
- PostgreSQL/SQLite
- UV package manager (recommended)

### **Installation**

1. **Clone the repository**
```bash
git clone <repository-url>
cd callCenter
```

2. **Set up virtual environment**
```bash
uv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
uv pip install -r requirements.txt
```

4. **Configure database**
```bash
uv python manage.py migrate
```

5. **Create superuser (Admin)**
```bash
uv python manage.py createsuperuser
```

6. **Load sample data (optional)**
```bash
uv python manage.py setup_demo_data
uv python manage.py populate_plans
```

7. **Run development server**
```bash
uv python manage.py runserver
```

## 📖 API Documentation

### **Interactive Documentation**
- **Swagger UI**: `http://localhost:8000/swagger/`
- **ReDoc**: `http://localhost:8000/redoc/`
- **Admin Panel**: `http://localhost:8000/admin/`

### **API Endpoints Overview**

#### **Authentication** (`/api/auth/`)
| Endpoint | Method | Description | Auth Required |
|----------|---------|-------------|---------------|
| `/signup/` | POST | User registration | No |
| `/login/email/` | POST | Email/password login | No |
| `/otp/generate/` | POST | Generate OTP for phone | No |
| `/otp/verify/` | POST | Verify OTP and login | No |

#### **Admin Management** (`/api/auth/admin/`)
| Endpoint | Method | Description | Admin Only |
|----------|---------|-------------|------------|
| `/users/` | GET | List distributors/retailers with wallet balance | ✅ |
| `/users/create/` | POST | Create new users (auto-creates wallet) | ✅ |
| `/users/{id}/` | GET | Get user details with wallet info | ✅ |
| `/users/{id}/update/` | PUT | Update user information | ✅ |
| `/users/{id}/delete/` | DELETE | Delete user account | ✅ |
| `/users/{id}/reset-password/` | POST | Reset user password | ✅ |

#### **Wallet Management** (`/api/wallet/`)
| Endpoint | Method | Description | Admin Only |
|----------|---------|-------------|------------|
| `/wallets/` | GET | List wallets | No |
| `/wallets/{id}/` | GET | Wallet details | No |
| `/transactions/` | GET | Transaction history | No |
| `/add-to-wallet/` | POST | Add money to wallet | ✅ |
| `/debit-from-wallet/` | POST | Debit from wallet | ✅ |
| `/set-margin/` | POST | Set user margins | ✅ |
| `/margins/` | GET | List user margins | No |

#### **Plans & Purchases** (`/api/plans/`, `/api/purchases/`)
| Endpoint | Method | Description | Auth Required |
|----------|---------|-------------|---------------|
| `/plans/` | GET | List recharge plans | Yes |
| `/purchases/purchase/` | POST | Process recharge | Yes |
| `/purchases/history/` | GET | Purchase history | Yes |

## 💼 Business Workflow

### **1. System Setup**
1. Admin creates distributor accounts with automatic wallet creation
2. Admin funds distributor wallets
3. Admin sets profit margins for distributors

### **2. Distributor Operations**
1. Distributor creates retailer accounts
2. Distributor transfers funds to retailer wallets
3. Distributor manages retailer margins

### **3. Retailer Operations**
1. Retailer serves end customers
2. Processes recharge transactions with wallet deduction
3. Manages customer relationships

### **4. Transaction Flow**
```
Customer Request → Retailer → Wallet Balance Check → Recharge Processing → Wallet Deduction → Success/Failure
```

## 🔧 Configuration

### **Environment Variables**
```bash
# Database
DATABASE_URL=postgresql://user:password@localhost/recharge_backend

# Security
SECRET_KEY=your-secret-key-here
DEBUG=False

# JWT Settings
JWT_ACCESS_TOKEN_LIFETIME=60  # minutes
JWT_REFRESH_TOKEN_LIFETIME=1440  # minutes (24 hours)

# OTP Settings
OTP_EXPIRY_MINUTES=1
```

### **User Roles Configuration**
```python
# User Types (IntEnum)
ADMIN = 1        # Full system access
DISTRIBUTOR = 2  # Manage retailers
RETAILER = 3     # Serve customers
CLIENT = 4       # End users
```

## 🧪 Testing

### **Run Tests**
```bash
uv python manage.py test
```

### **API Testing**
Use the interactive Swagger documentation at `/swagger/` for testing all endpoints with proper authentication.

### **Sample API Calls**

#### **Create User with Wallet (Admin)**
```bash
curl -X POST "http://localhost:8000/api/auth/admin/users/create/" \
     -H "Authorization: Bearer <admin_token>" \
     -H "Content-Type: application/json" \
     -d '{
       "email": "distributor@example.com",
       "username": "distributor",
       "first_name": "John",
       "last_name": "Distributor",
       "phone": "+1234567890",
       "user_type": 2,
       "password": "SecurePass123!",
       "password_confirm": "SecurePass123!"
     }'
```

Response includes wallet information:
```json
{
  "message": "User created successfully",
  "user": {
    "id": 2,
    "email": "distributor@example.com",
    "wallet_balance": "0.00",
    "wallet_id": 1,
    "user_type": 2,
    "user_type_display": "Distributor"
  }
}
```

#### **Add to Wallet (Admin)**
```bash
curl -X POST "http://localhost:8000/api/wallet/add-to-wallet/" \
     -H "Authorization: Bearer <admin_token>" \
     -H "Content-Type: application/json" \
     -d '{
       "user_email": "distributor@example.com",
       "amount": "1000.00",
       "description": "Initial wallet funding"
     }'
```

#### **List Users with Wallet Balance (Admin)**
```bash
curl -X GET "http://localhost:8000/api/auth/admin/users/?user_type=2" \
     -H "Authorization: Bearer <admin_token>"
```

Response shows wallet balance for each user:
```json
{
  "results": [
    {
      "id": 2,
      "email": "distributor@example.com",
      "wallet_balance": "1000.00",
      "wallet_id": 1,
      "user_type": 2,
      "user_type_display": "Distributor"
    }
  ]
}
```

## 📊 Key Features Highlights

### **Integrated Wallet Management**
- **Auto-Creation**: Wallets automatically created for distributors and retailers
- **Balance Visibility**: Wallet balance shown in all admin user management APIs
- **Transaction Tracking**: Complete audit trail of all wallet operations
- **Admin Control**: Only admins can add/debit wallet funds

### **Role-Based Security**
- **IntEnum Types**: Strongly typed user roles (1=Admin, 2=Distributor, 3=Retailer, 4=Client)
- **Permission Checks**: Role-based access control throughout the system
- **Data Isolation**: Users only see data appropriate for their role

### **Optimized Performance**
- **Database Optimization**: Uses `select_related()` for efficient wallet queries
- **Pagination**: Large datasets properly paginated
- **Query Efficiency**: Minimized database calls through smart querying

## 🛡️ Security Features

### **Authentication Security**
- JWT token expiration and refresh
- Strong password validation
- OTP verification for phone numbers
- Secure session management

### **Authorization**
- Role-based permissions
- Admin-only operations protection
- User data isolation
- Wallet access controls

### **Data Protection**
- Input validation and sanitization
- SQL injection prevention
- XSS protection
- CSRF tokens

## 🚀 Deployment

### **Production Checklist**
- [ ] Set `DEBUG=False`
- [ ] Configure production database
- [ ] Set up Redis for caching
- [ ] Configure static files serving
- [ ] Set up SSL certificates
- [ ] Configure monitoring and logging
- [ ] Set up backup procedures
- [ ] Configure email backend for OTP

### **Docker Deployment**
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["gunicorn", "config.wsgi:application"]
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new features
5. Ensure all tests pass
6. Submit a pull request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 📞 Support

For technical support or questions:
- Create an issue in the repository
- Check the API documentation at `/swagger/`
- Review the Django logs for debugging

## 🔄 Version History

### **v1.0.0** (Current)
- Multi-role user system with IntEnum types
- Advanced wallet management with auto-creation
- Margin configuration system
- Complete API documentation with Swagger
- Admin management interface with wallet visibility
- Transaction history tracking
- Role-based security implementation
- Optimized database queries

---

**Built with ❤️ using Django REST Framework**#   p y t h o n - r e c h a r g e - b a c k e n d  
 