# SmartFee Revenue - Deployment Guide

This guide explains how to deploy the SmartFee Revenue application in a production environment.

## Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Git (for version control)
- A production-ready database (SQLite is used by default, but PostgreSQL is recommended for production)

## Production Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd SmartFee_Revenue
   ```

2. **Set up a virtual environment**
   ```bash
   python -m venv .venv
   .venv\Scripts\activate  # On Windows
   # or
   source .venv/bin/activate  # On Unix/Linux/Mac
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   - Copy `.env.production` to `.env`
   - Update the settings in `.env` with your production values
   - **Important**: Set a strong `SECRET_KEY`
   - Configure your database connection string in `DATABASE_URI`

5. **Initialize the database**
   ```bash
   flask db upgrade
   ```

## Running in Production

### Using Gunicorn (Recommended for Production)

```bash
# Start Gunicorn with the production configuration
gunicorn -c gunicorn_config.py wsgi:app
```

### Using the Deployment Script (Windows)

```bash
# Run the deployment script
deploy.bat
```

## Systemd Service (Linux)

Create a systemd service file at `/etc/systemd/system/smartfee.service`:

```ini
[Unit]
Description=SmartFee Revenue Application
After=network.target

[Service]
User=your_username
WorkingDirectory=/path/to/SmartFee_Revenue
Environment="PATH=/path/to/SmartFee_Revenue/.venv/bin"
ExecStart=/path/to/SmartFee_Revenue/.venv/bin/gunicorn -c /path/to/SmartFee_Revenue/gunicorn_config.py wsgi:app
Restart=always

[Install]
WantedBy=multi-user.target
```

Then enable and start the service:

```bash
sudo systemctl daemon-reload
sudo systemctl enable smartfee
sudo systemctl start smartfee
```

## Nginx Configuration (Recommended for Production)

```nginx
server {
    listen 80;
    server_name yourdomain.com;

    location / {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Static files (if any)
    location /static {
        alias /path/to/SmartFee_Revenue/static;
        expires 30d;
    }
}
```

## Security Considerations

1. **Never** run the development server in production
2. Always use HTTPS in production
3. Keep your dependencies up to date
4. Use environment variables for sensitive information
5. Regularly backup your database
6. Set appropriate file permissions

## Monitoring

Check the following log files for issues:
- `gunicorn_error.log` - Gunicorn error logs
- `gunicorn_access.log` - Access logs
- Application logs (configured in your application)

## Updating the Application

1. Pull the latest changes
2. Install/update dependencies
3. Run database migrations (if any)
4. Restart the Gunicorn process

```bash
git pull
pip install -r requirements.txt
flask db upgrade
sudo systemctl restart smartfee  # If using systemd
```
