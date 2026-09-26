from django.contrib.auth import authenticate
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import PerfilUsuaria
from .serializers import PerfilSerializer, RegistroSerializer


class RegistroView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegistroSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        token, _ = Token.objects.get_or_create(user=user)
        return Response(
            {'token': token.key, 'usuario_id': user.id, 'username': user.username},
            status=status.HTTP_201_CREATED,
        )


class LoginView(APIView):
    """
    Login con mensaje de error en español. Reemplaza la vista por defecto
    de DRF (obtain_auth_token), cuyo mensaje viene en inglés.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        user = authenticate(username=username, password=password)
        if user is None:
            return Response(
                {'detail': 'Usuario o contraseña incorrectos.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        token, _ = Token.objects.get_or_create(user=user)
        return Response({'token': token.key})


class MeView(APIView):
    """Perfil completo de la usuaria autenticada (requiere el token)."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        perfil = PerfilUsuaria.objects.get(usuario=request.user)
        return Response(PerfilSerializer(perfil).data)


class CompletarOnboardingView(APIView):
    """
    Marca que la usuaria ya pasó, al menos una vez, por el flujo de
    diagnóstico + cuestionario inicial. A partir de este momento, sus
    próximos logins van directo al menú principal.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        perfil = PerfilUsuaria.objects.get(usuario=request.user)
        perfil.onboarding_completado = True
        perfil.save()
        return Response({'onboarding_completado': True})