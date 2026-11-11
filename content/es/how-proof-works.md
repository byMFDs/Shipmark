# Cómo funciona la verificación

Un proyecto puede conseguir aquí tres sellos (hallmarks). Cada uno es un hecho que comprobamos nosotros mismos, no algo que el autor escribe. Los sellos se calculan de nuevo cada vez que se muestra una página, a partir de las últimas comprobaciones, así que un sello que ya no se cumple desaparece.

## Repo owner {#authored}

**Qué significa:** la cuenta de GitHub de la persona que publicó el proyecto es propietaria del repositorio vinculado, o tiene al menos 10 commits en él. No prueba quién escribió el código.

**Cómo se comprueba:** el autor vincula un repositorio público de GitHub y pulsa «Comprobar repositorio». Consultamos la API pública de GitHub. El sello se consigue cuando se cumple una de estas dos condiciones:

- el repositorio pertenece a la cuenta personal de GitHub del autor y no es un fork, o
- GitHub cuenta al menos 10 commits de la cuenta del autor en la lista de colaboradores del repositorio.

Las cuentas se comparan por el id numérico de GitHub, así que cambiar el nombre de la cuenta no importa. Solo leemos datos públicos: iniciar sesión nunca nos da acceso a repositorios privados.

**Cómo se puede perder:** una comprobación posterior encuentra el repositorio borrado, privado, movido o que ya no es de esa cuenta y no tiene suficientes commits suyos, o el autor vincula otro repositorio al proyecto. Un repositorio solo puede estar vinculado a un proyecto.

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

## Steady {#steady}

**Qué significa:** el proyecto sigue en funcionamiento, no solo el día del lanzamiento.

**Cómo se comprueba:** mientras un proyecto tiene Live, solicitamos su URL pública más o menos cada 3 horas. Una comprobación es correcta cuando el sitio responde con un estado HTTP inferior a 400 en menos de 5 segundos. El sello se consigue cuando, en los últimos 30 días:

- hubo al menos 40 comprobaciones, y
- al menos el 95 % fueron correctas.

La página del proyecto muestra el porcentaje de disponibilidad y una franja de 30 días. Los resultados se conservan 90 días.

**Cómo se puede perder:** la disponibilidad baja del 95 %, o el proyecto pierde Live. Steady siempre requiere Live.

## Qué es declarado por el autor {#self-declared}

Estas partes de un proyecto las escribe el autor y **no** las comprobamos:

- nombre, lema, descripción y capturas de pantalla;
- etiquetas y fecha de lanzamiento;
- «Creado con», las herramientas de IA que el autor dice haber usado. Siempre aparece como «declarado por el autor».

Los sellos solo dicen lo que dicen. Repo owner trata del repositorio, Live del dominio, Steady de la disponibilidad. Ninguno es una reseña del producto.
