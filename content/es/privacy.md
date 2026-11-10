# Política de privacidad

> **Borrador**, última actualización el 10 de noviembre de 2026. Este texto aún no ha sido revisado por un abogado.
>
> Traducción de cortesía; prevalece la versión en inglés.

Esta página explica qué guarda {{ site_name }} sobre ti, para qué, durante cuánto tiempo y qué puedes hacer al respecto. Describe lo que el sitio hace realmente.

## Quién es responsable {#controller}

{{ site_name }} lo gestiona {{ legal_owner_name }}, que es responsable de tus datos (el «responsable del tratamiento»).
Preguntas o solicitudes: [{{ contact_email }}](mailto:{{ contact_email }}).

## Qué guardamos y por qué {#data}

**Cuando inicias sesión con GitHub.** Recibimos de GitHub el id de tu cuenta, tu login, tu nombre, tu biografía, el enlace a tu avatar y los demás campos públicos de tu perfil de GitHub, además de las direcciones de correo de tu cuenta de GitHub. Solo pedimos a GitHub `read:user` y `user:email`: nunca obtenemos acceso a tus repositorios, ni privados ni públicos, a través de tu cuenta. No conservamos tu token de acceso de GitHub después de iniciar sesión. Necesitamos estos datos para crear tu cuenta y reconocerte la próxima vez (ejecución de nuestro acuerdo contigo).

**Tu perfil.** Nombre de usuario, nombre visible, biografía, sitio web e idioma. El nombre y la biografía empiezan con tus valores de GitHub; puedes cambiarlos en Ajustes. Tu nombre de usuario, nombre visible, biografía, sitio web, login de GitHub y el mes en que te uniste son **públicos**.

**Tu dirección de correo.** Se guarda con tu cuenta y solo la ve nuestro equipo. Nunca se muestra en el sitio. El sitio no envía correos; usaríamos la dirección solo para contactarte sobre tu cuenta o una denuncia.

**Tus proyectos.** Todo lo que introduces: nombre, lema, descripción, enlaces, etiquetas, las herramientas de IA que dices haber usado (se muestran como declaradas por el autor), capturas de pantalla y entradas del registro de desarrollo. Los proyectos publicados son públicos; los borradores solo los ven tú y nuestro equipo. Las capturas de pantalla se recodifican al subirlas, lo que elimina metadatos ocultos como los datos de la cámara o la ubicación GPS.

**Comprobaciones de la prueba.** Para conceder sellos comprobamos los hechos nosotros mismos (nuestro interés legítimo en mostrar pruebas en las que se pueda confiar):

- *Authored:* consultamos la API pública de GitHub sobre el repositorio que vinculas y guardamos si eres su propietario, tu número de commits y las fechas de tu primer y último commit. La lista de otros colaboradores de GitHub se lee durante la comprobación y no se guarda.
- *Live:* consultamos los registros DNS del dominio de tu proyecto o descargamos su página para encontrar tu token de verificación.
- *Steady:* solicitamos la dirección de tu proyecto cada pocas horas y guardamos si respondió y con qué rapidez. Estas comprobaciones se conservan **90 días**.

Los resultados se muestran en la página pública de tu proyecto.

**Seguimientos y me gusta.** Guardamos a quién sigues y qué proyectos te gustan. Los demás solo ven los totales, no las listas.

**Denuncias.** Si denuncias un proyecto o un perfil, guardamos el motivo y los detalles que escribas. Solo las ve nuestro equipo. La persona denunciada no sabe quién la denunció.

**Aceptación de los Términos.** Guardamos qué versión de los Términos aceptaste y cuándo.

**Registro de auditoría.** Llevamos un registro interno de los cambios de sellos, las acciones de moderación y las eliminaciones de cuentas, para poder revisar las decisiones más adelante. Solo nuestro equipo puede verlo.

**Lo que no guardamos.** El sitio no registra tu dirección IP. Para limitar los abusos contamos las acciones por cuenta (por ejemplo, me gusta por hora) en memoria temporal durante una hora como máximo. No hay analítica, ni publicidad, ni scripts de seguimiento. Las fuentes se sirven desde nuestro propio servidor.

## Cuánto tiempo lo conservamos {#retention}

- Tu cuenta, perfil, proyectos, seguimientos y me gusta: hasta que los elimines a ellos o a tu cuenta.
- Comprobaciones de disponibilidad: 90 días.
- Sesiones de inicio de sesión: 2 semanas, o hasta que cierres sesión.
- Denuncias que hiciste: se conservan una vez tramitadas. Si eliminas tu cuenta, quedan sin tu nombre.
- Registro de auditoría: se conserva. Las entradas sobre una cuenta eliminada no contienen el nombre de usuario ni el correo.

## Quién más recibe datos {#recipients}

- **GitHub, Inc.** Inicias sesión en github.com y nuestro servidor lee tu perfil y los datos públicos de repositorios desde la API de GitHub. La declaración de privacidad propia de GitHub se aplica a tu uso de GitHub.
- **Los servidores de tu proyecto.** Para las comprobaciones de Live y Steady, nuestro servidor contacta con el DNS de tu dominio y con la dirección de tu proyecto. Ven nuestro servidor, no a ti.
- **Nuestro proveedor de alojamiento**, que ejecuta el servidor y la base de datos por nosotros.

No vendemos tus datos ni los compartimos con fines publicitarios.

## Tus derechos {#rights}

- **Ver y descargar tus datos:** en Ajustes → «Descargar mis datos» obtienes un archivo JSON con tu perfil, tus datos de GitHub, proyectos, registro de desarrollo, me gusta, seguimientos y las denuncias que hiciste.
- **Corregirlos:** edita tu perfil en Ajustes y tus proyectos en sus páginas.
- **Eliminarlos:** Ajustes → «Eliminar cuenta». Esto elimina de inmediato tu perfil y todos tus proyectos, me gusta y seguimientos, y no se puede deshacer. Tu nombre de usuario queda libre.
- **Oponerte o reclamar:** escribe a [{{ contact_email }}](mailto:{{ contact_email }}). Si vives en la UE, el Reino Unido o Ucrania, también puedes reclamar ante tu autoridad de protección de datos.

## Cookies {#cookies}

Usamos solo las cookies que el sitio necesita para funcionar. Consulta la [política de cookies](/legal/cookies/).

## Cambios {#changes}

Si esta política cambia, actualizamos la fecha de arriba. Si el cambio es importante, te pediremos que aceptes los Términos actualizados en tu próxima visita.
