# Climate Risk–Aware Credit Decision Support System

**Production-Ready Fintech Application** | Django 4.2 | AI-Powered Credit Scoring | Climate-Integrated Underwriting

## 🚀 Quick Start

### Local Development
```bash
# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Start development server
python manage.py runserver
```

### Demo Access
- Navigate to: `http://localhost:8000`
- Click **"Demo Access"** for instant manager-level login
- Credentials: `demo_manager` / `Demo@123`

## 🎯 Key Features

✅ **AI-Powered Credit Scoring** — RandomForestRegressor with 0-100 scale  
✅ **Climate Risk Integration** — Rainfall, flood, cyclone, drought analysis  
✅ **Dynamic Location Search** — Nominatim API for all India locations  
✅ **Real-Time Decision Engine** — Auto Approve / Conditional / Reject logic  
✅ **ESG-Aligned Lending** — Environmental, Social, Governance scoring  
✅ **Geospatial Visualization** — CARTO Leaflet.js risk mapping  
✅ **Role-Based Access** — Officer / Manager / Auditor dashboards  

## 📊 Decision Logic

| Credit Score | Climate Risk | Decision |
|---|---|---|
| ≥ 80 | Low/Medium | ✅ Auto Approve |
| 60-79 | Low/Medium | ⚠️ Conditional |
| < 60 | Any | ❌ Reject |
| Any | High/Severe | ❌ Reject |
| > 50% Default Prob | Any | ❌ Reject |

## 🌍 Deployment (Render.com)

### Prerequisites
- GitHub account with repository
- Render.com account
- Environment variables configured

### Deployment Steps

1. **Push to GitHub**
   ```bash
   git add .
   git commit -m "Production deployment"
   git push origin main
   ```

2. **Connect to Render**
   - Go to [render.com/dashboard](https://render.com/dashboard)
   - Click "New" → "Web Service"
   - Connect GitHub repository
   - Choose `render.yaml` as config

3. **Set Environment Variables**
   - `SECRET_KEY`: Generate strong key
   - `DEBUG`: Set to `False`
   - `DATABASE_URL`: Use PostgreSQL for production

4. **Deploy**
   - Render will auto-run `build.sh`
   - Monitor deployment logs
   - Application available at provided URL

## 📁 Project Structure

```
climate/
├── manage.py
├── requirements.txt
├── render.yaml
├── build.sh
├── .env.example
├── climate_credit/
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
└── core/
    ├── models.py
    ├── views.py
    ├── urls.py
    ├── migrations/
    ├── static/core/
    │   └── styles.css
    └── templates/
        ├── dashboard.html
        ├── apply_loan.html
        ├── login.html
        └── ...
```

## 🔐 Security

- CSRF protection enabled
- SSL/TLS enforced on Render
- Secure password hashing
- Input validation on all forms
- No hardcoded secrets (use environment variables)

## 📱 User Roles

1. **Officer** — Submit loan applications, view own dashboard
2. **Manager** — Approve/reject applications, override decisions, view all applications
3. **Auditor** — Read-only access to all applications and decisions

## 🛠️ Troubleshooting

**"New Applicant button not visible"**
- User must be authenticated and have assigned role (Officer/Manager/Auditor)
- Roles auto-assigned on first login (defaults to Officer)

**"Duplicate applications showing"**
- System prevents duplicate submissions within same location/state
- Check database for orphaned records: `python manage.py shell`

**"Map showing 403 Error"**
- Using CARTO tiles (no authentication required)
- Check browser console for CORS issues

**"Render deployment fails"**
- Verify `requirements.txt` is up to date
- Check `settings.py` for SECRET_KEY and ALLOWED_HOSTS
- Review `build.sh` execution logs on Render dashboard

## 📚 Additional Documentation

- [Smart Location Search Guide](climate/README_SMART_LOCATION.md)
- [Testing Checklist](climate/TESTING_CHECKLIST.md)
- [Implementation Summary](climate/IMPLEMENTATION_SUMMARY.md)
- [Quick Reference](climate/QUICK_REFERENCE.md)

## 📞 Support

For issues or questions:
1. Check [QUICKSTART.md](climate/QUICKSTART.md)
2. Review [TESTING_CHECKLIST.md](climate/TESTING_CHECKLIST.md)
3. Inspect application logs on Render dashboard

---

**Status**: ✅ Production Ready  
**Last Updated**: 2024  
**License**: Proprietary
