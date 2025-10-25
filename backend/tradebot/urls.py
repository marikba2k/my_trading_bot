"""
URL configuration for tradebot project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from .views import health
from accounts.views import (
    RegisterView, CredentialTestView, CredentialSaveView, OnboardingStateView
)
from trading.views import KeyInfoView, WalletBalanceView, OpenOrdersView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView


urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/health", health),

    # auth
    path("api/auth/register", RegisterView.as_view()),
    path("api/auth/login", TokenObtainPairView.as_view()),
    path("api/auth/refresh", TokenRefreshView.as_view()),

    # onboarding
    path("api/onboarding/credentials/test", CredentialTestView.as_view()),
    path("api/onboarding/credentials/save", CredentialSaveView.as_view()),
    path("api/onboarding/state", OnboardingStateView.as_view()),
    
    
       # trading (read-only)
    path("api/account/api-key-info", KeyInfoView.as_view()),
    path("api/wallet/balances",      WalletBalanceView.as_view()),
    path("api/orders",               OpenOrdersView.as_view()),
]

