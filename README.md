# Signal Daily

A Django-based news application built for the HyperionDev capstone project.

## Features
- Custom `SignalDailyUser` model with Reader, Journalist, and Editor roles
- Article publishing with multi-image uploads and minimum photo size validation
- Newsletter creation and management
- Subscription support for publishers and journalists
- Simple security-question password reset workflow
- REST API with token authentication for article access and subscriptions
- Approval signal logic that sends notification emails and logs approved articles
- Modern home page design with featured cards and article lists

## Setup
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Run migrations:
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```
3. Create a superuser:
   ```bash
   python manage.py createsuperuser
   ```
4. Start the development server:
   ```bash
   python manage.py runserver
   ```

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

## Notes
- The project configuration supports both SQLite and MariaDB/MySQL seamlessly via environment variables.
- Static and media assets are configured in `signaldaily/settings.py`.
- `mysql-connector-python` is included in `requirements.txt` for MariaDB support.
