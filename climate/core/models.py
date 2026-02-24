from django.contrib.auth.models import User
from django.db import models


class UserProfile(models.Model):
    ROLE_OFFICER = "officer"
    ROLE_MANAGER = "manager"
    ROLE_AUDITOR = "auditor"
    ROLE_CHOICES = [
        (ROLE_OFFICER, "Officer"),
        (ROLE_MANAGER, "Manager"),
        (ROLE_AUDITOR, "Auditor"),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=ROLE_OFFICER)

    def __str__(self):
        return f"{self.user.username} ({self.role})"


class LocationCatalog(models.Model):
    name = models.CharField(max_length=120, unique=True)
    state = models.CharField(max_length=80, blank=True)
    latitude = models.FloatField()
    longitude = models.FloatField()
    rainfall_index = models.FloatField(default=50)
    flood_index = models.FloatField(default=40)
    cyclone_index = models.FloatField(default=30)
    drought_index = models.FloatField(default=45)
    is_custom = models.BooleanField(default=False)
    created_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["state", "name"]

    def __str__(self):
        return f"{self.name}, {self.state}"


class ClimateCreditApplication(models.Model):
    ID_AADHAAR = "aadhaar"
    ID_PAN = "pan"
    ID_CHOICES = [
        (ID_AADHAAR, "Aadhaar"),
        (ID_PAN, "PAN"),
    ]

    PROPERTY_HOUSE = "House"
    PROPERTY_APARTMENT = "Apartment"
    PROPERTY_FARM = "Farm"
    PROPERTY_COMMERCIAL = "Commercial"
    PROPERTY_CHOICES = [
        (PROPERTY_HOUSE, PROPERTY_HOUSE),
        (PROPERTY_APARTMENT, PROPERTY_APARTMENT),
        (PROPERTY_FARM, PROPERTY_FARM),
        (PROPERTY_COMMERCIAL, PROPERTY_COMMERCIAL),
    ]

    CLIMATE_LOW = "Low"
    CLIMATE_MODERATE = "Moderate"
    CLIMATE_HIGH = "High"
    CLIMATE_SEVERE = "Severe"

    DECISION_AUTO_APPROVE = "Auto Approve"
    DECISION_CONDITIONAL = "Conditional Approve"
    DECISION_REJECT = "Reject"
    DECISION_CHOICES = [
        (DECISION_AUTO_APPROVE, DECISION_AUTO_APPROVE),
        (DECISION_CONDITIONAL, DECISION_CONDITIONAL),
        (DECISION_REJECT, DECISION_REJECT),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="climate_applications")

    borrower_name = models.CharField(max_length=120)
    id_type = models.CharField(max_length=20, choices=ID_CHOICES)
    borrower_id = models.CharField(max_length=20)

    property_type = models.CharField(max_length=20, choices=PROPERTY_CHOICES, default=PROPERTY_HOUSE)
    property_value = models.FloatField(default=0)
    property_risk_score = models.PositiveIntegerField(default=0)

    location_state = models.CharField(max_length=80, default="India")
    location_district = models.CharField(max_length=80)
    latitude = models.FloatField()
    longitude = models.FloatField()

    income = models.FloatField()
    base_credit_score = models.PositiveIntegerField()
    ai_credit_score = models.PositiveIntegerField(default=0)
    esg_aligned_credit_score = models.PositiveIntegerField(default=0)

    loan_amount = models.FloatField()
    is_location_valid = models.BooleanField(default=False)

    rainfall_trend = models.FloatField(default=0)
    flood_history = models.FloatField(default=0)
    cyclone_path_risk = models.FloatField(default=0)
    drought_index = models.FloatField(default=0)

    climate_risk_score = models.PositiveIntegerField(default=0)
    climate_risk_classification = models.CharField(max_length=16, default=CLIMATE_LOW)

    adjusted_credit_score = models.PositiveIntegerField(default=0)

    suggested_interest_rate = models.FloatField(default=0)
    suggested_collateral_ratio = models.FloatField(default=0)
    suggested_tenure_months = models.PositiveIntegerField(default=0)

    decision = models.CharField(max_length=30, choices=DECISION_CHOICES, default=DECISION_CONDITIONAL)
    esg_risk_score = models.PositiveIntegerField(default=0)
    default_probability = models.FloatField(default=0)
    esg_lending_recommendation = models.CharField(max_length=120, default="Standard Monitoring")

    early_warning_flag = models.BooleanField(default=False)
    early_warning_message = models.CharField(max_length=220, blank=True)

    model_algorithm = models.CharField(max_length=60, default="RandomForestRegressor")
    model_confidence = models.FloatField(default=0)

    manager_override_decision = models.CharField(max_length=30, choices=DECISION_CHOICES, blank=True)
    final_decision = models.CharField(max_length=30, choices=DECISION_CHOICES, default=DECISION_CONDITIONAL)

    decision_rationale = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.borrower_name} - {self.final_decision}"


class AuditLog(models.Model):
    ACTION_CREATE = "create"
    ACTION_OVERRIDE = "override"
    ACTION_FINAL_CONFIRM = "final_confirm"

    ACTION_CHOICES = [
        (ACTION_CREATE, "Create Application"),
        (ACTION_OVERRIDE, "Manager Override"),
        (ACTION_FINAL_CONFIRM, "Final Decision Confirmation"),
    ]

    application = models.ForeignKey(ClimateCreditApplication, on_delete=models.CASCADE, related_name="audit_logs")
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=40, choices=ACTION_CHOICES)
    decision = models.CharField(max_length=30, blank=True)
    risk_factors = models.TextField(blank=True)
    details = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]


class PlaceHistory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    place_name = models.CharField(max_length=255)
    latitude = models.FloatField()
    longitude = models.FloatField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.place_name} ({self.latitude}, {self.longitude})"
