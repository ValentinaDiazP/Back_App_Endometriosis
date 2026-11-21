from django.contrib.auth import authenticate
from django.contrib.auth.models import User
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

    def delete(self, request):
        user = request.user
        user.delete()
        return Response({'detail': 'Cuenta y datos eliminados correctamente.'}, status=status.HTTP_204_NO_CONTENT)


class RecuperarPasswordView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        username_or_celular = request.data.get('username') or request.data.get('celular')
        nueva_password = request.data.get('password')
        if not username_or_celular or not nueva_password:
            return Response({'detail': 'Usuario/celular y nueva contraseña son obligatorios.'}, status=status.HTTP_400_BAD_REQUEST)
        
        user = User.objects.filter(username=username_or_celular).first()
        if not user:
            perfil = PerfilUsuaria.objects.filter(celular=username_or_celular).first()
            if perfil:
                user = perfil.usuario
        
        if not user:
            return Response({'detail': 'No se encontró una cuenta con ese usuario o celular.'}, status=status.HTTP_404_NOT_FOUND)
        
        user.set_password(nueva_password)
        user.save()
        return Response({'detail': 'Contraseña actualizada exitosamente.'})


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

class ActivarPremiumView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        perfil = PerfilUsuaria.objects.get(usuario=request.user)
        if perfil.plan == 'gratuito':
            perfil.plan = 'premium'
            perfil.save(update_fields=['plan'])
        return Response({'plan': perfil.plan})    
    