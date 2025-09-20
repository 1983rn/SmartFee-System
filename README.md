# CWED SmartFee Revenue Collection System

A comprehensive Revenue Collection software designed for educational institutions to manage PTA Fund, School Development Fund (SDF), Boarding Fee, and Other Income payments.

## Features

### Core Functionality
- **Student Management**: Add and manage student records with fee requirements
- **Income Tracking**: Record payments for PTA Fund and SDF separately
- **Expenditure Management**: Track expenses for both fund types
- **Payment Status**: Monitor which students have paid in full vs outstanding balances
- **Receipt Generation**: Printable receipts for students who have completed all payments
- **SMS Reminders**: Send payment reminders to parents (integration ready)

### Reporting
- **Daily/Weekly Reports**: Detailed financial reports with fund separation
- **Real-time Dashboard**: Live statistics and quick actions
- **Export Capabilities**: Export reports in multiple formats

## Deployment Options

### Option 1: Render (Recommended)

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/yourusername/smartfee-revenue)

1. Click the "Deploy to Render" button above
2. Connect your GitHub repository
3. Configure environment variables in the Render dashboard
4. Deploy!

### Option 2: Docker Compose (Local Development)

```bash
# Start the application with PostgreSQL
docker-compose up -d

# Run database migrations
docker-compose exec web flask db upgrade

# Access the application at http://localhost:5000
```

### Option 3: Manual Deployment

1. **Install Dependencies**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Configure Environment**:
   Copy `.env.example` to `.env` and update the values

3. **Initialize Database**:
   ```bash
   flask db upgrade
   ```

4. **Run the Application**:
   ```bash
   gunicorn -c gunicorn_config.py wsgi:app
   ```

### Option 4: Netlify (Frontend only + external backend)

This repository can also be deployed on Netlify to host a static frontend that proxies API calls to a separately hosted Flask backend (e.g., Render, Railway, Fly.io).

1. Ensure your Flask backend is deployed and publicly accessible (e.g., `https://smartfee-backend.onrender.com`).
2. Update `netlify.toml` and replace `https://smartfee-backend.example.com` with your actual backend base URL.
3. Connect this repository to Netlify.
4. In Netlify settings, set:
   - Build command: leave empty (no build step needed)
   - Publish directory: `public`
5. Deploy.

Notes:
- The file `public/index.html` is a minimal landing page with a button to test the `/health` endpoint through the Netlify proxy.
- All routes are proxied to your backend via the `[[redirects]]` rule in `netlify.toml`.
- If your backend enforces CORS, ensure it allows requests from your Netlify domain.
- Make sure your backend exposes a `/health` route. If you use `health.py`, ensure its blueprint is registered with your Flask app.

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `FLASK_APP` | Yes | `wsgi.py` | Entry point of the application |
| `FLASK_ENV` | Yes | `production` | Application environment |
| `SECRET_KEY` | Yes | - | Secret key for session management |
| `DATABASE_URL` | Yes | `sqlite:///app.db` | Database connection string |
| `SMS_API_KEY` | No | - | API key for SMS notifications |

## Technical Stack

- **Backend**: Python 3.9, Flask, SQLAlchemy
- **Frontend**: HTML5, CSS3, JavaScript, Bootstrap 5
- **Database**: PostgreSQL (production), SQLite (development)
- **Deployment**: Docker, Gunicorn, Render

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
- **Icons**: Font Awesome

### Database Schema
- **Students**: ID, name, class, phone, balances, requirements
- **Income**: Payment records with student info and amounts
- **Expenditure**: Expense records with activity details

## SMS Integration

The system includes SMS reminder functionality that can be integrated with services like Twilio, AWS SNS, or other SMS gateway providers.

## Security Notes

- Change the SECRET_KEY in `app.py` for production use
- Use environment variables for sensitive configuration
- Consider using a more robust database for production

## Support

For questions or support, refer to the code documentation or contact the system administrator.
