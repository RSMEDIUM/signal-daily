# Signal Daily

A Django-based news application built for the HyperionDev capstone project.

[![Python](https://img.shields.io/badge/Python-3.11%2B-blue)]() [![Django](https://img.shields.io/badge/Django-6.0%2B-green)]() [![Docker](https://img.shields.io/badge/Docker-Ready-blue)]()

## Table of Contents
- [Features](#features)
- [Setup with Virtual Environment](#setup-with-virtual-environment)
- [Setup with Docker](#setup-with-docker)
- [Database Configuration](#database-configuration)
- [Documentation](#documentation)
- [Environment Variables](#environment-variables)

## Features
- Custom `SignalDailyUser` model with Reader, Journalist, and Editor roles
- Article publishing with multi-image uploads and minimum photo size validation
- Newsletter creation and management
- Subscription support for publishers and journalists
- Simple security-question password reset workflow
- REST API with token authentication for article access and subscriptions
- Approval signal logic that sends notification emails and logs approved articles
- Modern home page design with featured cards and article lists

## Setup with Virtual Environment

### Prerequisites
- Python 3.11 or higher
- pip package manager

### Steps

1. **Clone the repository**:
   ```bash
   git clone <your-repo-url>
   cd signaldaily
   ```

2. **Create and activate a virtual environment**:
   
   **On Windows (PowerShell)**:
   ```powershell
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   ```
   
   **On macOS/Linux**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables** (optional, for email/database):
   - Copy `.env.example` to `.env`
   - Update values in `.env` as needed
   - **Note**: For development, SQLite is used by default (no setup needed)

5. **Run migrations**:
   ```bash
   python manage.py migrate
   ```

6. **Create a superuser** (admin account):
   ```bash
   python manage.py createsuperuser
   ```
   Follow the prompts to create your admin account.

7. **Collect static files** (for production):
   ```bash
   python manage.py collectstatic
   ```

8. **Start the development server**:
   ```bash
   python manage.py runserver
   ```
   
   The application will be available at `http://127.0.0.1:8000/`

### Default Demo Users
The application creates default demo users for testing:
- **Reader**: `demo_reader` / `readerpass`
- **Journalist**: `demo_writer` / `writerpass`
- **Editor**: `demo_editor` / `editorpass`
- **Admin**: `ryan` / `ryanpass`

## Setup with Docker

### Prerequisites
- Docker installed on your system
- Docker Compose (optional, for multi-container setup)

### Steps

1. **Clone the repository**:
   ```bash
   git clone <your-repo-url>
   cd signaldaily
   ```

2. **Build the Docker image**:
   ```bash
   docker build -t signaldaily .
   ```

3. **Run the container**:
   ```bash
   docker run -p 8000:8000 signaldaily
   ```
   
   The application will be available at `http://localhost:8000/`

### Docker with Environment Variables

To use custom environment variables with Docker:

```bash
docker run -p 8000:8000 \
  -e DB_ENGINE=django.db.backends.mysql \
  -e DB_NAME=signaldaily_db \
  -e DB_USER=signaldaily_user \
  -e DB_PASSWORD=your_password \
  -e DB_HOST=host.docker.internal \
  -e DB_PORT=3306 \
  signaldaily
```

### Docker Playground Testing

You can test this application on [Play with Docker](https://labs.play-with-docker.com/):

1. Click "Add New Instance"
2. Clone and build:
   ```bash
   git clone <your-repo-url>
   cd signaldaily
   docker build -t signaldaily .
   docker run -d -p 8000:8000 signaldaily
   ```
3. Click on the "8000" port link that appears to access the application

## Database Configuration

### SQLite (Default - Development)
The project uses SQLite by default with the database file at `db.sqlite3`.

### MariaDB (Production)
To use MariaDB instead of SQLite:

1. **Install and start MariaDB** (if not already installed):
   - Windows: Download from [mariadb.com](https://mariadb.com/downloads/) or use Windows Package Manager
   - Linux: `apt-get install mariadb-server` or equivalent
   - macOS: `brew install mariadb`

2. **Create database and user**:
   ```sql
   mysql -u root -p
   
   CREATE DATABASE signaldaily_db;
   CREATE USER 'signaldaily_user'@'localhost' IDENTIFIED BY 'your_secure_password';
   GRANT ALL PRIVILEGES ON signaldaily_db.* TO 'signaldaily_user'@'localhost';
   FLUSH PRIVILEGES;
   EXIT;
   ```

3. **Set environment variables** (copy `.env.example` to `.env` and update):
   ```bash
   DB_ENGINE=django.db.backends.mysql
   DB_NAME=signaldaily_db
   DB_USER=signaldaily_user
   DB_PASSWORD=your_secure_password
   DB_HOST=localhost
   DB_PORT=3306
   ```

4. **Load environment variables in PowerShell**:
   ```powershell
   $env:DB_ENGINE = "django.db.backends.mysql"
   $env:DB_NAME = "signaldaily_db"
   $env:DB_USER = "signaldaily_user"
   $env:DB_PASSWORD = "your_secure_password"
   $env:DB_HOST = "localhost"
   $env:DB_PORT = "3306"
   ```

5. **Run migrations**:
   ```bash
   python manage.py migrate
   ```

6. **Migrate existing data** (if moving from SQLite):
   ```bash
   python manage.py dumpdata --exclude auth.permission --exclude contenttypes > data.json
   python manage.py loaddata data.json
   ```

## Documentation

Comprehensive Sphinx documentation is available in the `docs/` directory.

### Viewing Documentation

**Option 1: Open HTML files directly**
- Navigate to `docs/build/index.html` in your browser

**Option 2: Rebuild documentation** (after code changes):
```bash
cd docs
python -m sphinx -b html source build
```

The documentation includes:
- Full API reference for all models, views, and serializers
- Detailed docstrings for all functions and classes
- Module and package organization

## Environment Variables

 Create a `.env` file in the project root with the following variables:

```env
# Database Configuration (optional - defaults to SQLite)
DB_ENGINE=django.db.backends.sqlite3  # or django.db.backends.mysql
DB_NAME=signaldaily_db
DB_USER=signaldaily_user
DB_PASSWORD=your_secure_password
DB_HOST=localhost
DB_PORT=3306

# Email Configuration (optional - for password reset and notifications)
DEFAULT_FROM_EMAIL=noreply@signaldaily.com
SITE_URL=http://localhost:8000

# Django Secret Key (generate your own for production)
SECRET_KEY=your-secret-key-here

# Debug Mode (set to False in production)
DEBUG=True
```

**Important Security Notes**:
- Never commit `.env` files to version control
- The `.env` file is already included in `.gitignore`
- Generate a strong SECRET_KEY for production
- Set DEBUG=False in production environments
- Use environment-specific configurations for database credentials

## Project Structure

```
signaldaily/
├── docs/                      # Sphinx documentation
│   ├── build/                 # Generated HTML documentation
│   └── source/                # Documentation source files
├── newsapp/                   # Main Django application
│   ├── migrations/            # Database migrations
│   ├── templates/             # HTML templates
│   ├── admin.py              # Django admin configuration
│   ├── forms.py              # Form definitions
│   ├── models.py             # Database models
│   ├── serializers.py        # DRF serializers
│   ├── signals.py            # Django signals
│   ├── views.py              # View functions and classes
│   └── permissions.py        # Custom DRF permissions
├── signaldaily/              # Project settings
│   ├── settings.py           # Django settings
│   ├── urls.py               # URL configuration
│   └── wsgi.py               # WSGI configuration
├── static/                   # Static files (CSS, JS)
├── media/                    # User-uploaded files
├── templates/                # Global templates
├── .dockerignore            # Docker ignore file
├── .env.example             # Example environment variables
├── .gitignore               # Git ignore file
├── Dockerfile               # Docker configuration
├── manage.py                # Django management script
├── README.md                # This file
└── requirements.txt         # Python dependencies
```

## Troubleshooting

### Issue: Port 8000 already in use
**Solution**: Use a different port:
```bash
python manage.py runserver 8080
# or with Docker:
docker run -p 8080:8000 signaldaily
```

### Issue: Database connection errors
**Solution**: 
1. Verify database is running (for MySQL/MariaDB)
2. Check environment variables are correctly set
3. Ensure database user has proper permissions
4. For Docker, use `host.docker.internal` instead of `localhost`

### Issue: Static files not loading
**Solution**:
```bash
python manage.py collectstatic --noinput
```

### Issue: Missing dependencies
**Solution**:
```bash
pip install --upgrade -r requirements.txt
```

## Contributing

This is a capstone project for educational purposes. For any issues or suggestions, please open an issue in the repository.

## License

This project is created for educational purposes as part of the HyperionDev bootcamp.

## Notes
- The project configuration supports both SQLite and MariaDB/MySQL seamlessly via environment variables
- Static and media assets are configured in `signaldaily/settings.py`
- `mysql-connector-python` is included in `requirements.txt` for MariaDB support
- The application uses Django's built-in development server (not suitable for production)
- For production deployment, use a proper WSGI server like Gunicorn with Nginx
