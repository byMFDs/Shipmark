# Política de privacidad

> **Borrador**, última actualización el 11 de noviembre de 2026. Este texto aún no ha sido revisado por un abogado.
>
> Traducción de cortesía; prevalece la versión en inglés.

Esta página explica qué guarda {{ site_name }} sobre ti, para qué, durante cuánto tiempo y qué puedes hacer al respecto. Describe lo que el sitio hace realmente.

## Quién es responsable {#controller}

{{ site_name }} lo gestiona {{ legal_owner_name }}, que es responsable de tus datos (el «responsable del tratamiento»).
Preguntas o solicitudes: [{{ contact_email }}](mailto:{{ contact_email }}).

## Qué guardamos y por qué {#data}

**Cuando inicias sesión con GitHub.** Recibimos de GitHub el id de tu cuenta, tu login, tu nombre, tu biografía, el enlace a tu avatar y los demás campos públicos de tu perfil de GitHub, además de las direcciones de correo de tu cuenta de GitHub. Solo pedimos a GitHub `read:user` y `user:email`: nunca obtenemos acceso a tus repositorios, ni privados ni públicos, a través de tu cuenta. No conservamos tu token de acceso de GitHub después de iniciar sesión. Necesitamos estos datos para crear tu cuenta y reconocerte la próxima vez (ejecución de nuestro acuerdo contigo). Tu usuario de GitHub se actualiza cada vez que inicias sesión, así tu perfil siempre enlaza a tu cuenta actual de GitHub.

**Tu perfil.** Nombre de usuario, nombre visible, biografía, sitio web e idioma. El nombre y la biografía empiezan con tus valores de GitHub; puedes cambiarlos en Ajustes. Tu nombre de usuario, nombre visible, biografía, sitio web, login de GitHub y el mes en que te uniste son **públicos**.

**Tu dirección de correo.** Se guarda con tu cuenta y solo la ve nuestro equipo. Nunca se muestra en el sitio. El sitio no envía correos; usaríamos la dirección solo para contactarte sobre tu cuenta o una denuncia.

**Tus proyectos.** Todo lo que introduces: nombre, lema, descripción, enlaces, etiquetas, las herramientas de IA que dices haber usado (se muestran como declaradas por el autor), capturas de pantalla y entradas del registro de desarrollo. Los proyectos publicados son públicos; los borradores solo los ven tú y nuestro equipo. Las capturas de pantalla se recodifican al subirlas, lo que elimina metadatos ocultos como los datos de la cámara o la ubicación GPS.

**Comprobaciones de la prueba.** Para conceder sellos comprobamos los hechos nosotros mismos (nuestro interés legítimo en mostrar pruebas en las que se pueda confiar):

- *Repo owner:* consultamos la API pública de GitHub sobre el repositorio que enlazas y guardamos su identificador, el identificador de la cuenta propietaria, si es tuyo, su fecha de creación y su campo Website, el primer commit de su historial (identificador y fecha), tu número de commits, las fechas de tu primer y último commit, el número de semanas con commits tuyos y el estado de una revisión manual cuando hace falta. Lo volvemos a comprobar cada semana. La lista de otras personas que contribuyen se lee durante la comprobación y no se guarda. Si usas el archivo de verificación para un repositorio de una organización, también guardamos si se encontró.
- *Live:* consultamos los registros DNS del dominio de tu proyecto o descargamos su página para encontrar tu token de verificación.
- *Steady:* solicitamos la dirección de tu proyecto cada pocas horas y guardamos si respondió y con qué rapidez. Estas comprobaciones se conservan **90 días**.

Los resultados se muestran en la página pública de tu proyecto.

**Seguimientos y me gusta.** Guardamos a quién sigues y qué proyectos te gustan. Los demás solo ven los totales, no las listas.

**Denuncias y moderación.** Si denuncias un proyecto, un perfil o una entrada del registro de cambios (build log), guardamos el motivo y los detalles que escribas. Las ven los moderadores (personas con la insignia de moderador) y nuestro equipo; a la persona denunciada nunca se le dice quién la denunció. Cuando los moderadores deciden, guardamos la decisión y su motivo: un proyecto retirado conserva su contenido y el motivo (solo lo ves tú y el equipo), los campos de perfil vaciados se borran, y los silencios y bloqueos se guardan con su motivo, inicio y fin. Ves el motivo en un aviso en el sitio, que guardamos hasta que elimines tu cuenta. Las decisiones sobre ti y estos avisos se incluyen en «Descargar mis datos».

**Evasión de bloqueos.** Cuando se bloquea una cuenta, guardamos un hash unidireccional con sal de su id de usuario de GitHub (nunca el id), con el motivo y la fecha de fin. Solo sirve para reconocer la misma cuenta de GitHub si vuelve a registrarse durante el bloqueo. Se borra cuando el bloqueo termina o se levanta, también si la cuenta bloqueada se eliminó entretanto.

**Aceptación de los Términos.** Guardamos qué versión de los Términos aceptaste y cuándo.

**Registro de auditoría.** Llevamos un registro interno de los cambios de sellos, las acciones de moderación y las eliminaciones de cuentas, para poder revisar las decisiones más adelante. Solo nuestro equipo puede verlo.

**Direcciones IP y registros.** La aplicación no guarda tu dirección IP y sus propios registros no la contienen. De cada petición de página los registros anotan solo el método, la dirección de la página (sin lo que va después de un `?`), el estado de la respuesta, el tamaño y el tiempo empleado, además de los errores. No contienen datos de tu navegador. Las direcciones de página incluyen nombres de usuario (`/u/<username>/`), así que una línea del registro puede mostrar qué perfil se abrió, pero no quién lo abrió.

**Registro de errores.** Cuando algo falla, la aplicación escribe una entrada breve en un archivo de errores de nuestro servidor: la hora, un número de referencia aleatorio (el que aparece en la página de error), el método de la solicitud, la dirección de la página sin lo que va después de `?` y con los nombres de usuario sustituidos por `[user]`, el estado de la respuesta, la parte del código que falló y el mensaje técnico, del que se eliminan direcciones de correo, direcciones IP y todo lo que parezca una contraseña o una clave. Las páginas no encontradas van a un archivo aparte, cada dirección como mucho una vez por minuto. Estos archivos nunca contienen tu dirección IP, datos del navegador, cookies, lo que escribes en los formularios, tu correo ni tu nombre de usuario. Cada archivo está limitado a 5 MB más 5 copias anteriores; al llegar al límite se borra la más antigua.

> **TODO antes del lanzamiento:** el servidor web que está delante de la aplicación lleva su propio registro de accesos, que por defecto incluye direcciones IP. Aún no se ha decidido qué anota ni cuánto tiempo lo conserva (ni cuánto se conservan los registros de la aplicación). Hay que completarlo, o desactivar el registro de IP, antes de que esta página sea pública.

**Protección contra abusos.** Para limitar los abusos contamos algunas acciones (por ejemplo, me gusta por hora) en la base de datos del sitio. Cada contador es un número asociado a tu cuenta o a un proyecto, sin dirección IP, y se aplica durante 24 horas como máximo. Después deja de usarse, pero la fila puede permanecer en la base de datos hasta que se limpie.

**Analítica y seguimiento.** No hay: ni analítica, ni publicidad, ni scripts de seguimiento. Las fuentes se sirven desde nuestro propio servidor.

**Copias de seguridad.** Cada día hacemos una copia de la base de datos y de las capturas de pantalla subidas, y conservamos cada copia 14 días. Si eliminas tu cuenta, tus datos permanecen en esas copias hasta que se sustituya la última que los contiene, como máximo 14 días después.

## Cuánto tiempo lo conservamos {#retention}

- Tu cuenta, perfil, proyectos, seguimientos y me gusta: hasta que los elimines a ellos o a tu cuenta.
- Comprobaciones de disponibilidad: 90 días.
- Decisiones de moderación sobre ti (silencios, bloqueos, proyectos retirados) y avisos: mientras exista tu cuenta; se borran con ella. Las denuncias sobre ti se conservan sin vínculo con tu cuenta, solo con el nombre de ese momento.
- Hash del id de GitHub de una cuenta bloqueada: solo hasta que el bloqueo termine o se levante.
- Sesiones de inicio de sesión: 2 semanas, o hasta que cierres sesión.
- Denuncias que hiciste: se conservan una vez tramitadas. Si eliminas tu cuenta, quedan sin tu nombre.
- Registro de auditoría: se conserva. Las entradas sobre una cuenta eliminada no contienen el nombre de usuario ni el correo.
- Contadores contra abusos: 24 horas como máximo.
- Copias de seguridad: 14 días. Una cuenta eliminada desaparece de ellas en un plazo de 14 días.
- Archivos del registro de errores: hasta que se llenan (5 MB más 5 copias anteriores de 5 MB), luego se borran las entradas más antiguas.
- Registros del servidor web y de la aplicación: **TODO**, aún sin decidir.

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
