"""
URL configuration for ASM project.
"""
from django.contrib import admin
from django.urls import path
from ASMapp import views
from ASMapp.reports import report_builder, generate_report, report_data_api

# Authentication URLs
auth_urls = [
    path('signup/', views.signup_view, name='signup'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
]

# Main page URLs
main_urls = [
    path('', views.landing, name='landing'),
    path('about-us/', views.about_us, name='about-us'),
    path('view/', views.view, name='protected_view'),
    path('help/', views.help_center, name='help_center'),
]

# Scan and results URLs
scan_urls = [
    path('scan/', views.scans_page, name='scan'),
    path('get_subdomains/<str:domain>/', views.get_subdomain, name='get_subdomains'),
    path('get_subdomains/', views.get_subdomains, name='get_all_subdomains'),
    path('save_scan/', views.save_scan, name='save_scan'),
    path('views_scans/', views.my_scans, name='my_scans'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
]

# User profile URLs
profile_urls = [
    path('profile/', views.profile_view, name='profile'),
    path('profile/update/', views.update_profile, name='update_profile'),
    path('profile/change-password/', views.change_password, name='change_password'), 
    path('profile/preferences/', views.update_preferences, name='update_preferences'),
    path('generate-api-key/', views.generate_api_key, name='generate_api_key'),
]

# Additional feature URLs
feature_urls = [
    path('onboarding/', views.onboarding, name='onboarding'),
    path('submit-feedback/', views.submit_feedback, name='submit_feedback'),
    path('search/', views.global_search, name='global_search'),
]

# Admin URL
admin_urls = [
    path('admin/', admin.site.urls),
]

report_urls = [
    path('reports/dashboard/', views.report_dashboard, name='report_dashboard'),
    path('reports/generate/', views.generate_report, name='generate_report'),
    path('check_paths/', views.check_paths, name='check_paths'),
]

# Combine all URL patterns
urlpatterns = []
urlpatterns.extend(auth_urls)
urlpatterns.extend(main_urls)
urlpatterns.extend(scan_urls)
urlpatterns.extend(profile_urls)
urlpatterns.extend(feature_urls)
urlpatterns.extend(admin_urls)
urlpatterns.extend(report_urls)