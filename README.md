# 🔐 OpenCast Auth Platform

A centralized, multi-tenant authentication and authorization system with REST API and CLI support. This platform provides secure user management, organization-based access control, and comprehensive authentication features for multiple client services and organizations.

## 🌟 Features

### Phase 1 (MVP - Current)

- ✅ **Custom User Authentication**: Email-based authentication with JWT tokens
- ✅ **Multi-tenant Organizations**: Users can belong to multiple organizations
- ✅ **Role-based Access Control**: Owner, Admin, Member, and Viewer roles
- ✅ **RESTful API**: Comprehensive REST API with Swagger documentation
- ✅ **CLI Tool**: Command-line interface for authentication and user management
- ✅ **Admin Interface**: Django admin panel for management
- ✅ **Test Coverage**: Comprehensive test suite with >80% coverage

### Upcoming Phases

- 🔄 **User Profiles & Enhanced Roles** (Phase 2)
- 🔄 **Events & Webhooks** (Phase 3)
- 🔄 **Advanced Authorization & CLI Expansion** (Phase 4)
- 🔄 **Production Hardening** (Phase 5)

## 🛠️ Tech Stack

| Component         | Technology                         |
| ----------------- | ---------------------------------- |
| Language          | Python 3.11+                       |
| Framework         | Django 4.2 + Django REST Framework |
| Database          | PostgreSQL                         |
| Authentication    | JWT (Simple JWT)                   |
| API Documentation | Swagger/OpenAPI (drf-spectacular)  |
| CLI               | Typer + Rich                       |
| Testing           | Pytest + Coverage                  |
| Containerization  | Docker + Docker Compose            |

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Docker and Docker Compose
- Virtual environment (recommended)

### 1. Clone and Setup

```bash
git clone https://github.com/macaris64/opencast-auth.git
cd opencast-auth

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Database Setup

```bash
# Start PostgreSQL with Docker
docker-compose up -d postgres

# Run migrations
python manage.py migrate

# Create superuser (optional)
python manage.py createsuperuser
```

### 3. Start Development Server

```bash
python manage.py runserver
```

The API will be available at:

- **API Root**: http://localhost:8000/api/
- **Swagger Documentation**: http://localhost:8000/api/docs/
- **ReDoc Documentation**: http://localhost:8000/api/redoc/
- **Admin Panel**: http://localhost:8000/admin/

## 📚 API Documentation

### Authentication Endpoints

| Method | Endpoint                   | Description       |
| ------ | -------------------------- | ----------------- |
| POST   | `/api/auth/register/`      | Register new user |
| POST   | `/api/auth/login/`         | User login        |
| POST   | `/api/auth/logout/`        | User logout       |
| POST   | `/api/auth/token/refresh/` | Refresh JWT token |

### User Management

| Method | Endpoint                      | Description              |
| ------ | ----------------------------- | ------------------------ |
| GET    | `/api/users/me/`              | Get current user info    |
| PATCH  | `/api/users/{id}/`            | Update user profile      |
| POST   | `/api/users/change_password/` | Change password          |
| GET    | `/api/users/organizations/`   | Get user's organizations |

### Organizations

| Method | Endpoint                              | Description                |
| ------ | ------------------------------------- | -------------------------- |
| GET    | `/api/organizations/`                 | List organizations         |
| POST   | `/api/organizations/`                 | Create organization        |
| GET    | `/api/organizations/{id}/`            | Get organization details   |
| GET    | `/api/organizations/{id}/members/`    | List organization members  |
| POST   | `/api/organizations/{id}/add_member/` | Add member to organization |

## 🖥️ CLI Usage

The CLI tool provides convenient access to the API from the command line.

### Installation & Configuration

```bash
# The CLI is included in the project
# First, configure the base URL (optional, defaults to localhost:8000)
python -m cli.auth configure --base-url http://localhost:8000/api
```

### Authentication

```bash
# Login
python -m cli.auth login
# Prompts for email and password

# Check current user
python -m cli.auth whoami

# List organizations
python -m cli.auth organizations

# Logout
python -m cli.auth logout
```

### Example Usage

```bash
# Complete authentication flow
$ python -m cli.auth login
Email: admin@example.com
Password: [hidden]
✅ Login successful!
Welcome, admin@example.com

$ python -m cli.auth whoami
┏━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Field    ┃ Value                                                                               ┃
┡━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ ID       │ 1                                                                                   │
│ Email    │ admin@example.com                                                                   │
│ Username │ admin                                                                               │
│ Full Name│ Not set                                                                             │
│ Active   │ Yes                                                                                 │
│ Joined   │ 2024-06-14T11:22:33.123456Z                                                        │
└──────────┴─────────────────────────────────────────────────────────────────────────────────────┘
```

## 🧪 Testing

We use pytest for testing with comprehensive coverage requirements.

### Run Tests

```bash
# Run all tests (with Django settings override)
DJANGO_SETTINGS_MODULE=opencast_auth.settings python -m pytest

# Run with coverage report
DJANGO_SETTINGS_MODULE=opencast_auth.settings python -m pytest --cov=. --cov-report=html --cov-report=term-missing

# Run specific test file
DJANGO_SETTINGS_MODULE=opencast_auth.settings python -m pytest accounts/test_models.py

# Run with verbose output
DJANGO_SETTINGS_MODULE=opencast_auth.settings python -m pytest -v

# Alternative: Use Django test runner
python manage.py test --keepdb
```

### Current Test Coverage: 91% ✅

| Module                    | Coverage |
| ------------------------- | -------- |
| Organizations Models      | 100%     |
| Accounts Models           | 95%      |
| CLI                       | 91%      |
| Accounts Views            | 82%      |
| Accounts Serializers      | 78%      |
| Organizations Serializers | 73%      |
| Organizations Views       | 69%      |

## 🔄 Development Workflow

### Prerequisites for Development

```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Install pre-commit hooks
pre-commit install
```

### Code Quality Tools

```bash
# Format code
black .
isort .

# Lint code
flake8 .

# Security scan
bandit -r .

# Type checking
mypy .
```

### CI/CD Pipeline

This project uses GitHub Actions for continuous integration:

- **Lint**: Code formatting and style checks
- **Test**: Unit and integration tests with 90%+ coverage requirement
- **Security**: Security vulnerability scanning
- **Build**: Django deployment checks
- **CLI Test**: Command-line interface functionality tests

### Branch Protection

- Direct pushes to `master` branch are **disabled**
- All changes must go through **Pull Requests**
- PRs require **1 approval** and **all CI checks to pass**
- **Squash and merge** is the preferred merge strategy

### Test Structure

Tests follow the **Given/When/Then** pattern:

```python
def test_create_user_with_email(self):
    """
    Given: Valid user data
    When: Creating a new user with email
    Then: User should be created successfully
    """
    user = User.objects.create_user(
        email="test@example.com",
        username="testuser",
        password="testpass123"
    )

    assert user.email == "test@example.com"
    # ... more assertions
```

## 🔧 Development

### Code Quality

We maintain high code quality standards:

```bash
# Format code
black .

# Sort imports
isort .

# Lint code
ruff check .

# Type checking
mypy .
```

### Database Migrations

```bash
# Create migrations after model changes
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Show migration status
python manage.py showmigrations
```

### Docker Development

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

## 📁 Project Structure

```
opencast-auth/
├── accounts/              # User authentication app
│   ├── models.py         # Custom User model
│   ├── serializers.py    # DRF serializers
│   ├── views.py          # API views
│   ├── admin.py          # Admin configuration
│   └── test_*.py         # Test files
├── organizations/         # Organization management app
│   ├── models.py         # Organization, Role, Membership models
│   ├── serializers.py    # DRF serializers
│   ├── views.py          # API views
│   ├── admin.py          # Admin configuration
│   └── test_*.py         # Test files
├── cli/                   # CLI application
│   └── auth.py           # CLI commands
├── opencast_auth/         # Django project settings
│   ├── settings.py       # Django configuration
│   └── urls.py           # URL routing
├── docker-compose.yml     # Docker services
├── requirements.txt       # Python dependencies
├── pytest.ini           # Test configuration
└── README.md             # This file
```

## 🔒 Security Features

- **JWT Authentication**: Secure token-based authentication
- **Password Validation**: Django's built-in password validators
- **Permission-based Access**: Role-based access control
- **Admin Security**: Staff-only admin access with proper filters
- **Token Blacklisting**: Logout invalidates refresh tokens

## 🚦 API Status Codes

| Code | Meaning          |
| ---- | ---------------- |
| 200  | Success          |
| 201  | Created          |
| 204  | No Content       |
| 400  | Bad Request      |
| 401  | Unauthorized     |
| 403  | Forbidden        |
| 404  | Not Found        |
| 422  | Validation Error |

## 📈 Current Test Coverage

The project maintains >80% test coverage across all applications:

- **Unit Tests**: Model logic and utilities
- **Integration Tests**: API endpoints and serializers
- **Authentication Tests**: Login, logout, and token management

## 🔄 Development Workflow

1. **Start with failing tests** (TDD approach)
2. **Implement minimal code** to pass tests
3. **Refactor** while keeping tests green
4. **Update documentation** as needed
5. **Run full test suite** before committing

## 📝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Write tests for your changes
4. Implement your changes
5. Ensure all tests pass
6. Update documentation
7. Commit your changes (`git commit -m 'Add amazing feature'`)
8. Push to the branch (`git push origin feature/amazing-feature`)
9. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🤝 Support

For support, please create an issue on GitHub or contact the development team.

---

**Note**: This is Phase 1 (MVP) of the OpenCast Auth Platform. More features and enhancements will be added in subsequent phases as outlined in the project roadmap.
