# Sobre {{ site_name }}

{{ site_name }} es un lugar público donde quienes construyen con herramientas de IA muestran lo que de verdad lanzaron. En lugar de afirmaciones, cada proyecto lleva sellos de prueba que comprobamos nosotros mismos.

## El problema {#problem}

Decir «lo lancé» no cuesta nada. Una captura, un post de lanzamiento o una línea en el CV pueden describir cualquier cosa, y desde fuera nadie sabe si el producto existe, quién lo controla o si sigue funcionando un mes después.

GitHub muestra código. LinkedIn muestra afirmaciones. {{ site_name }} intenta mostrar resultados: un proyecto, los hechos que pudimos comprobar sobre él y lo que hizo después quien lo construyó. Lo principal aquí es el proyecto; un perfil es solo la colección de proyectos de alguien.

## Cómo funciona la verificación {#proof}

Un proyecto puede ganar tres sellos. Cada uno es un hecho que comprueba nuestro servidor, y cada uno desaparece cuando el hecho deja de ser cierto.

- **Repo owner.** El proyecto enlaza un repositorio público de GitHub. Preguntamos a la API pública de GitHub si pertenece a la cuenta personal de GitHub del autor y no es un fork; en repositorios de organizaciones y equipos, el autor añade en su lugar un archivo con el token de este proyecto. Lo volvemos a comprobar cada semana.
- **Domain verified.** El autor demuestra que controla el dominio del proyecto con un token que generamos: un registro TXT en el DNS o una metaetiqueta en la página principal. Lo volvemos a comprobar con regularidad, y el sello solo se mantiene mientras el dominio se haya confirmado en los últimos 35 días.
- **Steady.** Cuando un proyecto tiene Domain verified, abrimos su dirección más o menos cada 3 horas. Steady necesita al menos 40 comprobaciones en los últimos 30 días, y al menos el 95 % de ellas debe recibir respuesta sin error en 5 segundos.

Las reglas completas, incluido cómo se puede perder cada sello, están en [Cómo funciona la verificación](/how-proof-works/).

## Lo que no verificamos {#not-verified}

- **Quién escribió el código.** {{ site_name }} comprueba hechos que puede demostrar: a quién pertenece el repositorio de GitHub enlazado, quién controla el dominio y si el sitio responde. No comprueba ni puede comprobar quién escribió el código ni cuánto escribió una herramienta de IA. El historial de commits y sus fechas los escribe el propietario del repositorio y se pueden cambiar. Si crees que un proyecto está copiado, denúncialo.
- **Si el proyecto es bueno.** Los sellos no son reseñas. Un proyecto con Steady puede ser una idea floja, y un gran proyecto puede no tener todavía ningún sello.
- **Lo que escribe el autor.** El nombre, la descripción, las capturas, las etiquetas, la fecha de lanzamiento y las herramientas de IA en «Creado con» los indica el autor. «Creado con» siempre aparece como declarado por el autor.

## Qué obtienes {#builders}

- Un perfil público que reúne tus proyectos. Inicias sesión con GitHub; solo pedimos tu perfil público y tus direcciones de correo, nunca acceso a tus repositorios.
- Una página para cada proyecto con sus sellos, capturas, una franja de disponibilidad de 30 días (cuando tiene Domain verified) y un registro de desarrollo: actualizaciones breves y notas de lanzamiento, en orden.
- Una insignia para el README de GitHub o tu web que muestra los sellos que tiene el proyecto en este momento. El código para pegar está en la página del proyecto.
- Seguir, me gusta, novedades con nuevos lanzamientos y de la gente que sigues, y una página «Explorar» para encontrar proyectos por etiqueta, herramienta o sello.
- Control sobre tus datos: descárgalos todos en un archivo o elimina tu cuenta desde Ajustes. Sin anuncios, sin analítica, sin scripts de seguimiento.

## Quién está detrás {#who}

{{ site_name }} lo construye y lo mantiene una sola persona, Danylo Rudenko, desarrollador independiente. Está hecho como muchos proyectos de aquí: con herramientas de IA, sobre todo Claude Code, y una persona decide qué se construye y si el resultado sirve.

**TODO (Danylo):** confirma este párrafo y, si quieres, añade una frase sobre ti (dónde estás, por qué empezaste).

## Qué viene después {#next}

Previsto después de la primera versión, sin un orden fijo:

- una sola página de novedades con un filtro en lugar de pestañas separadas;
- avatares y más formas de personalizar un perfil;
- logros;
- mejores comprobaciones de repositorios, por ejemplo con forks, y vincular un repositorio con su dominio;
- qué debería significar Domain verified para proyectos que no son webs: herramientas de línea de comandos, bibliotecas, apps móviles.

**TODO (Danylo):** antes de publicar, comprueba que la lista sigue coincidiendo con tus planes.

## Contacto {#contact}

Preguntas, ideas, un error o un proyecto que no debería estar aquí: escribe a [{{ contact_email }}](mailto:{{ contact_email }}). También puedes usar el enlace «Denunciar» en cualquier proyecto o perfil.

**TODO antes del lanzamiento:** esta dirección viene de `CONTACT_EMAIL` en `config/branding.py` y todavía es provisional.
