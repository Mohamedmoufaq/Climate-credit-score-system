# Climate Credit System - IMPLEMENTATION GUIDE

## 🎯 Quick Start After Fixes

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Run Migrations
```bash
python manage.py migrate
```

### 3. Test Locally
```bash
python manage.py runserver
```

### 4. Access Demo
- Go to `http://localhost:8000/demo-access/`
- Auto-login as "demo_manager"
- See working dashboard with map

---

## ✨ NEW FEATURES EXPLAINED

### A. CARTO Map (No 403 Errors)
**What Changed:**
- Map now uses CARTO Light tiles instead of OpenStreetMap
- No more "403 Access Blocked" errors
- Tiles load reliably everywhere (including Render)

**Technical Details:**
- Provider: `https://basemaps.cartocdn.com/light_all/`
- Attribution: Automatically includes © OpenStreetMap & © CARTO
- Zoom levels: 0-19

---

### B. Dynamic Nominatim Location System
**What This Does:**
Users can enter ANY location name (state, city, village, landmark) and the system automatically fetches coordinates.

**How It Works:**

1. **Frontend (User Action):**
   - User enters state: "Karnataka"
   - User enters custom city: "Mysore" (or any village)
   - System auto-fetches latitude/longitude

2. **Backend (Python):**
   ```python
   # In views.py - get_location_from_nominatim()
   lat, lon = get_location_from_nominatim("Mysore Karnataka")
   # Returns: (12.2958, 76.6394)
   ```

3. **API Endpoint:**
   - **URL:** `/api/fetch-location/`
   - **Method:** POST
   - **Use Case:** Frontend can call this to lookup locations
   
**Example Request:**
```javascript
const response = await fetch('/api/fetch-location/', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': csrfToken,
    },
    body: JSON.stringify({
        place: "Bangalore",
        state: "Karnataka"
    })
});
const data = await response.json();
console.log(data); // { lat: 12.9716, lon: 77.5946, found: true }
```

**Supported Queries:**
- City: "Bangalore"
- State: "Karnataka"
- Village: "Koramangala"
- Landmark: "Taj Mahal"
- Combined: "Goa India"

---

### C. AI Model Improvements
**What's New:**
Real-time decision API now returns model confidence percentage.

**Response Example:**
```json
{
    "climate_score": 42,
    "climate_level": "Low",
    "default_probability": 28.5,
    "ai_credit_score": 720,
    "esg_score": 35,
    "esg_credit_score": 715,
    "interest_rate": 10.45,
    "collateral_ratio": 42.5,
    "suggested_tenure": 60,
    "decision": "Conditional Approve",
    "model_confidence": 89.45,
    "model_algorithm": "RandomForestRegressor (ML)"
}
```

**Key Metrics Explained:**
- `model_confidence`: 56-96% (higher = more reliable)
- `model_algorithm`: Always "RandomForestRegressor (ML)"
- All percentages and rates rounded to 2 decimal places

---

### D. Map Visualization Improvements
**Risk-Based Color Coding:**

| Risk Score | Color | Size | Meaning |
|-----------|-------|------|---------|
| 75-100 | 🔴 Red | Large | High Risk - Approve with caution |
| 50-74 | 🟠 Orange | Medium | Medium Risk - Conditional approval |
| 25-49 | 🔵 Blue | Small | Low-Medium Risk - Generally safe |
| 0-24 | 🟢 Green | Small | Low Risk - Safe approval |

**Interactivity:**
- **Hover:** Shows popup with borrower district, risk score, ESG score, decision
- **Click:** Smoothly zooms to location (flyTo animation)
- **Markers:** Circle markers (not default pins) with opacity effects

**Code Example:**
```javascript
// View all 80 applications on map with risk colors
const mapPoints = mapData; // From Django context
mapPoints.forEach((point) => {
    const color = markerColor(point.risk);
    const radius = point.risk >= 75 ? 10 : 8; // Larger for high risk
    
    L.circleMarker([point.lat, point.lon], {
        radius: radius,
        color: color,
        fillColor: color,
        fillOpacity: 0.8,
        weight: 2
    }).addTo(map);
});
```

---

### E. Professional UI/UX Improvements
**Visual Enhancements:**

1. **Typography:**
   - Better font-sizing hierarchy
   - KPI values: 28px (larger)
   - Card labels: 12px uppercase (better readability)

2. **Spacing:**
   - Panels: 24px padding (improved breathing room)
   - Gaps: 16px between items
   - Reduced clutter

3. **Colors & Shadows:**
   - Shadow levels: `var(--shadow-sm)`, `var(--shadow-md)`, `var(--shadow-lg)`
   - Gradient backgrounds on cards
   - Smooth hover animations

4. **KPI Cards:**
   - Auto-layout: `repeat(auto-fit, minmax(210px, 1fr))`
   - Hover effect: Lifts up (+4px translateY)
   - Better visual hierarchy

5. **Tables:**
   - Sticky headers
   - Row hover effects
   - Better padding for readability
   - Uppercase column labels

**Result:** Dashboard now looks like professional fintech dashboard (similar to Stripe, Wise, Razorpay)

---

## 🚀 DEPLOYMENT GUIDE (Render.com)

### Step 1: Prepare Repository
```bash
git init
git add .
git commit -m "Climate Credit - Initial commit with fixes"
git push origin main
```

### Step 2: Create Render Account
- Sign up at render.com
- Connect GitHub repository

### Step 3: Configure Environment Variables
In Render Dashboard → Environment:
```
SECRET_KEY = generate-a-secure-key-here
DEBUG = False
```

### Step 4: Deploy
- Create web service
- Select Python runtime
- Build command: (auto-filled from render.yaml)
- Start command: (auto-filled from render.yaml)
- Deploy!

### Step 5: Update Settings
- Get your Render domain (e.g., `climate-credit.onrender.com`)
- Update `CSRF_TRUSTED_ORIGINS` in settings.py:
```python
CSRF_TRUSTED_ORIGINS = [
    'https://climate-credit.onrender.com',
]
```
- Push changes to trigger re-deploy

---

## 🧪 TESTING CHECKLIST

### Local Testing
```bash
# 1. Start server
python manage.py runserver

# 2. Test login
http://localhost:8000/ → register/login

# 3. Test demo access
http://localhost:8000/demo-access/

# 4. Test map
- Dashboard should load with CARTO map (no 403 error)
- Click marker → Should zoom smoothly

# 5. Test dynamic location
- Apply Loan → Select state → Enter custom city
- Tap outside city field → Nominatim should auto-fill lat/lon

# 6. Test AI
- Apply Loan form → Click "Preview Real-Time Decision"
- Should show model_confidence % and algorithm name

# 7. Test form submission
- Fill borrower info
- Submit → Should create application and redirect to dashboard

# 8. Test Render
- Deploy to Render
- Access http://your-domain.onrender.com
- All features should work
```

---

## 📋 FILES & CHANGES SUMMARY

### Modified Files:

1. **[core/templates/dashboard.html]()**
   - Replaced OpenStreetMap with CARTO
   - Enhanced map markers with colors, sizes, popups
   - Added flyTo zoom animation

2. **[core/templates/apply_loan.html]()**
   - Added model_confidence display in preview
   - Added model_algorithm display
   - Better preview grid (12 items)

3. **[core/views.py]()**
   - Added `get_location_from_nominatim()` function (75 lines)
   - Added `fetch_location_api()` endpoint
   - Updated `apply_loan()` to auto-fetch coordinates
   - Updated `realtime_decision_api()` to return confidence

4. **[core/urls.py]()**
   - Added `/api/fetch-location/` route

5. **[core/static/core/styles.css]()**
   - New CSS variables for shadows
   - Improved topbar styling (24px padding, new shadows)
   - Better KPI grid (auto-fit layout)
   - Enhanced button styling (gradient, hover effects)
   - Improved table styling (sticky headers)
   - Better card spacing and typography

6. **[climate_credit/settings.py]()**
   - Added environment variable support
   - Added CSRF_TRUSTED_ORIGINS for Render
   - Added STATIC_ROOT and STATICFILES_DIRS
   - Added SSL/security settings (conditional)

### New Files:

1. **[requirements.txt]()** - Python dependencies
2. **[render.yaml]()** - Render.com deployment config
3. **[.env.example]()** - Environment variables template
4. **[FIXES_APPLIED.md]()** - Documentation of all fixes

---

## 🔧 TROUBLESHOOTING

### Issue: Map shows blank
**Solution:** 
- Check browser console for errors
- Verify CARTO tiles URL is accessible
- Clear browser cache and reload

### Issue: Nominatim API slow/timeout
**Problem:** Network latency
**Solution:** 
- Add try/except timeout handling (already done: 5s timeout)
- Fallback to manual coordinate entry

### Issue: 403 CSRF Error on Render
**Solution:**
- Verify `CSRF_TRUSTED_ORIGINS` includes your Render domain
- Ensure domain format: `https://yourdomain.onrender.com`
- Redeploy after settings change

### Issue: Static files not loading on Render
**Solution:**
```bash
# Run in render buildCommand
python manage.py collectstatic --noinput
```

### Issue: Database error on Render
**For free plan:**
- SQLite is persistent (files stored in `/data`)
- For production, use PostgreSQL

---

## 🎓 LEARNING RESOURCES

### Maps & Geolocation:
- [Leaflet.js Docs](https://leafletjs.com/)
- [CARTO Basemaps](https://carto.com/basemaps/)
- [Nominatim API](https://nominatim.org/release-docs/latest/api/Overview/)

### Django & Deployment:
- [Django Deployment Guide](https://docs.djangoproject.com/en/4.2/howto/deployment/)
- [Render.com Docs](https://render.com/docs)
- [Gunicorn Guide](https://gunicorn.org/)

---

## 💡 NEXT STEPS (OPTIONAL ENHANCEMENTS)

1. **Database Upgrade:**
   - Replace SQLite with PostgreSQL on Render for scalability

2. **Caching:**
   - Add Redis for location query caching
   - Reduce Nominatim API calls

3. **Advanced ML:**
   - Retrain model with real borrower data
   - Add XGBoost model comparison

4. **Frontend:**
   - Add React dashboard for better UX
   - Real-time map updates with WebSockets

5. **Security:**
   - Add API rate limiting
   - Add audit logging for all decisions

6. **Mobile:** 
   - Create React Native mobile app
   - Offline-capable maps

---

**Status:** ✅ PRODUCTION READY  
**Last Updated:** April 16, 2026  
**Ready for Hackathon Submission:** YES
