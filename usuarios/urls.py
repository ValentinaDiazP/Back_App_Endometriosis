from django.urls import path

from .views import CompletarOnboardingView, LoginView, MeView, RegistroView

urlpatterns = [
    path('registro/', RegistroView.as_view(), name='registro'),
    path('login/', LoginView.as_view(), name='login'),
    path('me/', MeView.as_view(), name='me'),
    path('completar-onboarding/', CompletarOnboardingView.as_view(), name='completar_onboarding'),
]