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
            'url_recurso': '',
        })

    def test_contenido_y_ejercicio_devuelven_url_recurso(self):
        from .models import ContenidoEducativo, EjercicioPsicoeducativo
        ContenidoEducativo.objects.filter(id='c2').update(url_recurso='https://www.youtube.com/watch?v=abc123')
        EjercicioPsicoeducativo.objects.filter(id='e3').update(url_recurso='https://open.spotify.com/episode/xyz')
        contenido = self.client.get('/api/educativo/contenidos/c2/').json()
        ejercicio = self.client.get('/api/educativo/ejercicios/e3/').json()
        self.assertEqual(contenido['url_recurso'], 'https://www.youtube.com/watch?v=abc123')
        self.assertEqual(ejercicio['url_recurso'], 'https://open.spotify.com/episode/xyz')

    def test_filtra_contenidos_por_categoria(self):
        respuesta = self.client.get('/api/educativo/contenidos/', {'categoria': 'cat_dolor'})
        self.assertEqual([c['id'] for c in respuesta.json()], ['c2', 'c4'])

    def test_lista_ejercicios(self):
        respuesta = self.client.get('/api/educativo/ejercicios/')
        self.assertEqual(respuesta.status_code, 200)
        tipos = {e['id']: e['tipo'] for e in respuesta.json()}
        self.assertEqual(tipos, {'e1': 'psicoeducacion', 'e2': 'tcc', 'e3': 'actMindfulness', 'e4': 'actMindfulness',
                                 'e5': 'psicoeducacion', 'e6': 'psicoeducacion'})

    def test_rutas_devuelven_contenidos_en_orden(self):
        respuesta = self.client.get('/api/educativo/rutas/')
        self.assertEqual(respuesta.status_code, 200)
        rutas = {r['id']: [c['id'] for c in r['contenidos']] for r in respuesta.json()}
        self.assertEqual(rutas, {'r1': ['c1', 'c2', 'c3'], 'r2': ['c2', 'c4']})

    def test_catalogo_es_de_solo_lectura(self):
        respuesta = self.client.post('/api/educativo/categorias/', {'id': 'x', 'nombre': 'X'})
        self.assertEqual(respuesta.status_code, 405)


class DatosUsuariaTests(APITestCase):
    def setUp(self):
        User = get_user_model()
        self.ana = User.objects.create_user(username='ana', password='secreta123')
        self.bea = User.objects.create_user(username='bea', password='secreta123')
        self._autenticar(self.ana)

    def _autenticar(self, usuaria):
        token, _ = Token.objects.get_or_create(user=usuaria)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')

    # --- Preferencias ---

    def test_preferencias_vacias_al_inicio(self):
        respuesta = self.client.get('/api/educativo/preferencias/')
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta.json(), {'categorias': []})

    def test_guardar_y_reemplazar_preferencias(self):
        self.client.put('/api/educativo/preferencias/', {'categorias': ['cat_dolor', 'cat_autocuidado']}, format='json')
        respuesta = self.client.put('/api/educativo/preferencias/', {'categorias': ['cat_endometriosis']}, format='json')
        self.assertEqual(respuesta.status_code, 200)
        guardadas = self.client.get('/api/educativo/preferencias/').json()['categorias']
        self.assertEqual(guardadas, ['cat_endometriosis'])

    def test_preferencias_rechaza_categoria_inexistente(self):
        respuesta = self.client.put('/api/educativo/preferencias/', {'categorias': ['cat_inventada']}, format='json')
        self.assertEqual(respuesta.status_code, 400)
        self.assertEqual(self.client.get('/api/educativo/preferencias/').json()['categorias'], [])

    def test_preferencias_son_de_cada_usuaria(self):
        self.client.put('/api/educativo/preferencias/', {'categorias': ['cat_dolor']}, format='json')
        self._autenticar(self.bea)
        self.assertEqual(self.client.get('/api/educativo/preferencias/').json()['categorias'], [])

    # --- Progreso de contenidos ---

    def test_marcar_contenido_completado_no_duplica(self):
        primera = self.client.post('/api/educativo/interacciones-contenido/', {'contenido': 'c1'}, format='json')
        segunda = self.client.post('/api/educativo/interacciones-contenido/', {'contenido': 'c1'}, format='json')
        self.assertEqual(primera.status_code, 201)
        self.assertEqual(segunda.status_code, 200)
        lista = self.client.get('/api/educativo/interacciones-contenido/').json()
        self.assertEqual([(i['contenido'], i['completado']) for i in lista], [('c1', True)])

    def test_contenido_inexistente_da_400(self):
        respuesta = self.client.post('/api/educativo/interacciones-contenido/', {'contenido': 'zzz'}, format='json')
        self.assertEqual(respuesta.status_code, 400)

    def test_progreso_es_de_cada_usuaria(self):
        self.client.post('/api/educativo/interacciones-contenido/', {'contenido': 'c1'}, format='json')
        self.client.post('/api/educativo/registros-ejercicio/', {'ejercicio': 'e1'}, format='json')
        self._autenticar(self.bea)
        self.assertEqual(self.client.get('/api/educativo/interacciones-contenido/').json(), [])
        self.assertEqual(self.client.get('/api/educativo/registros-ejercicio/').json(), [])

    # --- Registros de ejercicio ---

    def test_registrar_ejercicio(self):
        respuesta = self.client.post(
            '/api/educativo/registros-ejercicio/',
            {'ejercicio': 'e2', 'respuestas': 'Pensamiento más balanceado', 'utilidad': 4},
            format='json',
        )
        self.assertEqual(respuesta.status_code, 201)
        datos = respuesta.json()
        self.assertEqual((datos['ejercicio'], datos['utilidad']), ('e2', 4))

    def test_registrar_ejercicio_sin_campos_opcionales(self):
        respuesta = self.client.post('/api/educativo/registros-ejercicio/', {'ejercicio': 'e1'}, format='json')
        self.assertEqual(respuesta.status_code, 201)

    def test_utilidad_fuera_de_rango_da_400(self):
        respuesta = self.client.post('/api/educativo/registros-ejercicio/', {'ejercicio': 'e1', 'utilidad': 9}, format='json')
        self.assertEqual(respuesta.status_code, 400)
