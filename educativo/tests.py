from django.contrib.auth import get_user_model
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

# El catálogo inicial lo carga la migración 0002, así que ya existe en la
# base de datos de pruebas.


class CatalogoEducativoTests(APITestCase):
    def setUp(self):
        usuaria = get_user_model().objects.create_user(username='ana', password='secreta123')
        token = Token.objects.create(user=usuaria)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')

    def test_requiere_autenticacion(self):
        self.client.credentials()
        respuesta = self.client.get('/api/educativo/contenidos/')
        self.assertEqual(respuesta.status_code, 401)

    def test_lista_categorias(self):
        respuesta = self.client.get('/api/educativo/categorias/')
        self.assertEqual(respuesta.status_code, 200)
        ids = {c['id'] for c in respuesta.json()}
        self.assertEqual(ids, {'cat_endometriosis', 'cat_dolor', 'cat_autocuidado'})

    def test_detalle_contenido_con_campos_del_frontend(self):
        respuesta = self.client.get('/api/educativo/contenidos/c4/')
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta.json(), {
            'id': 'c4',
            'categoria': 'cat_dolor',
            'titulo': 'Catastrofización del dolor: cómo identificarla',
            'tipo': 'texto',
            'nivel': 'avanzado',
            'es_premium': True,
            'fecha_publicacion': '2026-01-20',
            'resumen': 'Contenido premium con enfoque TCC.',
            'cuerpo': 'Contenido de ejemplo premium...',
            'minutos_estimados': 10,
        })

    def test_filtra_contenidos_por_categoria(self):
        respuesta = self.client.get('/api/educativo/contenidos/', {'categoria': 'cat_dolor'})
        self.assertEqual([c['id'] for c in respuesta.json()], ['c2', 'c4'])

    def test_lista_ejercicios(self):
        respuesta = self.client.get('/api/educativo/ejercicios/')
        self.assertEqual(respuesta.status_code, 200)
        tipos = {e['id']: e['tipo'] for e in respuesta.json()}
        self.assertEqual(tipos, {'e1': 'psicoeducacion', 'e2': 'tcc', 'e3': 'actMindfulness', 'e4': 'actMindfulness'})

    def test_rutas_devuelven_contenidos_en_orden(self):
        respuesta = self.client.get('/api/educativo/rutas/')
        self.assertEqual(respuesta.status_code, 200)
        rutas = {r['id']: [c['id'] for c in r['contenidos']] for r in respuesta.json()}
        self.assertEqual(rutas, {'r1': ['c1', 'c2', 'c3'], 'r2': ['c2', 'c4']})

    def test_catalogo_es_de_solo_lectura(self):
        respuesta = self.client.post('/api/educativo/categorias/', {'id': 'x', 'nombre': 'X'})
        self.assertEqual(respuesta.status_code, 405)
