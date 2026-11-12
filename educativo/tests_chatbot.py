from unittest import mock

from django.contrib.auth import get_user_model
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from educativo import views
from educativo.views import (
    FRASE_RECHAZO,
    MENSAJE_CRISIS_EMOCIONAL,
    MENSAJE_URGENCIA_FISICA,
)

URL = '/api/educativo/chatbot/'


class ChatbotAlcanceYCrisisTests(APITestCase):
    def setUp(self):
        user = get_user_model().objects.create_user(
            username='chat@test.com', email='chat@test.com', password='x12345678'
        )
        token = Token.objects.create(user=user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')

    def _post(self, texto):
        return self.client.post(URL, {'pregunta': texto}, format='json')

    @mock.patch.object(views, 'generar_respuesta_rag', return_value='respuesta rag')
    def test_crisis_emocional_no_llama_a_gemini(self, rag):
        r = self._post('Ya no quiero vivir con este dolor')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data['respuesta'], MENSAJE_CRISIS_EMOCIONAL)
        self.assertIn('106', r.data['respuesta'])
        self.assertEqual(r.data['opciones_sugeridas'], ['Volver al menú principal'])
        rag.assert_not_called()

    @mock.patch.object(views, 'generar_respuesta_rag', return_value='respuesta rag')
    def test_urgencia_fisica_usa_123(self, rag):
        r = self._post('Tengo un sangrado abundante y me desmayé')
        self.assertEqual(r.data['respuesta'], MENSAJE_URGENCIA_FISICA)
        self.assertIn('123', r.data['respuesta'])
        rag.assert_not_called()

    @mock.patch.object(views, 'generar_respuesta_rag', return_value='respuesta rag')
    def test_palabras_sueltas_ya_no_disparan_crisis(self, rag):
        for texto in ['¿Cómo vivir mejor con endometriosis?', 'Siento daño emocional por el diagnóstico',
                      'Me cuesta respirar profundo cuando estoy ansiosa']:
            r = self._post(texto)
            self.assertEqual(r.data['respuesta'], 'respuesta rag', texto)

    @mock.patch.object(views, 'generar_respuesta_rag', return_value='respuesta rag')
    def test_pregunta_libre_va_a_rag(self, rag):
        r = self._post('Me siento muy triste y sola por mi endometriosis')
        self.assertEqual(r.data['respuesta'], 'respuesta rag')
        rag.assert_called_once()

    @mock.patch.object(views, 'generar_respuesta_rag', return_value='respuesta rag')
    def test_carrusel_pasa_por_rag(self, rag):
        r = self._post('¿Cómo puedo manejar la fatiga crónica asociada a la endometriosis?')
        self.assertEqual(r.data['respuesta'], 'respuesta rag')
        self.assertIn('articulo_relacionado', r.data)

    def test_menu_no_llama_a_rag(self):
        with mock.patch.object(views, 'generar_respuesta_rag') as rag:
            r = self._post('menú')
            self.assertEqual(len(r.data['opciones_sugeridas']), 5)
            r = self._post('2')
            self.assertEqual(len(r.data['opciones_sugeridas']), 6)
            rag.assert_not_called()

    @mock.patch.object(views, 'generar_respuesta_rag', side_effect=views.RagError('sin clave'))
    def test_sin_ia_responde_con_la_base_de_conocimiento(self, rag):
        r = self._post('¿Cómo puedo manejar la fatiga crónica asociada a la endometriosis?')
        self.assertEqual(r.status_code, 200)
        self.assertIn('fatiga', r.data['respuesta'].lower())
        self.assertIn('Fuente:', r.data['respuesta'])
        self.assertEqual(r.data['opciones_sugeridas'], ['Volver al menú principal'])

    @mock.patch.object(views, 'generar_respuesta_rag', side_effect=views.RagError('sin clave'))
    def test_sin_ia_y_sin_coincidencia_da_mensaje_amable(self, rag):
        r = self._post('¿Cuál es la capital de Francia?')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data['respuesta'], views.MENSAJE_SIN_COINCIDENCIA)

    def test_prompt_y_frase_de_rechazo(self):
        self.assertIn(FRASE_RECHAZO, views.SYSTEM_PROMPT_RAG)
        self.assertNotIn('ESHRE', views.SYSTEM_PROMPT_RAG)

    def test_base_de_conocimiento_tiene_los_25_bloques(self):
        from pathlib import Path
        kb = (Path(views.__file__).parent / 'knowledge_base.md').read_text(encoding='utf-8')
        for t in range(1, 6):
            for n in range(1, 6):
                self.assertIn(f'### T{t}-0{n} |', kb)
