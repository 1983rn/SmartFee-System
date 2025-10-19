import os
import stat
from pathlib import Path

def setup_production_environment():
    """Set up the production environment with proper directory structure and permissions."""
    try:
        # Create necessary directories
        directories = [
            'logs',
            'instance',
            'backups',
            'static/uploads'
        ]
        
        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {directory}")
        
        # Create log files if they don't exist
        log_files = [
            'logs/gunicorn_access.log',
            'logs/gunicorn_error.log',
            'logs/application.log'
        ]
        
        for log_file in log_files:
            if not Path(log_file).exists():
                Path(log_file).touch()
                print(f"Created log file: {log_file}")
        
        # Set permissions (Unix-like systems)
        if os.name != 'nt':  # Not Windows
            for directory in directories:
                os.chmod(directory, 0o755)  # rwxr-xr-x
            
            for log_file in log_files:
                os.chmod(log_file, 0o644)  # rw-r--r--
        
        print("\nProduction environment setup completed successfully!")
        print("Please make sure to:")
        print("1. Configure your .env file with production settings")
        print("2. Set up a production database")
        print("3. Configure your web server (Nginx/Apache) if needed")
        print("4. Set up SSL certificates for HTTPS")
        
        return True
    except Exception as e:
        print(f"Error setting up production environment: {e}")
        return False

if __name__ == "__main__":
    setup_production_environment()
