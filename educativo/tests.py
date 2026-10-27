from datetime import date as _date

from django.contrib.auth import get_user_model
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from usuarios.models import PerfilUsuaria

# El catálogo inicial lo carga la migración 0002, así que ya existe en la
# base de datos de pruebas.


def dar_plan(usuaria, plan):
    """Crea el perfil de la usuaria con el plan indicado ('premium', 'hospital'...)."""
    return PerfilUsuaria.objects.create(usuario=usuaria, fecha_nacimiento=_date(1995, 5, 1), plan=plan)


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
        # La usuaria de estas pruebas no tiene plan: el contenido premium c4
        # llega bloqueado y sin cuerpo (ver SegmentacionPremiumTests).
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
            'cuerpo': '',
            'minutos_estimados': 10,
            'url_recurso': '',
            'bloqueado': True,
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
                                 'e5': 'psicoeducacion', 'e6': 'psicoeducacion',
                                 'e7': 'tcc', 'e8': 'actMindfulness'})

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


# ---------------------------------------------------------------------------
# Motor de aprendizaje (puntos, niveles, rachas e insignias por ruta).
# Las reglas, niveles e insignias iniciales las cargan las migraciones
# 0010 y 0011.
# ---------------------------------------------------------------------------

from datetime import date, datetime, timedelta
from datetime import timezone as dt_timezone
from unittest import mock


class MotorAprendizajeTests(APITestCase):
    def setUp(self):
        self.usuaria = get_user_model().objects.create_user(username='ana', password='secreta123')
        # Premium para poder leer c4 (premium) y completar la ruta r2.
        dar_plan(self.usuaria, 'premium')
        token = Token.objects.create(user=self.usuaria)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')

    def _leer(self, contenido):
        return self.client.post(
            '/api/educativo/interacciones-contenido/',
            {'contenido': contenido, 'completado': True},
            format='json',
        )

    def _ejercicio(self, ejercicio):
        return self.client.post(
            '/api/educativo/registros-ejercicio/', {'ejercicio': ejercicio}, format='json'
        )

    def _progreso(self):
        return self.client.get('/api/educativo/progreso/').json()

    def test_progreso_inicial(self):
        datos = self._progreso()
        self.assertEqual(datos['puntos_totales'], 0)
        self.assertEqual(datos['nivel']['nombre'], 'Exploradora')
        self.assertEqual(datos['siguiente_nivel']['nombre'], 'Aprendiz')
        self.assertEqual(datos['racha_actual'], 0)
        self.assertEqual({i['ruta_id'] for i in datos['insignias']}, {'r1', 'r2'})
        self.assertFalse(any(i['obtenida'] for i in datos['insignias']))
        self.assertIn('contenido_leido', {r['clave'] for r in datos['reglas']})

    def test_requiere_autenticacion(self):
        self.client.credentials()
        self.assertEqual(self.client.get('/api/educativo/progreso/').status_code, 401)

    def test_leer_contenido_da_puntos_una_sola_vez(self):
        primera = self._leer('c1').json()
        self.assertEqual(primera['gamificacion']['puntos_ganados'], 10)
        segunda = self._leer('c1').json()
        self.assertNotIn('gamificacion', segunda)
        self.assertEqual(self._progreso()['puntos_totales'], 10)

    def test_ejercicio_da_puntos_una_vez_por_dia(self):
        self.assertEqual(self._ejercicio('e1').json()['gamificacion']['puntos_ganados'], 15)
        self.assertEqual(self._ejercicio('e1').json()['gamificacion']['puntos_ganados'], 0)
        # Otro ejercicio el mismo día sí suma.
        self.assertEqual(self._ejercicio('e2').json()['gamificacion']['puntos_ganados'], 15)

    def test_completar_ruta_da_insignia_y_bonus(self):
        self._leer('c2')
        resultado = self._leer('c4').json()['gamificacion']
        self.assertEqual([i['id'] for i in resultado['insignias_nuevas']],
                         [self._progreso()['insignias'][1]['id']])
        # 10 + 10 por leer, 50 de la ruta r2.
        self.assertEqual(self._progreso()['puntos_totales'], 70)
        r2 = [i for i in self._progreso()['insignias'] if i['ruta_id'] == 'r2'][0]
        self.assertTrue(r2['obtenida'])
        self.assertEqual((r2['contenidos_completados'], r2['contenidos_total']), (2, 2))

    def test_la_insignia_no_se_entrega_dos_veces(self):
        self._leer('c2')
        self._leer('c4')
        self.assertEqual(self._progreso()['puntos_totales'], 70)
        self.assertEqual(self._progreso()['puntos_totales'], 70)

    def test_sube_de_nivel(self):
        for c in ('c1', 'c2', 'c3'):
            self._leer(c)  # 30 pts + 50 por completar la ruta r1 = 80
        self.assertEqual(self._progreso()['nivel']['nombre'], 'Aprendiz')
        resultado = self._leer('c4').json()['gamificacion']  # +10 y +50 de la ruta r2 = 140
        self.assertEqual(resultado['puntos_totales'], 140)
        self.assertEqual(resultado['nivel'], 'Aprendiz')
        self.assertIsNone(resultado['subio_de_nivel'])

    def test_aviso_de_subida_de_nivel(self):
        self._leer('c1')
        self._leer('c2')
        resultado = self._leer('c3').json()['gamificacion']  # 30 + 50 de r1 = 80: sube a Aprendiz
        self.assertEqual(resultado['subio_de_nivel'], 'Aprendiz')

    def test_racha_de_aprendizaje(self):
        hoy = date(2026, 3, 1)
        with mock.patch('educativo.aprendizaje._hoy', return_value=hoy):
            self.assertEqual(self._ejercicio('e1').json()['gamificacion']['racha_actual'], 1)
        with mock.patch('educativo.aprendizaje._hoy', return_value=hoy + timedelta(days=1)):
            self.assertEqual(self._ejercicio('e1').json()['gamificacion']['racha_actual'], 2)
        with mock.patch('educativo.aprendizaje._hoy', return_value=hoy + timedelta(days=2)):
            resultado = self._ejercicio('e1').json()['gamificacion']
            self.assertEqual(resultado['racha_actual'], 3)
            # 15 del ejercicio + 10 del bono de racha de 3 días.
            self.assertEqual(resultado['puntos_ganados'], 25)
        # Se salta un día: la racha vigente es 0 y al volver empieza de nuevo.
        with mock.patch('educativo.aprendizaje._hoy', return_value=hoy + timedelta(days=5)):
            self.assertEqual(self._progreso()['racha_actual'], 0)
            self.assertEqual(self._progreso()['racha_maxima'], 3)
            self.assertEqual(self._ejercicio('e1').json()['gamificacion']['racha_actual'], 1)

    # --- Zona horaria: el día se cuenta en hora Colombia, no en UTC ---------
    # 2026-10-27 01:00 UTC son las 8 p. m. del 26 de octubre en Colombia.

    MANANA_COLOMBIA = datetime(2026, 10, 26, 15, 0, tzinfo=dt_timezone.utc)  # 10 a. m. del 26
    NOCHE_COLOMBIA = datetime(2026, 10, 27, 1, 0, tzinfo=dt_timezone.utc)    # 8 p. m. del 26

    def test_el_dia_se_cuenta_en_hora_colombia(self):
        from .aprendizaje import _hoy
        with mock.patch('django.utils.timezone.now', return_value=self.NOCHE_COLOMBIA):
            self.assertEqual(_hoy(), date(2026, 10, 26))

    def test_actividad_de_noche_cuenta_el_mismo_dia(self):
        with mock.patch('django.utils.timezone.now', return_value=self.MANANA_COLOMBIA):
            self.assertEqual(self._ejercicio('e1').json()['gamificacion']['racha_actual'], 1)
        with mock.patch('django.utils.timezone.now', return_value=self.NOCHE_COLOMBIA):
            # Sigue siendo el 26 en Colombia: la racha no sube y el mismo
            # ejercicio no vuelve a dar puntos ese día.
            resultado = self._ejercicio('e1').json()['gamificacion']
            self.assertEqual(resultado['racha_actual'], 1)
            self.assertEqual(resultado['puntos_ganados'], 0)

    def test_fecha_de_insignia_en_hora_colombia(self):
        with mock.patch('django.utils.timezone.now', return_value=self.NOCHE_COLOMBIA):
            self._leer('c2')
            self._leer('c4')  # completa la ruta r2
            r2 = [i for i in self._progreso()['insignias'] if i['ruta_id'] == 'r2'][0]
        self.assertEqual(r2['fecha_obtenida'], '2026-10-26')

    def test_varias_acciones_el_mismo_dia_no_suben_la_racha(self):
        self._leer('c1')
        self._ejercicio('e1')
        self.assertEqual(self._progreso()['racha_actual'], 1)

    def test_cada_usuaria_ve_solo_su_progreso(self):
        self._leer('c1')
        otra = get_user_model().objects.create_user(username='bea', password='secreta123')
        token = Token.objects.create(user=otra)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')
        self.assertEqual(self._progreso()['puntos_totales'], 0)

    def test_regla_inactiva_no_da_puntos(self):
        from .models import ReglaAprendizaje
        ReglaAprendizaje.objects.filter(clave='contenido_leido').update(activa=False)
        self.assertEqual(self._leer('c1').json()['gamificacion']['puntos_ganados'], 0)


# ---------------------------------------------------------------------------
# Segmentación gratuito / premium
# ---------------------------------------------------------------------------


class SegmentacionPremiumTests(APITestCase):
    def setUp(self):
        self.usuaria = get_user_model().objects.create_user(username='ana', password='secreta123')
        self.perfil = dar_plan(self.usuaria, 'gratuito')
        token = Token.objects.create(user=self.usuaria)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')

    def _contenido(self, id_):
        return self.client.get(f'/api/educativo/contenidos/{id_}/').json()

    def _cambiar_plan(self, plan):
        self.perfil.plan = plan
        self.perfil.save()

    def test_gratuita_ve_premium_bloqueado_sin_cuerpo(self):
        c4 = self._contenido('c4')
        self.assertTrue(c4['bloqueado'])
        self.assertEqual((c4['cuerpo'], c4['url_recurso']), ('', ''))
        self.assertTrue(c4['titulo'])  # el título y el resumen siguen visibles
        c1 = self._contenido('c1')
        self.assertFalse(c1['bloqueado'])
        self.assertTrue(c1['cuerpo'])

    def test_premium_y_hospital_ven_todo(self):
        for plan in ('premium', 'hospital'):
            self._cambiar_plan(plan)
            c4 = self._contenido('c4')
            self.assertFalse(c4['bloqueado'], plan)
            self.assertEqual(c4['cuerpo'], 'Contenido de ejemplo premium...', plan)

    def test_ejercicios_premium(self):
        ejercicios = {e['id']: e for e in self.client.get('/api/educativo/ejercicios/').json()}
        self.assertEqual({i for i, e in ejercicios.items() if e['es_premium']}, {'e7', 'e8'})
        self.assertTrue(ejercicios['e7']['bloqueado'])
        self.assertEqual(ejercicios['e7']['instrucciones'], '')
        self.assertFalse(ejercicios['e1']['bloqueado'])

    def test_gratuita_no_puede_completar_premium(self):
        leer = self.client.post('/api/educativo/interacciones-contenido/', {'contenido': 'c4'}, format='json')
        self.assertEqual(leer.status_code, 403)
        hacer = self.client.post('/api/educativo/registros-ejercicio/', {'ejercicio': 'e7'}, format='json')
        self.assertEqual(hacer.status_code, 403)
        self.assertEqual(self.client.get('/api/educativo/interacciones-contenido/').json(), [])
        self.assertEqual(self.client.get('/api/educativo/registros-ejercicio/').json(), [])
        # Lo gratuito sí.
        ok = self.client.post('/api/educativo/registros-ejercicio/', {'ejercicio': 'e1'}, format='json')
        self.assertEqual(ok.status_code, 201)

    def test_premium_puede_completar_premium(self):
        self._cambiar_plan('premium')
        leer = self.client.post('/api/educativo/interacciones-contenido/', {'contenido': 'c4'}, format='json')
        self.assertEqual(leer.status_code, 201)

    def test_sin_perfil_se_trata_como_gratuita(self):
        sin_perfil = get_user_model().objects.create_user(username='bea', password='secreta123')
        token = Token.objects.create(user=sin_perfil)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')
        self.assertTrue(self._contenido('c4')['bloqueado'])

    def test_rutas_bloquean_sus_contenidos_premium(self):
        r2 = self.client.get('/api/educativo/rutas/r2/').json()
        c4 = [c for c in r2['contenidos'] if c['id'] == 'c4'][0]
        self.assertTrue(c4['bloqueado'])
        self.assertEqual(c4['cuerpo'], '')

    def test_progreso_avisa_rutas_que_requieren_premium(self):
        url = '/api/educativo/progreso/'
        insignias = {i['ruta_id']: i for i in self.client.get(url).json()['insignias']}
        self.assertTrue(insignias['r2']['requiere_premium'])   # tiene c4
        self.assertFalse(insignias['r1']['requiere_premium'])
        self._cambiar_plan('premium')
        insignias = {i['ruta_id']: i for i in self.client.get(url).json()['insignias']}
        self.assertFalse(insignias['r2']['requiere_premium'])


# ---------------------------------------------------------------------------
# Recomendaciones automáticas con datos de Seguimiento (app sintomas)
# ---------------------------------------------------------------------------

from django.utils import timezone as dj_timezone  # noqa: E402

from sintomas.models import RegistroCiclo, RegistroEmocional, RegistroSintoma  # noqa: E402

from .recomendaciones import MOTIVO_ANIMO, MOTIVO_DOLOR  # noqa: E402


class RecomendacionesTests(APITestCase):
    def setUp(self):
        self.usuaria = get_user_model().objects.create_user(username='ana', password='secreta123')
        self.perfil = dar_plan(self.usuaria, 'gratuito')
        token = Token.objects.create(user=self.usuaria)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')

    def _recomendaciones(self):
        respuesta = self.client.get('/api/educativo/recomendaciones/')
        self.assertEqual(respuesta.status_code, 200)
        return respuesta.json()

    def _dolor(self, *intensidades, dias_atras=0):
        for intensidad in intensidades:
            registro = RegistroSintoma.objects.create(usuario=self.usuaria, intensidad_dolor=intensidad)
            if dias_atras:
                RegistroSintoma.objects.filter(id=registro.id).update(
                    fecha_hora=dj_timezone.now() - timedelta(days=dias_atras)
                )

    def test_requiere_autenticacion(self):
        self.client.credentials()
        self.assertEqual(self.client.get('/api/educativo/recomendaciones/').status_code, 401)

    def test_sin_datos_de_seguimiento(self):
        datos = self._recomendaciones()
        self.assertFalse(datos['senales']['hay_datos'])
        self.assertEqual(datos['senales']['resumen'], '')
        self.assertEqual(len(datos['contenidos']), 4)
        self.assertEqual(len(datos['ejercicios']), 8)

    def test_dolor_alto_prioriza_dolor_y_tcc(self):
        self._dolor(7, 8)
        datos = self._recomendaciones()
        senales = datos['senales']
        self.assertTrue(senales['dolor_alto'])
        self.assertEqual(senales['dolor_promedio'], 7.5)
        self.assertEqual(senales['resumen'], 'Dolor promedio 7.5/10')
        primero = datos['contenidos'][0]
        self.assertEqual(primero['id'], 'c2')  # dolor crónico y gratuito
        self.assertIn(MOTIVO_DOLOR, primero['motivo'])
        self.assertIn(datos['ejercicios'][0]['id'], {'e1', 'e2', 'e5', 'e6'})  # TCC o psicoeducación gratis
        self.assertIn(MOTIVO_DOLOR, datos['ejercicios'][0]['motivo'])

    def test_dolor_leve_no_cuenta_como_alto(self):
        self._dolor(2, 3)
        senales = self._recomendaciones()['senales']
        self.assertFalse(senales['dolor_alto'])
        self.assertEqual(senales['resumen'], 'Dolor promedio 2.5/10')

    def test_registros_de_hace_mas_de_una_semana_no_cuentan(self):
        self._dolor(9, dias_atras=10)
        self.assertFalse(self._recomendaciones()['senales']['hay_datos'])

    def test_animo_bajo_prioriza_autocuidado_y_act(self):
        RegistroEmocional.objects.create(usuario=self.usuaria, estado_animo=2)
        datos = self._recomendaciones()
        self.assertTrue(datos['senales']['animo_bajo'])
        self.assertEqual(datos['contenidos'][0]['id'], 'c3')  # autocuidado
        self.assertIn(MOTIVO_ANIMO, datos['contenidos'][0]['motivo'])
        primero = datos['ejercicios'][0]
        self.assertIn(primero['id'], {'e3', 'e4'})  # ACT/Mindfulness gratuitos
        self.assertFalse(primero['bloqueado'])

    def test_periodo_activo(self):
        hoy = dj_timezone.localdate()
        RegistroCiclo.objects.create(
            usuario=self.usuaria, fecha_inicio=hoy - timedelta(days=2), abundancia='moderada'
        )
        senales = self._recomendaciones()['senales']
        self.assertTrue(senales['en_periodo'])
        self.assertIn('en tu periodo', senales['resumen'].lower())

    def test_periodo_terminado_no_cuenta(self):
        hoy = dj_timezone.localdate()
        RegistroCiclo.objects.create(
            usuario=self.usuaria, fecha_inicio=hoy - timedelta(days=9),
            fecha_fin=hoy - timedelta(days=4), abundancia='leve',
        )
        self.assertFalse(self._recomendaciones()['senales']['en_periodo'])

    def test_premium_bloqueado_queda_detras_para_gratuita(self):
        self._dolor(8)
        contenidos = self._recomendaciones()['contenidos']
        ids = [c['id'] for c in contenidos]
        c4 = [c for c in contenidos if c['id'] == 'c4'][0]
        self.assertTrue(c4['bloqueado'])
        self.assertLess(ids.index('c2'), ids.index('c4'))

    def test_premium_no_ve_nada_bloqueado(self):
        self.perfil.plan = 'premium'
        self.perfil.save()
        datos = self._recomendaciones()
        self.assertTrue(datos['es_premium'])
        self.assertFalse(any(c['bloqueado'] for c in datos['contenidos'] + datos['ejercicios']))

    def test_preferencias_y_completados(self):
        self.client.put('/api/educativo/preferencias/', {'categorias': ['cat_endometriosis']}, format='json')
        datos = self._recomendaciones()
        self.assertEqual(datos['contenidos'][0]['id'], 'c1')
        self.assertIn('Porque te interesa Endometriosis', datos['contenidos'][0]['motivo'])
        # Al leerlo, baja al final.
        self.client.post('/api/educativo/interacciones-contenido/', {'contenido': 'c1'}, format='json')
        ultimo = self._recomendaciones()['contenidos'][-1]
        self.assertEqual((ultimo['id'], ultimo['completado']), ('c1', True))

    def test_datos_de_otra_usuaria_no_cuentan(self):
        otra = get_user_model().objects.create_user(username='bea', password='secreta123')
        RegistroSintoma.objects.create(usuario=otra, intensidad_dolor=9)
        self.assertFalse(self._recomendaciones()['senales']['hay_datos'])
