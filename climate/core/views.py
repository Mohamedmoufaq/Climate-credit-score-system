import json
import re
from functools import wraps

import numpy as np
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db import IntegrityError
from django.db.models import Avg, Count
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods
from sklearn.ensemble import RandomForestRegressor

from .models import AuditLog, ClimateCreditApplication, LocationCatalog, PlaceHistory, UserProfile


STATE_CITY_DATA = {
    "Tamil Nadu": [
        {"name": "Chennai", "lat": 13.0827, "lon": 80.2707},
        {"name": "Coimbatore", "lat": 11.0168, "lon": 76.9558},
        {"name": "Madurai", "lat": 9.9252, "lon": 78.1198},
        {"name": "Tiruchirappalli", "lat": 10.7905, "lon": 78.7047},
        {"name": "Salem", "lat": 11.6643, "lon": 78.1460},
    ],
    "Maharashtra": [
        {"name": "Mumbai", "lat": 19.0760, "lon": 72.8777},
        {"name": "Pune", "lat": 18.5204, "lon": 73.8567},
        {"name": "Nagpur", "lat": 21.1458, "lon": 79.0882},
        {"name": "Nashik", "lat": 19.9975, "lon": 73.7898},
        {"name": "Aurangabad", "lat": 19.8762, "lon": 75.3433},
    ],
    "Karnataka": [
        {"name": "Bengaluru", "lat": 12.9716, "lon": 77.5946},
        {"name": "Mysuru", "lat": 12.2958, "lon": 76.6394},
        {"name": "Mangaluru", "lat": 12.9141, "lon": 74.8560},
        {"name": "Hubballi", "lat": 15.3647, "lon": 75.1240},
        {"name": "Belagavi", "lat": 15.8497, "lon": 74.4977},
    ],
    "Gujarat": [
        {"name": "Ahmedabad", "lat": 23.0225, "lon": 72.5714},
        {"name": "Surat", "lat": 21.1702, "lon": 72.8311},
        {"name": "Vadodara", "lat": 22.3072, "lon": 73.1812},
        {"name": "Rajkot", "lat": 22.3039, "lon": 70.8022},
        {"name": "Bhavnagar", "lat": 21.7645, "lon": 72.1519},
    ],
    "Uttar Pradesh": [
        {"name": "Lucknow", "lat": 26.8467, "lon": 80.9462},
        {"name": "Kanpur", "lat": 26.4499, "lon": 80.3319},
        {"name": "Varanasi", "lat": 25.3176, "lon": 82.9739},
        {"name": "Agra", "lat": 27.1767, "lon": 78.0081},
        {"name": "Prayagraj", "lat": 25.4358, "lon": 81.8463},
    ],
    "Rajasthan": [
        {"name": "Jaipur", "lat": 26.9124, "lon": 75.7873},
        {"name": "Jodhpur", "lat": 26.2389, "lon": 73.0243},
        {"name": "Udaipur", "lat": 24.5854, "lon": 73.7125},
        {"name": "Kota", "lat": 25.2138, "lon": 75.8648},
        {"name": "Bikaner", "lat": 28.0229, "lon": 73.3119},
    ],
}

_RF_MODEL = None


def get_or_create_profile(user):
    profile, _ = UserProfile.objects.get_or_create(user=user)
    return profile


def derive_climate_profile(lat, lon):
    coastal_factor = max(0.0, 1 - min(abs(lon - 80) / 18, 1))
    south_factor = max(0.0, 1 - min(abs(lat - 12) / 18, 1))
    west_dry = max(0.0, 1 - min(abs(lon - 72) / 12, 1))

    rainfall = float(np.clip(30 + 35 * south_factor + 18 * coastal_factor, 20, 95))
    flood = float(np.clip(18 + 42 * coastal_factor + 20 * south_factor, 10, 95))
    cyclone = float(np.clip(10 + 55 * coastal_factor, 5, 95))
    drought = float(np.clip(20 + 50 * west_dry + 12 * (1 - south_factor), 10, 95))
    return rainfall, flood, cyclone, drought


def seed_default_locations():
    for state, cities in STATE_CITY_DATA.items():
        for city in cities:
            rainfall, flood, cyclone, drought = derive_climate_profile(city["lat"], city["lon"])
            LocationCatalog.objects.get_or_create(
                name=city["name"],
                defaults={
                    "state": state,
                    "latitude": city["lat"],
                    "longitude": city["lon"],
                    "rainfall_index": round(rainfall, 2),
                    "flood_index": round(flood, 2),
                    "cyclone_index": round(cyclone, 2),
                    "drought_index": round(drought, 2),
                },
            )


def get_rf_model():
    global _RF_MODEL
    if _RF_MODEL is not None:
        return _RF_MODEL

    rng = np.random.default_rng(42)
    n = 1800
    rainfall = rng.uniform(10, 95, n)
    flood = rng.uniform(5, 95, n)
    cyclone = rng.uniform(0, 90, n)
    drought = rng.uniform(5, 95, n)
    income = rng.uniform(180000, 3500000, n)
    loan_amount = rng.uniform(100000, 15000000, n)
    credit_score = rng.uniform(300, 900, n)
    property_value = rng.uniform(250000, 25000000, n)

    target = (
        0.24 * rainfall
        + 0.33 * flood
        + 0.17 * cyclone
        + 0.26 * drought
        + 0.0000007 * (loan_amount - income)
        + 0.03 * (740 - credit_score)
        + 0.0000002 * (loan_amount - property_value)
    )
    target = np.clip(target, 1, 95)

    features = np.column_stack([rainfall, flood, cyclone, drought, income, loan_amount, credit_score, property_value])
    model = RandomForestRegressor(
        n_estimators=240,
        max_depth=11,
        min_samples_leaf=3,
        random_state=42,
    )
    model.fit(features, target)
    _RF_MODEL = model
    return model


def is_authorized_role(user):
    role = get_or_create_profile(user).role
    return role in {UserProfile.ROLE_OFFICER, UserProfile.ROLE_MANAGER, UserProfile.ROLE_AUDITOR}


def role_required(allowed_roles):
    def decorator(view_func):
        @wraps(view_func)
        def wrapped(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect("login")
            role = get_or_create_profile(request.user).role
            if role not in allowed_roles:
                return render(request, "unauthorized.html", status=403)
            return view_func(request, *args, **kwargs)

        return wrapped

    return decorator


def is_valid_aadhaar(value):
    return bool(re.fullmatch(r"\d{12}", value))


def is_valid_pan(value):
    return bool(re.fullmatch(r"[A-Z]{5}\d{4}[A-Z]", value))


def is_within_india(lat, lon):
    return 6.0 <= lat <= 38.5 and 68.0 <= lon <= 97.5


def find_or_create_location(state, city, lat, lon, save_custom, user):
    location = LocationCatalog.objects.filter(name__iexact=city).first()
    if location:
        return location, False

    rainfall, flood, cyclone, drought = derive_climate_profile(lat, lon)
    if save_custom:
        location = LocationCatalog.objects.create(
            name=city,
            state=state or "Custom",
            latitude=lat,
            longitude=lon,
            rainfall_index=round(rainfall, 2),
            flood_index=round(flood, 2),
            cyclone_index=round(cyclone, 2),
            drought_index=round(drought, 2),
            is_custom=True,
            created_by=user,
        )
        return location, True

    return LocationCatalog(
        name=city,
        state=state or "India",
        latitude=lat,
        longitude=lon,
        rainfall_index=round(rainfall, 2),
        flood_index=round(flood, 2),
        cyclone_index=round(cyclone, 2),
        drought_index=round(drought, 2),
    ), False


def aggregate_climate_data(location, income, loan_amount):
    exposure = min(20.0, (loan_amount / max(income, 1)) * 1.45)
    rainfall = float(np.clip(location.rainfall_index + exposure * 0.9, 0, 100))
    flood = float(np.clip(location.flood_index + exposure * 1.1, 0, 100))
    cyclone = float(np.clip(location.cyclone_index + exposure * 0.8, 0, 100))
    drought = float(np.clip(location.drought_index + exposure * 0.75, 0, 100))
    return rainfall, flood, cyclone, drought


def predict_default_probability_rf(rainfall, flood, cyclone, drought, income, loan_amount, credit_score, property_value):
    model = get_rf_model()
    features = np.array([[rainfall, flood, cyclone, drought, income, loan_amount, credit_score, property_value]], dtype=float)
    pred = float(model.predict(features)[0])
    return round(float(np.clip(pred, 1, 95)), 2)


def property_risk(property_type, property_value, loan_amount, flood, cyclone):
    property_factor = {
        ClimateCreditApplication.PROPERTY_HOUSE: 1.0,
        ClimateCreditApplication.PROPERTY_APARTMENT: 0.85,
        ClimateCreditApplication.PROPERTY_FARM: 1.25,
        ClimateCreditApplication.PROPERTY_COMMERCIAL: 1.1,
    }.get(property_type, 1.0)

    ltv = (loan_amount / max(property_value, 1)) * 100
    score = (0.4 * ltv) + (0.35 * flood) + (0.25 * cyclone)
    score *= property_factor
    return int(np.clip(round(score), 0, 100))


def climate_analytics(rainfall, flood, cyclone, drought, income, loan_amount, credit_score, property_value):
    default_prob = predict_default_probability_rf(
        rainfall, flood, cyclone, drought, income, loan_amount, credit_score, property_value
    )

    base_climate_score = round(float(np.clip(
        (0.26 * rainfall) + (0.34 * flood) + (0.19 * cyclone) + (0.21 * drought),
        0,
        100,
    )))

    adjusted_climate_score = round(float(np.clip(0.58 * base_climate_score + 0.42 * default_prob, 0, 100)))

    if adjusted_climate_score < 25:
        level = ClimateCreditApplication.CLIMATE_LOW
    elif adjusted_climate_score < 50:
        level = ClimateCreditApplication.CLIMATE_MODERATE
    elif adjusted_climate_score < 75:
        level = ClimateCreditApplication.CLIMATE_HIGH
    else:
        level = ClimateCreditApplication.CLIMATE_SEVERE

    confidence = round(float(np.clip(89 - (abs(base_climate_score - default_prob) * 0.32), 56, 96)), 2)
    return adjusted_climate_score, level, default_prob, confidence


def ai_credit_score(base_credit_score, climate_score, default_probability, property_risk_score):
    score = base_credit_score - (0.45 * climate_score) - (0.35 * default_probability) - (0.2 * property_risk_score)
    return int(np.clip(round(score), 300, 900))


def esg_credit_score(ai_credit, esg_risk):
    return int(np.clip(round(ai_credit - (0.4 * esg_risk)), 300, 900))


def risk_based_pricing(adjusted_credit_score, climate_score, default_probability, requested_tenure):
    interest_rate = round(7.9 + (climate_score * 0.07) + (default_probability * 0.03) + max(0, (700 - adjusted_credit_score) * 0.01), 2)
    collateral_ratio = round(min(85, 18 + (climate_score * 0.55) + (default_probability * 0.2)), 2)
    suggested_tenure = max(12, min(84, int(requested_tenure - (climate_score * 0.25) - (default_probability * 0.1))))
    return interest_rate, collateral_ratio, suggested_tenure


def esg_score_from_risk(climate_score, flood, drought, property_risk_score):
    esg = (climate_score * 0.58) + (flood * 0.16) + (drought * 0.16) + (property_risk_score * 0.10)
    return int(np.clip(round(esg), 0, 100))


def esg_recommendation(esg_score):
    if esg_score >= 75:
        return "Restrict lending with mandatory green mitigation plan"
    if esg_score >= 55:
        return "Conditional lending with ESG covenants"
    return "Standard ESG monitoring"


def decision_engine(adjusted_credit_score, climate_level, loan_amount, default_probability):
    if climate_level in {ClimateCreditApplication.CLIMATE_HIGH, ClimateCreditApplication.CLIMATE_SEVERE}:
        return ClimateCreditApplication.DECISION_REJECT

    if default_probability > 50:
        return ClimateCreditApplication.DECISION_REJECT

    if adjusted_credit_score >= 745 and loan_amount <= 3000000:
        return ClimateCreditApplication.DECISION_AUTO_APPROVE

    if adjusted_credit_score >= 650:
        return ClimateCreditApplication.DECISION_CONDITIONAL

    return ClimateCreditApplication.DECISION_REJECT


def early_warning(default_probability, climate_score, esg_score):
    if default_probability >= 55 or climate_score >= 75:
        return True, "Critical Alert: Immediate portfolio review required"
    if default_probability >= 40 or esg_score >= 65:
        return True, "Warning: Closely monitor repayment and climate events"
    return False, ""


def register_view(request):
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")
        role = request.POST.get("role", UserProfile.ROLE_OFFICER)

        if role not in dict(UserProfile.ROLE_CHOICES):
            role = UserProfile.ROLE_OFFICER

        if not username or not password:
            return render(request, "register.html", {"error": "Username and password are required.", "roles": UserProfile.ROLE_CHOICES})

        try:
            user = User.objects.create_user(username=username, password=password)
            UserProfile.objects.create(user=user, role=role)
        except IntegrityError:
            return render(request, "register.html", {"error": "Username already exists.", "roles": UserProfile.ROLE_CHOICES})

        return redirect("login")

    return render(request, "register.html", {"roles": UserProfile.ROLE_CHOICES})


def login_view(request):
    if request.method == "POST":
        user = authenticate(
            request,
            username=request.POST.get("username", ""),
            password=request.POST.get("password", ""),
        )

        if user:
            login(request, user)
            get_or_create_profile(user)
            if not is_authorized_role(user):
                logout(request)
                return render(request, "unauthorized.html", status=403)
            return redirect("dashboard")

        return render(request, "login.html", {"error": "Invalid username or password."})

    return render(request, "login.html")


def demo_access_view(request):
    user, created = User.objects.get_or_create(username="demo_manager")
    if created:
        user.set_password("Demo@123")
        user.save()

    profile = get_or_create_profile(user)
    profile.role = UserProfile.ROLE_MANAGER
    profile.save(update_fields=["role"])

    login(request, user)
    return redirect("dashboard")


@login_required
def dashboard(request):
    if not is_authorized_role(request.user):
        return render(request, "unauthorized.html", status=403)

    seed_default_locations()
    role = get_or_create_profile(request.user).role
    applications = ClimateCreditApplication.objects.all() if role in {UserProfile.ROLE_MANAGER, UserProfile.ROLE_AUDITOR} else ClimateCreditApplication.objects.filter(user=request.user)

    metrics = applications.aggregate(
        total=Count("id"),
        avg_risk=Avg("climate_risk_score"),
        avg_default=Avg("default_probability"),
        avg_esg=Avg("esg_risk_score"),
        avg_interest=Avg("suggested_interest_rate"),
        avg_ai_credit=Avg("ai_credit_score"),
        avg_esg_credit=Avg("esg_aligned_credit_score"),
    )

    kpis = {
        "total": metrics["total"] or 0,
        "avg_risk": round(metrics["avg_risk"] or 0, 2),
        "avg_default": round(metrics["avg_default"] or 0, 2),
        "avg_esg": round(metrics["avg_esg"] or 0, 2),
        "avg_interest": round(metrics["avg_interest"] or 0, 2),
        "avg_ai_credit": round(metrics["avg_ai_credit"] or 0, 2),
        "avg_esg_credit": round(metrics["avg_esg_credit"] or 0, 2),
        "approved": applications.filter(final_decision=ClimateCreditApplication.DECISION_AUTO_APPROVE).count(),
        "conditional": applications.filter(final_decision=ClimateCreditApplication.DECISION_CONDITIONAL).count(),
        "rejected": applications.filter(final_decision=ClimateCreditApplication.DECISION_REJECT).count(),
        "warnings": applications.filter(early_warning_flag=True).count(),
    }

    severe_flags = applications.filter(climate_risk_classification__in=[ClimateCreditApplication.CLIMATE_HIGH, ClimateCreditApplication.CLIMATE_SEVERE])[:8]
    warning_alerts = applications.filter(early_warning_flag=True)[:10]

    map_points = [
        {
            "district": item.location_district,
            "lat": item.latitude,
            "lon": item.longitude,
            "risk": item.climate_risk_score,
            "decision": item.final_decision,
            "esg": item.esg_risk_score,
        }
        for item in applications[:80]
    ]

    advantages = [
        "AI-integrated climate-aware credit scoring",
        "Borrower + property-level risk analytics",
        "Real-time loan decision engine API",
        "Climate-based interest and pricing recommendation",
        "ML default probability prediction",
        "Operational dashboard for daily officer workflow",
        "Early warning alerts for existing loans",
        "ESG-aligned credit scoring and lending recommendation",
    ]

    return render(
        request,
        "dashboard.html",
        {
            "applications": applications[:40],
            "role": role,
            "kpis": kpis,
            "severe_flags": severe_flags,
            "warning_alerts": warning_alerts,
            "map_points": json.dumps(map_points),
            "advantages": advantages,
        },
    )


@login_required
@role_required({UserProfile.ROLE_OFFICER, UserProfile.ROLE_MANAGER})
def apply_loan(request):
    seed_default_locations()
    states = sorted(set(LocationCatalog.objects.values_list("state", flat=True)))
    location_lookup = {}
    for item in LocationCatalog.objects.all().order_by("state", "name"):
        if item.state not in location_lookup:
            location_lookup[item.state] = []
        location_lookup[item.state].append(
            {
                "name": item.name,
                "lat": item.latitude,
                "lon": item.longitude,
            }
        )

    if request.method == "POST":
        borrower_name = request.POST.get("borrower_name", "").strip()
        id_type = request.POST.get("id_type", "")
        borrower_id = request.POST.get("borrower_id", "").strip().upper()
        location_state = request.POST.get("location_state", "").strip()
        location_city = request.POST.get("location_city", "").strip()
        custom_city = request.POST.get("custom_city", "").strip()
        property_type = request.POST.get("property_type", ClimateCreditApplication.PROPERTY_HOUSE)
        save_location = request.POST.get("save_location") == "on"

        try:
            income = float(request.POST.get("income", 0))
            base_credit_score = int(request.POST.get("credit_score", 0))
            loan_amount = float(request.POST.get("loan_amount", 0))
            property_value = float(request.POST.get("property_value", 0))
            tenure_months = int(request.POST.get("tenure_months", 0))
            latitude = float(request.POST.get("latitude", 0))
            longitude = float(request.POST.get("longitude", 0))
        except ValueError:
            return render(
                request,
                "apply_loan.html",
                {
                    "states": states,
                    "location_lookup": json.dumps(location_lookup),
                    "error": "Please enter valid numeric values.",
                },
            )

        final_city = custom_city or location_city
        if not location_state or not final_city:
            return render(
                request,
                "apply_loan.html",
                {
                    "states": states,
                    "location_lookup": json.dumps(location_lookup),
                    "error": "Select state and city. If city is missing, add a custom city.",
                },
            )

        if not is_within_india(latitude, longitude):
            return render(
                request,
                "apply_loan.html",
                {
                    "states": states,
                    "location_lookup": json.dumps(location_lookup),
                    "error": "Location Error: coordinates are outside India boundary.",
                },
            )

        if id_type == ClimateCreditApplication.ID_AADHAAR and not is_valid_aadhaar(borrower_id):
            return render(
                request,
                "apply_loan.html",
                {
                    "states": states,
                    "location_lookup": json.dumps(location_lookup),
                    "error": "Aadhaar must be exactly 12 digits.",
                },
            )

        if id_type == ClimateCreditApplication.ID_PAN and not is_valid_pan(borrower_id):
            return render(
                request,
                "apply_loan.html",
                {
                    "states": states,
                    "location_lookup": json.dumps(location_lookup),
                    "error": "PAN must match format: AAAAA9999A.",
                },
            )

        location, created_custom = find_or_create_location(
            location_state,
            final_city,
            latitude,
            longitude,
            save_location or bool(custom_city),
            request.user,
        )

        rainfall, flood, cyclone, drought = aggregate_climate_data(location, income, loan_amount)
        property_risk_score = property_risk(property_type, property_value, loan_amount, flood, cyclone)

        climate_score, climate_level, default_probability, model_confidence = climate_analytics(
            rainfall,
            flood,
            cyclone,
            drought,
            income,
            loan_amount,
            base_credit_score,
            property_value,
        )

        predicted_ai_credit = ai_credit_score(base_credit_score, climate_score, default_probability, property_risk_score)
        adjusted_credit_score = predicted_ai_credit

        interest_rate, collateral_ratio, suggested_tenure = risk_based_pricing(
            adjusted_credit_score,
            climate_score,
            default_probability,
            tenure_months,
        )

        esg_score = esg_score_from_risk(climate_score, flood, drought, property_risk_score)
        esg_credit = esg_credit_score(predicted_ai_credit, esg_score)
        esg_reco = esg_recommendation(esg_score)

        decision = decision_engine(adjusted_credit_score, climate_level, loan_amount, default_probability)
        warning_flag, warning_msg = early_warning(default_probability, climate_score, esg_score)

        rationale = (
            f"AI+Climate integrated scoring={climate_score} ({climate_level}), default probability={default_probability}%, "
            f"property risk={property_risk_score}, AI credit={predicted_ai_credit}, ESG credit={esg_credit}, "
            f"rate={interest_rate}%, collateral={collateral_ratio}%, tenure={suggested_tenure} months."
        )

        if climate_level in {ClimateCreditApplication.CLIMATE_HIGH, ClimateCreditApplication.CLIMATE_SEVERE}:
            rationale += " High climate risk policy triggered mandatory rejection."

        application = ClimateCreditApplication.objects.create(
            user=request.user,
            borrower_name=borrower_name,
            id_type=id_type,
            borrower_id=borrower_id,
            property_type=property_type,
            property_value=property_value,
            property_risk_score=property_risk_score,
            location_state=location_state,
            location_district=final_city,
            latitude=latitude,
            longitude=longitude,
            income=income,
            base_credit_score=base_credit_score,
            ai_credit_score=predicted_ai_credit,
            esg_aligned_credit_score=esg_credit,
            loan_amount=loan_amount,
            is_location_valid=True,
            rainfall_trend=round(rainfall, 2),
            flood_history=round(flood, 2),
            cyclone_path_risk=round(cyclone, 2),
            drought_index=round(drought, 2),
            climate_risk_score=climate_score,
            climate_risk_classification=climate_level,
            adjusted_credit_score=adjusted_credit_score,
            suggested_interest_rate=interest_rate,
            suggested_collateral_ratio=collateral_ratio,
            suggested_tenure_months=suggested_tenure,
            decision=decision,
            esg_risk_score=esg_score,
            default_probability=default_probability,
            esg_lending_recommendation=esg_reco,
            early_warning_flag=warning_flag,
            early_warning_message=warning_msg,
            model_algorithm="RandomForestRegressor",
            model_confidence=model_confidence,
            final_decision=decision,
            decision_rationale=rationale,
        )

        risk_factors = (
            f"rain={application.rainfall_trend}, flood={application.flood_history}, cyclone={application.cyclone_path_risk}, "
            f"drought={application.drought_index}, property_risk={application.property_risk_score}, "
            f"ai_confidence={application.model_confidence}%"
        )

        AuditLog.objects.create(
            application=application,
            user=request.user,
            action=AuditLog.ACTION_CREATE,
            decision=application.final_decision,
            risk_factors=risk_factors,
            details=f"Application created and scored. Custom location created={created_custom}.",
        )

        AuditLog.objects.create(
            application=application,
            user=request.user,
            action=AuditLog.ACTION_FINAL_CONFIRM,
            decision=application.final_decision,
            risk_factors=risk_factors,
            details="Final decision confirmed.",
        )

        return redirect("dashboard")

    return render(
        request,
        "apply_loan.html",
        {
            "states": states,
            "location_lookup": json.dumps(location_lookup),
        },
    )


@login_required
@role_required({UserProfile.ROLE_OFFICER, UserProfile.ROLE_MANAGER})
@require_http_methods(["POST"])
def realtime_decision_api(request):
    try:
        payload = json.loads(request.body.decode("utf-8"))
        income = float(payload.get("income", 0))
        base_credit_score = int(payload.get("credit_score", 0))
        loan_amount = float(payload.get("loan_amount", 0))
        property_value = float(payload.get("property_value", 0))
        tenure_months = int(payload.get("tenure_months", 0))
        property_type = str(payload.get("property_type", ClimateCreditApplication.PROPERTY_HOUSE))
        lat = float(payload.get("lat", 0))
        lon = float(payload.get("lon", 0))
    except (TypeError, ValueError, json.JSONDecodeError):
        return JsonResponse({"error": "Invalid input"}, status=400)

    rainfall, flood, cyclone, drought = derive_climate_profile(lat, lon)
    rainfall, flood, cyclone, drought = aggregate_climate_data(
        LocationCatalog(
            name="Temp",
            state="Temp",
            latitude=lat,
            longitude=lon,
            rainfall_index=rainfall,
            flood_index=flood,
            cyclone_index=cyclone,
            drought_index=drought,
        ),
        income,
        loan_amount,
    )

    property_risk_score = property_risk(property_type, property_value, loan_amount, flood, cyclone)
    climate_score, climate_level, default_probability, _ = climate_analytics(
        rainfall, flood, cyclone, drought, income, loan_amount, base_credit_score, property_value
    )
    ai_credit = ai_credit_score(base_credit_score, climate_score, default_probability, property_risk_score)
    esg_score = esg_score_from_risk(climate_score, flood, drought, property_risk_score)
    esg_credit = esg_credit_score(ai_credit, esg_score)
    interest_rate, collateral_ratio, suggested_tenure = risk_based_pricing(ai_credit, climate_score, default_probability, tenure_months)
    decision = decision_engine(ai_credit, climate_level, loan_amount, default_probability)

    return JsonResponse(
        {
            "climate_score": climate_score,
            "climate_level": climate_level,
            "default_probability": default_probability,
            "ai_credit_score": ai_credit,
            "esg_score": esg_score,
            "esg_credit_score": esg_credit,
            "interest_rate": interest_rate,
            "collateral_ratio": collateral_ratio,
            "suggested_tenure": suggested_tenure,
            "decision": decision,
        }
    )


@login_required
@role_required({UserProfile.ROLE_MANAGER})
@require_http_methods(["POST"])
def override_decision(request, app_id):
    application = get_object_or_404(ClimateCreditApplication, id=app_id)
    override = request.POST.get("override_decision", "")

    valid_decisions = {choice[0] for choice in ClimateCreditApplication.DECISION_CHOICES}
    if override not in valid_decisions:
        return redirect("dashboard")

    if application.climate_risk_classification in {ClimateCreditApplication.CLIMATE_HIGH, ClimateCreditApplication.CLIMATE_SEVERE} and override != ClimateCreditApplication.DECISION_REJECT:
        return redirect("dashboard")

    application.manager_override_decision = override
    application.final_decision = override
    application.save(update_fields=["manager_override_decision", "final_decision", "updated_at"])

    AuditLog.objects.create(
        application=application,
        user=request.user,
        action=AuditLog.ACTION_OVERRIDE,
        decision=override,
        risk_factors=(
            f"climate_score={application.climate_risk_score}, adjusted_credit={application.adjusted_credit_score}, "
            f"esg={application.esg_risk_score}, default={application.default_probability}"
        ),
        details="Manager override applied.",
    )

    AuditLog.objects.create(
        application=application,
        user=request.user,
        action=AuditLog.ACTION_FINAL_CONFIRM,
        decision=override,
        details="Final decision reconfirmed after manager override.",
    )

    return redirect("dashboard")


@login_required
@require_http_methods(["GET", "POST"])
def place_history_api(request):
    if request.method == "GET":
        items = PlaceHistory.objects.filter(user=request.user)[:12]
        data = [
            {
                "place": item.place_name,
                "lat": f"{item.latitude:.4f}",
                "lon": f"{item.longitude:.4f}",
            }
            for item in items
        ]
        return JsonResponse({"items": data})

    try:
        payload = json.loads(request.body.decode("utf-8"))
        place = str(payload.get("place", "")).strip()
        lat = round(float(payload.get("lat")), 4)
        lon = round(float(payload.get("lon")), 4)
    except (ValueError, TypeError, json.JSONDecodeError):
        return JsonResponse({"error": "Invalid payload"}, status=400)

    if not place:
        return JsonResponse({"error": "Place is required"}, status=400)

    PlaceHistory.objects.filter(user=request.user, latitude=lat, longitude=lon).delete()
    PlaceHistory.objects.create(
        user=request.user,
        place_name=place[:255],
        latitude=lat,
        longitude=lon,
    )

    stale = PlaceHistory.objects.filter(user=request.user).order_by("-created_at")[12:]
    if stale:
        stale.delete()

    return JsonResponse({"ok": True})


@login_required
@require_http_methods(["POST"])
def clear_place_history_api(request):
    PlaceHistory.objects.filter(user=request.user).delete()
    return JsonResponse({"ok": True})
