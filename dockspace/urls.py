from django.urls import path, re_path

from . import views

urlpatterns = [
    path('', views.root_redirect, name='root'),
    path('login/', views.account_login, name='account_login'),
    path('logout/', views.account_logout, name='account_logout'),
    path('register/', views.account_register, name='account_register'),
    path('recoverpw/', views.account_recoverpw, name='account_recoverpw'),
    path('login/totp/', views.account_totp, name='account_totp'),
    path('profile/', views.account_profile, name='account_profile'),
    path('profile/<int:account_id>/', views.account_profile, name='account_profile_admin'),
    path('management/', views.management_dashboard, name='management'),
    path('404/', views.page_not_found_view, name='page_404'),
    re_path(r'^media/(?P<path>.*)$', views.protected_media, name='protected_media'),
]
