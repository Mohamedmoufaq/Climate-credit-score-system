# Testing Checklist - Smart Location Search & Dashboard

## ✅ Verification Steps

### Part 1: Setup & Access
- [ ] Install dependencies: `pip install -r requirements.txt`
- [ ] Run: `python manage.py runserver`
- [ ] Visit: `http://localhost:8000/demo-access/`
- [ ] Confirm auto-login as demo_manager

### Part 2: Dashboard Appearance
- [ ] Dashboard loads cleanly
- [ ] "New Application" button visible in top-right
- [ ] Navigation bar properly styled
- [ ] KPI cards display with values
- [ ] Map shows with CARTO tiles (no 403 error)
- [ ] All panels have proper spacing

### Part 3: Navigation
- [ ] Click "New Application" button
- [ ] New Application form loads
- [ ] All form fields visible
- [ ] No hardcoded state/city dropdowns

### Part 4: Location Search - Basic Testing

#### Test 4.1: Search for City
- [ ] Type "Bangalore" in location field
- [ ] Suggestions appear within 1 second
- [ ] Multiple suggestions shown
- [ ] Shows coordinates in suggestions
- [ ] Click first suggestion
- [ ] Location field updates
- [ ] Latitude field auto-fills (12.9716)
- [ ] Longitude field auto-fills (77.5946)
- [ ] Green confirmation message appears

#### Test 4.2: Search for Different City
- [ ] Clear location field
- [ ] Type "Mumbai"
- [ ] Suggestions appear
- [ ] Click "Mumbai, Maharashtra, India"
- [ ] Coordinates populate (19.0760, 72.8777)

#### Test 4.3: Search for Village
- [ ] Clear field
- [ ] Type "Koramangala"
- [ ] Should find village/locality
- [ ] Click to select
- [ ] Form updates

#### Test 4.4: Search for District
- [ ] Clear field
- [ ] Type "Goa"
- [ ] Multiple Goa results show
- [ ] Click "Goa, India"
- [ ] Coordinates for Goa load

### Part 5: Location Search - Edge Cases

#### Test 5.1: Typing Short Query
- [ ] Type "A" (1 character)
- [ ] No suggestions shown (working as designed)
- [ ] Type "AB" (2 characters)
- [ ] Suggestions may start to appear

#### Test 5.2: Typing Nonexistent Location
- [ ] Type "XYZABCDEF999"
- [ ] "No locations found" message appears

#### Test 5.3: API Timeout Handling
- [ ] (If internet disconnected)
- [ ] Error message shows gracefully
- [ ] Form doesn't break

#### Test 5.4: Suggestion Interaction
- [ ] Hover over suggestions
- [ ] Background color changes (light blue)
- [ ] Cursor changes to pointer
- [ ] Click elsewhere
- [ ] Suggestions hide

### Part 6: Form Submission

#### Test 6.1: Complete Valid Form
- [ ] Select location: "Bangalore"
- [ ] Fill borrower name: "Raj Kumar"
- [ ] ID type: "Aadhaar"
- [ ] ID: "123456789012"
- [ ] Property type: "House"
- [ ] Property value: "5000000"
- [ ] Income: "500000"
- [ ] Credit score: "720"
- [ ] Loan amount: "2000000"
- [ ] Tenure: "60"
- [ ] Click "Preview Real-Time Decision"
- [ ] Decision panel shows with:
  - [ ] Climate Score
  - [ ] Climate Level
  - [ ] Default Probability
  - [ ] AI Credit Score
  - [ ] ESG Score
  - [ ] Interest Rate
  - [ ] Model Confidence %
  - [ ] AI Algorithm name
- [ ] No errors in browser console

#### Test 6.2: Submit Without Location
- [ ] Leave location blank
- [ ] Fill other fields
- [ ] Click submit
- [ ] Error message: "Please search and select a location"

#### Test 6.3: Submit Without Coordinates
- [ ] (Edge case) Try to manually clear lat/lon
- [ ] Should not be possible (readonly fields)
- [ ] Confirm fields are grayed out

#### Test 6.4: Submit Valid Application
- [ ] Select location: "Delhi"
- [ ] Fill all required fields
- [ ] Click "Run AI Climate Credit Decision"
- [ ] Should redirect to dashboard
- [ ] New application appears in dashboard table
- [ ] Application shows correct location

### Part 7: Dashboard Integration

#### Test 7.1: New Application Appears
- [ ] Submit new application
- [ ] Redirect to dashboard
- [ ] New application visible in table
- [ ] Shows location correctly
- [ ] Shows decision

#### Test 7.2: New Application on Map
- [ ] Check geospatial map
- [ ] New location appears as circle marker
- [ ] Color matches risk level
- [ ] Click marker
- [ ] Zooms to location with animation

#### Test 7.3: Multiple Applications
- [ ] Create 3 different applications:
  1. Bangalore (low risk expected)
  2. Mumbai (different risk)
  3. Delhi (different risk)
- [ ] All 3 appear on map
- [ ] Different colors based on risk
- [ ] Dashboard table shows all 3

### Part 8: API Response Validation

#### Test 8.1: Check Real-Time Decision API
- [ ] Fill form with valid location
- [ ] Click "Preview"
- [ ] Open browser DevTools → Network
- [ ] Find `/api/realtime-decision/` request
- [ ] Check request payload has:
  - [ ] `lat` (number)
  - [ ] `lon` (number)
  - [ ] `income` (number)
  - [ ] `credit_score` (number)
- [ ] Check response has:
  - [ ] `climate_score`
  - [ ] `decision`
  - [ ] `model_confidence` (new!)
  - [ ] `model_algorithm` (new!)

#### Test 8.2: Check Location Search Quality
- [ ] Search "Mysore"
- [ ] Open DevTools → Network
- [ ] Check nominatim.openstreetmap.org requests
- [ ] Response should have 8 results

### Part 9: Accessibility

- [ ] Form works on mobile (responsive)
- [ ] Suggestions dropdown fits on screen
- [ ] No horizontal scroll needed
- [ ] Buttons accessible with keyboard
- [ ] Tab navigation works

### Part 10: Performance

- [ ] First page load: <2 seconds
- [ ] Search suggestion appears: <1 second
- [ ] Form submission: <3 seconds
- [ ] No JavaScript errors in console
- [ ] No infinite loops or hangs

---

## 🐛 Common Issues & Fixes

| Issue | Solution |
|-------|----------|
| Suggestions not appearing | Check internet (Nominatim API access needed) |
| Wrong coordinates | Try more specific location name |
| Form won't submit | Check all fields have values, esp. location |
| Styles look broken | Clear browser cache (`Ctrl+Shift+Delete`) |
| Dashboard doesn't load | Try `/demo-access/` URL first |
| Map shows blank | Verify CARTO tiles URL works |

---

## 📋 Deployment Checklist

Before deploying to Render:

- [ ] All tests pass locally
- [ ] No JavaScript errors in console
- [ ] Nominatim API accessible from Render server
- [ ] Settings.py configured correctly
- [ ] Static files configured
- [ ] CSRF_TRUSTED_ORIGINS set
- [ ] SECRET_KEY set as environment variable
- [ ] DEBUG = False in prod

---

## 📊 Test Summary Template

```
Date: _______________
Tester: ______________

Dashboard Tests:
- Access: ☐ Pass ☐ Fail
- Navigation: ☐ Pass ☐ Fail
- Map Display: ☐ Pass ☐ Fail

Location Search Tests:
- City search: ☐ Pass ☐ Fail
- Village search: ☐ Pass ☐ Fail
- Coordinates populate: ☐ Pass ☐ Fail
- Error handling: ☐ Pass ☐ Fail

Form Tests:
- All fields visible: ☐ Pass ☐ Fail
- Validation works: ☐ Pass ☐ Fail
- Submission succeeds: ☐ Pass ☐ Fail
- Application appears on dashboard: ☐ Pass ☐ Fail

Overall: ☐ Ready ☐ Needs Fixes

Issues Found:
_________________________________________________
_________________________________________________
```

---

## 🎯 Success Criteria

✅ System passes all tests when:
1. Location search shows suggestions within 1 second
2. All 3 locations (city, village, district) work
3. Form submits successfully
4. New applications appear on dashboard
5. Map visualization works with correct colors
6. No JavaScript errors in console
7. Dashboard looks professional

---

**Last Updated:** April 16, 2026  
**Status:** Ready for Testing ✅
