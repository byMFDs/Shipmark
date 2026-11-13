# Política de privacidad

> **Borrador**, última actualización el 13 de noviembre de 2026. Este texto aún no ha sido revisado por un abogado.
>
> Traducción de cortesía; prevalece la versión en inglés.

Esta página explica qué guarda {{ site_name }} sobre ti, para qué, durante cuánto tiempo y qué puedes hacer al respecto. Describe lo que el sitio hace realmente.

## Quién es responsable {#controller}

{{ site_name }} lo gestiona {{ legal_owner_name }}, que es responsable de tus datos (el «responsable del tratamiento»).
Preguntas o solicitudes: [{{ contact_email }}](mailto:{{ contact_email }}).

## Qué guardamos y por qué {#data}

**Cuando inicias sesión con GitHub.** Recibimos de GitHub el id de tu cuenta, tu login, tu nombre, tu biografía, el enlace a tu avatar y los demás campos públicos de tu perfil de GitHub, además de las direcciones de correo de tu cuenta de GitHub. Solo pedimos a GitHub `read:user` y `user:email`: nunca obtenemos acceso a tus repositorios, ni privados ni públicos, a través de tu cuenta. No conservamos tu token de acceso de GitHub después de iniciar sesión. Necesitamos estos datos para crear tu cuenta y reconocerte la próxima vez (ejecución de nuestro acuerdo contigo). Tu usuario de GitHub se actualiza cada vez que inicias sesión, así tu perfil siempre enlaza a tu cuenta actual de GitHub.

**Tu perfil.** Nombre de usuario, nombre visible, descripción breve, «Acerca de», ubicación, un estado (por ejemplo, «Abierto a trabajo»), hasta 10 habilidades, hasta 6 enlaces, hasta 3 proyectos fijados y tu idioma. Todo salvo el nombre de usuario es opcional. El nombre visible y «Acerca de» empiezan con tu nombre y tu biografía de GitHub; puedes cambiarlos o quitarlos en Ajustes. También guardamos la dirección de tu imagen de GitHub, solo para que «Usar mi imagen de GitHub» pueda copiarla; nunca se muestra. Tu nombre de usuario, nombre visible, descripción breve, «Acerca de», ubicación, estado, habilidades, enlaces, proyectos fijados, usuario de GitHub y el mes en que te uniste son **públicos**.

**Foto de perfil y portada.** Puedes subir una foto y una imagen de portada ancha, o copiar una vez tu imagen de GitHub. Cada imagen se vuelve a codificar (la foto a 512×512, la portada a 1500×500), lo que elimina metadatos ocultos como la ubicación GPS, recibe un nombre de archivo aleatorio y se guarda en nuestro propio servidor: las páginas nunca cargan tu foto desde GitHub. Ambas son **públicas**. Cuando quitas o reemplazas una, o eliminas tu cuenta, el archivo se borra; las copias quedan en las copias de seguridad hasta 14 días. Sin foto, se muestran tus iniciales.

**Tu dirección de correo.** Se guarda con tu cuenta y solo la ve nuestro equipo. Nunca se muestra en el sitio. El sitio no te envía correos (el único que envía es un aviso a nuestro equipo sobre un mensaje de soporte); usaríamos la dirección solo para contactarte sobre tu cuenta, una denuncia o un mensaje de soporte.

**Tus proyectos.** Todo lo que introduces: nombre, lema, descripción, enlaces, etiquetas, las herramientas de IA que dices haber usado (se muestran como declaradas por el autor), capturas de pantalla y entradas del registro de desarrollo. Los proyectos publicados son públicos; los borradores solo los ven tú y nuestro equipo. Las capturas de pantalla se recodifican al subirlas, lo que elimina metadatos ocultos como los datos de la cámara o la ubicación GPS.

**Comprobaciones de la prueba.** Para conceder sellos comprobamos los hechos nosotros mismos (nuestro interés legítimo en mostrar pruebas en las que se pueda confiar):

- *Repo owner:* consultamos la API pública de GitHub sobre el repositorio que enlazas y guardamos su identificador, el identificador de la cuenta propietaria, si es tuyo, su fecha de creación y su campo Website, el primer commit de su historial (identificador y fecha), tu número de commits, las fechas de tu primer y último commit, el número de semanas con commits tuyos y el estado de una revisión manual cuando hace falta. Lo volvemos a comprobar cada semana. La lista de otras personas que contribuyen se lee durante la comprobación y no se guarda. Si usas el archivo de verificación para un repositorio de una organización, también guardamos si se encontró.
- *Domain verified:* consultamos los registros DNS del dominio de tu proyecto o descargamos su página para encontrar tu token de verificación.
- *Steady:* solicitamos la dirección de tu proyecto cada pocas horas y guardamos si respondió y con qué rapidez. Estas comprobaciones se conservan **90 días**.

Los resultados se muestran en la página pública de tu proyecto.

**Seguimientos y me gusta.** Guardamos a quién sigues y qué proyectos te gustan. Los demás solo ven los totales, no las listas.

**Denuncias y moderación.** Si denuncias un proyecto, un perfil o una entrada del registro de desarrollo, guardamos el motivo y los detalles que escribas. Las denuncias las ven los moderadores (personas con la insignia de moderador) y el equipo. Para decidir, también ven el contenido denunciado y el historial de la persona denunciada en {{ site_name }}: cuándo se unió, sanciones anteriores, otras denuncias sobre ella y proyectos retirados. Las páginas de moderación no muestran direcciones de correo. A la persona denunciada nunca se le dice quién la denunció. Cuando los moderadores actúan, guardamos la decisión y su motivo: un proyecto retirado conserva su contenido y el motivo (solo lo ven tú, los moderadores y el equipo), los campos de perfil vaciados (foto y portada, descripción breve y «Acerca de», o enlaces) se borran, y los silencios y bloqueos se guardan con su motivo, inicio y fin. Ves el motivo en un aviso en el sitio, que guardamos hasta que eliminas tu cuenta. Las decisiones sobre ti y estos avisos se incluyen en «Descargar mis datos». Para recurrir una decisión, escribe a [{{ contact_email }}](mailto:{{ contact_email }}).

**Comunidad.** Cuando publicas en la comunidad guardamos tus hilos (sección, título, texto, fechas y si un hilo fue editado, fijado, cerrado o retirado), tus respuestas (texto, el sticker que elegiste, a qué publicación responden) y las imágenes que adjuntas. Las imágenes se vuelven a codificar como las capturas de pantalla: se eliminan metadatos ocultos como la ubicación GPS, los nombres de archivo son aleatorios y en nuestro propio servidor guardamos una copia de hasta 1600 px y una miniatura de 640 px. Las publicaciones, sus imágenes, su número de votos y tu nombre de usuario en ellas son **públicos**. También guardamos tus votos; nadie ve quién votó qué, ni en el sitio ni en el panel de administración. Cuando eliminas una publicación, su texto, su sticker y sus imágenes se eliminan en el acto (el título de un hilo se queda mientras haya respuestas de otras personas debajo y aparece como «[eliminado]»). Cuando los moderadores retiran una publicación, sus imágenes se eliminan en el acto y su texto se conserva con el motivo, visible solo para ti, los moderadores y el personal. Los moderadores ven las publicaciones denunciadas junto con el historial de su autor, como en otras denuncias.

**Avisos de respuestas.** Cuando alguien responde a tu hilo o a tu respuesta, guardamos un aviso para ti (qué respuesta, cuándo y cuándo abriste la lista), además de la hora del aviso sin leer más reciente, para que el menú pueda mostrar una marca. Solo tú los ves. Se eliminan a los **90 días** o con tu cuenta. Nunca los enviamos por correo.

**Evasión de bloqueos.** Cuando se bloquea una cuenta, guardamos un hash unidireccional con sal de su id de usuario de GitHub (nunca el id), con el motivo y la fecha de fin. Solo sirve para reconocer la misma cuenta de GitHub si vuelve a registrarse durante el bloqueo. Se borra cuando el bloqueo termina o se levanta, también si la cuenta bloqueada se eliminó entretanto.

**Aceptación de los Términos.** Guardamos qué versión de los Términos aceptaste y cuándo.

**Registro de auditoría.** Llevamos un registro interno de los cambios de sellos, las acciones de moderación y las eliminaciones de cuentas, para poder revisar las decisiones más adelante. Solo nuestro equipo puede verlo.

**Direcciones IP y registros.** La aplicación no guarda tu dirección IP y sus propios registros no la contienen. De cada petición de página los registros anotan solo el método, la dirección de la página (sin lo que va después de un `?`), el estado de la respuesta, el tamaño y el tiempo empleado, además de los errores. No contienen datos de tu navegador. Las direcciones de página incluyen nombres de usuario (`/u/<username>/`), así que una línea del registro puede mostrar qué perfil se abrió, pero no quién lo abrió.

**Registro de errores.** Cuando algo falla, la aplicación escribe una entrada breve en un archivo de errores de nuestro servidor: la hora, un número de referencia aleatorio (el que aparece en la página de error), el método de la solicitud, la dirección de la página sin lo que va después de `?` y con los nombres de usuario sustituidos por `[user]`, el estado de la respuesta, la parte del código que falló y el mensaje técnico, del que se eliminan direcciones de correo, direcciones IP y todo lo que parezca una contraseña o una clave. Las páginas no encontradas van a un archivo aparte, cada dirección como mucho una vez por minuto. Estos archivos nunca contienen tu dirección IP, datos del navegador, cookies, lo que escribes en los formularios, tu correo ni tu nombre de usuario. Cada archivo está limitado a 5 MB más 5 copias anteriores; al llegar al límite se borra la más antigua.

> **TODO antes del lanzamiento:** el servidor web que está delante de la aplicación lleva su propio registro de accesos, que por defecto incluye direcciones IP. Aún no se ha decidido qué anota ni cuánto tiempo lo conserva (ni cuánto se conservan los registros de la aplicación). Hay que completarlo, o desactivar el registro de IP, antes de que esta página sea pública.

**Protección contra abusos.** Para limitar los abusos contamos algunas acciones (por ejemplo, me gusta por hora) en la base de datos del sitio. Cada contador es un número asociado a tu cuenta o a un proyecto, sin dirección IP, y se aplica durante 24 horas como máximo. Después deja de usarse, pero la fila puede permanecer en la base de datos hasta que se limpie.

**Analítica y seguimiento.** No hay: ni analítica, ni publicidad, ni scripts de seguimiento. Las fuentes se sirven desde nuestro propio servidor.

**Copias de seguridad.** Cada día hacemos una copia de la base de datos y de las imágenes subidas (capturas, fotos de perfil y portadas) y guardamos cada copia 14 días. Si eliminas tu cuenta, tus datos siguen en esas copias hasta que se reemplaza la última que los contiene, como máximo 14 días después.

## Mensajes al soporte {#support}

Cuando nos escribes con el [formulario de soporte](/support/), guardamos el tema, el asunto, tu mensaje, la dirección de correo que indicas (o la de tu cuenta), la cuenta con la que habías iniciado sesión, el número de referencia de una página de error si vienes de una y hasta 3 archivos adjuntos. Las imágenes se vuelven a codificar como las demás (se eliminan metadatos ocultos como la ubicación GPS); los archivos de texto se guardan como texto. Los adjuntos se guardan en una carpeta privada de nuestro servidor que no tiene dirección pública: solo el personal con acceso al buzón de soporte puede descargarlos. Usamos tu correo solo para responderte.

No guardamos tu dirección IP ni datos del navegador con el mensaje. Para frenar el spam, una huella unidireccional con sal de tu dirección IP se guarda en la caché del servidor como máximo 24 horas, nunca en la base de datos ni en los registros.

Cuando llega un mensaje, nuestro servidor envía al buzón del equipo un breve aviso en texto plano con tu mensaje y tu correo, a través de nuestro proveedor de correo (ver «Quién más recibe datos»). El personal puede añadir notas internas y poner un estado (nuevo, leído, respondido, cerrado). Leemos cada mensaje, pero no podemos prometer responder a todos. Los mensajes cerrados se eliminan 12 meses después de enviarse; los demás se quedan hasta que se cierran. «Descargar mis datos» incluye los mensajes que enviaste con sesión iniciada, y eliminar tu cuenta los elimina, también los enviados sin sesión desde el correo de tu cuenta.

## Cuánto tiempo lo conservamos {#retention}

- Tu cuenta, perfil, proyectos, seguimientos y me gusta: hasta que los elimines a ellos o a tu cuenta.
- Mensajes de soporte y adjuntos: los cerrados, 12 meses después de enviarse; los demás, hasta que se cierran; con tu cuenta.
- Hilos, respuestas e imágenes de la comunidad: hasta que los elimines o elimines tu cuenta (lo que se queda se explica arriba, en «Comunidad»). Votos: hasta que los retires o elimines tu cuenta.
- Avisos de respuestas: 90 días.
- Foto de perfil y portada: hasta que las quites o reemplaces, o elimines tu cuenta.
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
- **Nuestro proveedor de correo** (por ejemplo Google, si el buzón del equipo es una cuenta de Gmail) entrega al buzón del equipo el aviso de cada mensaje de soporte, con su texto y tu correo.
- **Los servidores de tu proyecto.** Para las comprobaciones de Domain verified y Steady, nuestro servidor contacta con el DNS de tu dominio y con la dirección de tu proyecto. Ven nuestro servidor, no a ti.
- **Nuestro proveedor de alojamiento**, que ejecuta el servidor y la base de datos por nosotros.

No vendemos tus datos ni los compartimos con fines publicitarios.

## Tus derechos {#rights}

- **Ver y descargar tus datos:** en Ajustes → «Descargar mis datos» obtienes un archivo JSON con tu perfil (con tus enlaces, habilidades, proyectos fijados y las direcciones de tu foto y tu portada), tus datos de GitHub, proyectos, registro de desarrollo, me gusta, seguimientos, las denuncias que hiciste y las decisiones de moderación y avisos sobre ti.
- **Corregirlos:** edita tu perfil en Ajustes y tus proyectos en sus páginas.
- **Eliminarlos:** Ajustes → «Eliminar cuenta». Esto elimina de inmediato tu perfil, tu foto y tu portada y todos tus proyectos, me gusta y seguimientos, y no se puede deshacer. Tu nombre de usuario queda libre.
- **Comunidad:** «Descargar mis datos» también incluye tus hilos, respuestas, las direcciones de tus imágenes, tus votos y tus avisos de respuestas. Eliminar tu cuenta elimina tus imágenes de la comunidad, tus votos, tus avisos y tus hilos sin respuestas de otras personas; el resto de tus publicaciones se queda sin tu nombre, tu foto ni tu enlace. Las imágenes de la comunidad están en las copias de seguridad diarias, como las demás subidas (14 días).
- **Oponerte o reclamar:** escribe a [{{ contact_email }}](mailto:{{ contact_email }}). Si vives en la UE, el Reino Unido o Ucrania, también puedes reclamar ante tu autoridad de protección de datos.

## Cookies {#cookies}

Usamos solo las cookies que el sitio necesita para funcionar. Consulta la [política de cookies](/legal/cookies/).

## Cambios {#changes}

Si esta política cambia, actualizamos la fecha de arriba. Si el cambio es importante, te pediremos que aceptes los Términos actualizados en tu próxima visita.
