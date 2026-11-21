from django.urls import path

from .views import RegistroView, LoginView, MeView, CompletarOnboardingView, ActivarPremiumView, RecuperarPasswordView

urlpatterns = [
    path('registro/', RegistroView.as_view(), name='registro'),
    path('login/', LoginView.as_view(), name='login'),
    path('me/', MeView.as_view(), name='me'),
    path('completar-onboarding/', CompletarOnboardingView.as_view(), name='completar_onboarding'),
    path('activar-premium/', ActivarPremiumView.as_view(), name='activar-premium'),
    path('recuperar-password/', RecuperarPasswordView.as_view(), name='recuperar-password'),
]