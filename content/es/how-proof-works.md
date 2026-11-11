# Cómo funciona la verificación

Un proyecto puede conseguir aquí tres sellos (hallmarks). Cada uno es un hecho que comprobamos nosotros mismos, no algo que el autor escribe. Los sellos se calculan de nuevo cada vez que se muestra una página, a partir de las últimas comprobaciones, así que un sello que ya no se cumple desaparece.

## Repo owner {#authored}

**Qué significa:** el repositorio de GitHub enlazado al proyecto pertenece a la cuenta personal de GitHub de quien lo publicó. No demuestra quién escribió el código.

**Cómo se comprueba:** el autor enlaza un repositorio público de GitHub y pulsa «Comprobar repositorio». Consultamos la API pública de GitHub. La marca se consigue cuando el repositorio pertenece a la cuenta personal de GitHub del autor y no es un fork.

Las cuentas y los repositorios se comparan por los identificadores numéricos de GitHub, no por sus nombres: cambiar el nombre de una cuenta o de un repositorio no cambia nada, y un repositorio borrado que alguien vuelve a crear con el mismo nombre es otro repositorio. Solo leemos datos públicos: iniciar sesión nunca nos da acceso a repositorios privados.

**Qué más registramos:** cuándo se creó el repositorio, su primer commit, cuántos commits tiene el autor y cuándo hizo el primero y el último, y en cuántas semanas sus commits cambiaron código (según las estadísticas de GitHub; los bots no cuentan). La página del proyecto muestra estos datos en «Qué se comprobó». La marca espera una breve revisión manual en tres casos: el primer commit es mucho más antiguo que el repositorio, el mismo primer commit pertenece a un repositorio enlazado a otro proyecto de aquí, o GitHub no muestra commits del autor. Las fechas de los commits las escribe quien hace el commit, así que describen la historia, pero no la demuestran.

**Cómo se vuelve a comprobar:** cada semana buscamos de nuevo el repositorio por su identificador.

**Cómo se puede perder:** el repositorio se borra, se hace privado o se transfiere a otra cuenta, o el autor enlaza otro repositorio. Un repositorio solo puede estar enlazado a un proyecto.

## Live {#live}

**Qué significa:** el autor controla el dominio en el que funciona el proyecto.

**Cómo se comprueba:** el autor añade un token que generamos para este proyecto y este dominio, de una de dos maneras:

- un registro DNS TXT en el dominio, o
- una metaetiqueta en la página de inicio, que debe cargar públicamente (sin login), responder 200 OK y pesar menos de 512 KB.

`www.example.com` y `example.com` cuentan como el mismo dominio. Un dominio solo puede estar verificado para un proyecto a la vez. Los tokens son aleatorios y nunca se reutilizan.

**Cómo se vuelve a comprobar:** una vez al día volvemos a comprobar todos los dominios que no se han confirmado en los últimos 30 días. El sello se mantiene solo mientras el dominio se haya confirmado en los últimos 35 días.

**Cómo se puede perder:**

- el token ya no está en el DNS ni en la página de inicio: el sello se retira de inmediato;
- el sitio o el DNS no responde: lo intentamos de nuevo en la siguiente ejecución, pero tras 35 días sin confirmación el sello desaparece;
- el autor cambia la URL pública a otro dominio.

Cada vez que Live se consigue o se retira, el cambio queda anotado en nuestro registro interno.

La dirección principal de un servicio de alojamiento que comparten muchos sitios (como `github.io` o `vercel.app`) no se puede verificar. Tu propia dirección en él (`yourname.github.io`) sí.

## Steady {#steady}

**Qué significa:** el proyecto sigue en funcionamiento, no solo el día del lanzamiento.

**Cómo se comprueba:** mientras un proyecto tiene Live, solicitamos su URL pública más o menos cada 3 horas. Una comprobación es correcta cuando el sitio responde con un estado HTTP inferior a 400 en menos de 5 segundos. El sello se consigue cuando, en los últimos 30 días:

- hubo al menos 40 comprobaciones, y
- al menos el 95 % fueron correctas.

La página del proyecto muestra el porcentaje de disponibilidad y una franja de 30 días. Los resultados se conservan 90 días.

**Cómo se puede perder:** la disponibilidad baja del 95 %, o el proyecto pierde Live. Steady siempre requiere Live.

Una comprobación también falla cuando el sitio solo responde tras redirigir a otro dominio: la respuesta tiene que venir del dominio verificado.

## Qué es declarado por el autor {#self-declared}

Estas partes de un proyecto las escribe el autor y **no** las comprobamos:

- nombre, lema, descripción y capturas de pantalla;
- etiquetas y fecha de lanzamiento;
- «Creado con», las herramientas de IA que el autor dice haber usado. Siempre aparece como «declarado por el autor».

Los sellos solo dicen lo que dicen. Repo owner trata del repositorio, Live del dominio, Steady de la disponibilidad. Ninguno es una reseña del producto.

## Qué no podemos comprobar {#limits}

{{ site_name }} comprueba hechos que puede demostrar: a quién pertenece el repositorio de GitHub enlazado, quién controla el dominio y si el sitio responde. No comprueba ni puede comprobar quién escribió el código. El historial de commits y sus fechas los escribe el propietario del repositorio y se pueden cambiar. Si crees que un proyecto está copiado, denúncialo.
