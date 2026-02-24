from django.urls import path

from . import views

urlpatterns = [
    path("", views.login_view, name="login"),
    path("register/", views.register_view, name="register"),
    path("demo-access/", views.demo_access_view, name="demo_access"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("apply/", views.apply_loan, name="apply"),
    path("api/realtime-decision/", views.realtime_decision_api, name="realtime_decision_api"),
    path("override/<int:app_id>/", views.override_decision, name="override_decision"),
    path("api/place-history/", views.place_history_api, name="place_history_api"),
    path("api/place-history/clear/", views.clear_place_history_api, name="clear_place_history_api"),
]
