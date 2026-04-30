# Política de Colaboradores de DentalPin

> Versión 1.0 — abril 2026
> Autor: Dentared Odontology Services S.L. (en adelante, **Dentaltix**, mantenedor del proyecto)

DentalPin aspira a convertirse en el estándar abierto para la gestión de clínicas dentales: el sistema operativo que conecta a clínicas, profesionales, proveedores, software y servicios del ecosistema. Para que ese estándar sea creíble y duradero, su núcleo debe ser **abierto, neutral e independiente**.

Si estás leyendo esto, probablemente quieras construir algo encima de DentalPin. **Bienvenido.** Nos encanta que estés aquí. Este documento existe para que entiendas, sin letra pequeña, qué te ofrecemos, qué te pedimos y por qué algunas cosas no se mueven. Pensamos que la honestidad desde el primer minuto es lo que hace que las colaboraciones aguanten años.

Si decides sumarte al ecosistema, das por aceptados los principios que vienen a continuación.

---

## 1. Visión

- **Estándar abierto.** DentalPin existe para que cualquier clínica, en cualquier país, pueda gestionar su operativa con un software libre, auditado y portable.
- **Ecosistema multilateral.** El valor del proyecto crece cuando otros construyen sobre él: módulos clínicos, integraciones con laboratorios, ortodoncia digital, radiología, facturación, IA, automatización, marketplaces, etc.
- **SaaS oficial gratuito sobre el core.** Dentaltix operará una versión SaaS cuyo uso del core es gratis para las clínicas. Las clínicas pagan únicamente por los módulos e integraciones de pago que decidan activar.
- **Sostenibilidad sin captura.** Los colaboradores monetizan sus módulos. Dentaltix monetiza la operación del SaaS y una comisión sobre el marketplace. El core nunca se monetiza por sí mismo.

---

## 2. Principios innegociables

Empezamos por aquí porque son los pilares que nos permiten ofrecer todo lo demás. No se negocian con nadie —y precisamente porque no se negocian con nadie, también te protegen a ti: nadie podrá usar el proyecto en tu contra mañana.

1. **Único mantenedor del core.** Dentared Odontology Services S.L. es la única entidad que mantiene, dirige y publica el core de DentalPin. No hay co-propiedad, ni gobernanza compartida, ni asientos reservados para colaboradores en las decisiones técnicas del core.
2. **Licencia y conversión.** El core se distribuye bajo BSL 1.1, con conversión automática a Apache 2.0 a los 4 años de cada release. La licencia no se modificará a la baja en perjuicio de la comunidad.
3. **Marca protegida.** "DentalPin" y los logotipos asociados son marca de Dentared Odontology Services S.L. Los colaboradores pueden indicar compatibilidad ("Compatible con DentalPin", "Módulo para DentalPin") según las guías de marca, pero no usar la marca como suya ni en denominación social, dominio o producto.
4. **CLA obligatorio.** Toda contribución al repositorio del core requiere firmar un Contributor License Agreement que otorga a Dentaltix los derechos necesarios para mantener, relicenciar (dentro de licencias OSI-aprobadas) y defender el proyecto. El CLA no transfiere la autoría: el contribuidor sigue siendo titular de su trabajo.
5. **Frontera técnica estricta.** El core y los módulos están separados por contratos explícitos: manifiestos de módulo, dependencias declaradas, bus de eventos y APIs públicas versionadas. Ningún módulo puede modificar el core para su propio beneficio. Las extensiones pasan por las APIs públicas o por una propuesta abierta (RFC).
6. **Neutralidad competitiva.** El core no favorece a ningún colaborador. Si Dentaltix construye un módulo en una categoría donde ya existen colaboradores, lo hace usando exactamente las mismas APIs y reglas del marketplace que cualquier tercero, y se declara como tal.
7. **Portabilidad de los datos clínicos.** Las clínicas son siempre propietarias de sus datos. Ningún módulo, integración o configuración de la SaaS oficial puede impedir la exportación íntegra de los datos de una clínica.

---

## 3. Modelo de ecosistema

DentalPin es un **open core con marketplace**. Tres capas:

| Capa | Quién la mantiene | Cómo se distribuye |
|------|-------------------|--------------------|
| **Core** | Dentaltix en exclusiva | Open source (BSL 1.1 → Apache 2.0) |
| **Módulos oficiales** | Dentaltix, abiertos | Open source, parte del repositorio principal |
| **Módulos de terceros** | Cualquier colaborador | Marketplace de DentalPin; pueden ser open source o propietarios |

El SaaS oficial operado por Dentaltix es la vía de distribución por defecto, pero el proyecto sigue siendo auto-hospedable. Cualquier clínica o partner técnico puede desplegar DentalPin por su cuenta.

---

## 4. Qué ofrecemos a los colaboradores

A cambio de construir sobre DentalPin con calidad y respeto a estos principios, los colaboradores reciben valor concreto:

- **Distribución.** Acceso al marketplace integrado en la SaaS oficial, con presencia ante todas las clínicas activas.
- **APIs estables y documentadas.** Compromiso de versionado semántico para las APIs públicas, ventana mínima de deprecación de 12 meses y catálogo de eventos publicados.
- **Revenue share transparente.** Dentaltix actúa como procesador de pagos del marketplace. Comisión estándar publicada y aplicada por igual a todos los colaboradores.
- **Co-marketing.** Casos de éxito, listados destacados, contenido conjunto, presencia en eventos del ecosistema.
- **Voz técnica.** Cualquier colaborador puede proponer cambios a las APIs o nuevos puntos de extensión mediante RFCs públicos. Dentaltix los discute en abierto. La decisión final es de Dentaltix; el debate es de la comunidad.
- **Early access al roadmap.** Acceso anticipado a APIs preliminares y a información del roadmap bajo NDA cuando aplique.

Los colaboradores que entren en la fase inicial del proyecto reciben además beneficios reforzados —ver §5.

---

## 5. Programa Founding Partners

Apostar por un ecosistema joven, con poca adopción, no es gratis. Lo sabemos. Los **Founding Partners** son los colaboradores que se suben cuando todavía hay más visión que clínicas, y queremos que esa apuesta os la devolvamos con creces —no solo en los primeros meses, sino mientras el módulo siga vivo.

### Beneficios

- **Comisión 0% de marketplace durante 18 meses** desde la activación de su módulo, sobre todas las ventas a través de la SaaS oficial.
- **50% de descuento sobre la comisión estándar a partir del mes 19**, de forma indefinida mientras el módulo siga activo y el colaborador siga cumpliendo los compromisos del programa. Este descuento perpetuo es la forma en la que reconocemos, también con el tiempo, a quienes confiaron primero.
- **Co-diseño de APIs en su categoría.** Asiento técnico en el diseño de las APIs y eventos relevantes para su área (no es voto vinculante, pero sí input prioritario y respondido por escrito).
- **Acceso temprano** a roadmap, APIs preliminares y entornos de prueba, con tiempo razonable para adaptarse antes que la comunidad general.
- **Placement destacado** en el marketplace y materiales oficiales durante los primeros 18 meses.
- **Co-marketing prioritario.** Caso de éxito conjunto, contenido coordinado, presencia en eventos donde Dentaltix participe.
- **Línea directa** con el equipo técnico de Dentaltix (canal dedicado, SLA de respuesta en días laborables).
- **Acceso a métricas agregadas y anonimizadas del marketplace** que ayuden a su decisión de negocio (sin datos identificables de clínicas o de otros colaboradores).
- **Reconocimiento perpetuo.** El badge "Founding Partner desde [año]" y la mención en la página oficial de partners se mantienen mientras el módulo siga activo y cumpla los compromisos, incluso cuando otros colaboradores se sumen al ecosistema.
- **Compromisos reforzados de Dentaltix** (ver §6) aplicados con mayor rigor: aviso anticipado de cambios estructurales, tratamiento preferente en periodos de coexistencia, prioridad en revisiones técnicas.

### Qué te pedimos a cambio

- Un módulo de calidad, en producción, con soporte real detrás.
- Feedback honesto —del bueno y del incómodo— sobre APIs, documentación, onboarding y puntos de fricción.
- Que estés dispuesto a hacer un caso de éxito conjunto cuando llegue el momento.
- Buena fe: no usar el acceso temprano para erosionar el ecosistema ni para construir un fork competitivo.

### Lo que el programa **no** es

Para que no haya malentendidos: ser Founding Partner no implica co-propiedad, exclusividad, voto vinculante sobre el core ni descuento perpetuo. Es un acuerdo de "primera ola", generoso y con fecha, pensado para que arrancar contigo merezca la pena —no es una concesión sobre el proyecto.

El programa contempla **un máximo de 5 Founding Partners** en total. No hay prisa por llenarlas: las plazas son pocas a propósito, porque queremos elegir bien con quién arrancamos esto. Cada plaza se reserva para una categoría distinta del ecosistema (agenda automatizada, comunicación con paciente, IA clínica, integraciones de laboratorio, etc.); no se concede más de una plaza por categoría.

---

## 6. Compromisos de Dentaltix con sus colaboradores

Esto no va en una sola dirección. Si te pedimos calidad, soporte y buena fe, lo justo es que tú sepas exactamente qué puedes esperar de nosotros:

- **APIs estables.** Versionado semántico, ventana mínima de deprecación de 12 meses, changelog público.
- **Comunicación temprana.** Cambios estructurales en core, modelo de marketplace o políticas de la SaaS se comunican con antelación razonable a colaboradores activos. Para Founding Partners y Strategic, antes que al público general.
- **No canibalización oportunista.** Si Dentaltix decide construir un módulo oficial en una categoría donde ya existe un módulo Strategic o Founding Partner activo y conforme con esta política, lo notificará con un mínimo de **6 meses de antelación** y mantendrá un periodo razonable de coexistencia. El módulo de Dentaltix usará exactamente las mismas APIs que cualquier tercero, sin atajos privilegiados.
- **Pagos puntuales.** Liquidaciones del marketplace en los plazos publicados, con desglose claro y trazabilidad.
- **Defensa pública de la neutralidad.** Dentaltix asume la responsabilidad de mantener visible la neutralidad del ecosistema y de actuar cuando un actor —incluida ella misma— intente quebrarla.
- **Reconocimiento de la apuesta inicial.** Quienes apuesten por el proyecto en su fase temprana mantendrán el reconocimiento de Founding Partner mientras cumplan los compromisos básicos, también cuando lleguen jugadores más grandes.
- **Sin sorpresas legales.** Esta política no se modifica retroactivamente en perjuicio de acuerdos firmados con Founding Partners durante la vigencia de su acuerdo (ver §12).

Estos compromisos no se quedan en un PDF: aparecen también, por escrito, en el acuerdo que firmamos contigo.

---

## 7. Lo que no podemos ofrecerte (y por qué te conviene)

Con el mismo cariño con el que te decimos sí a muchas cosas, hay otras a las que vamos a responder siempre con un "no". No es desconfianza ni rigidez: es lo que mantiene el ecosistema neutral y, sobre todo, lo que protege tu inversión en él frente a actores que vengan después.

- **Co-propiedad o co-gobernanza del core.** Ningún colaborador, por antiguo o estratégico que sea, obtiene voto vinculante sobre el core, derecho de veto, ni participación en su roadmap más allá de la voz pública en RFCs.
- **Exclusividad por categoría.** No se concede exclusividad funcional ni territorial. Si entras como módulo de automatización de agenda, otros pueden entrar también en automatización de agenda. Esa misma regla evita que otro te bloquee mañana a ti.
- **Cambios al core a medida.** El core no se modifica para favorecer un caso de negocio particular de un colaborador. Si una API no existe, se propone vía RFC y se evalúa por su valor general, no por quién la pide.
- **Forks favoritos.** No se reconoce, recomienda ni apoya ningún fork del core, salvo despliegues legítimos auto-hospedados por clínicas o partners técnicos.
- **Equity, IP o branding compartido.** Una colaboración técnica o comercial no genera derechos sobre Dentared Odontology Services S.L., sobre el código del core, ni sobre la marca DentalPin.
- **Acceso privilegiado a datos de clínicas.** Los datos clínicos son de las clínicas. Ningún colaborador accede a datos agregados o desagregados sin consentimiento explícito de la clínica titular.

> **Por qué estos límites también te protegen a ti.** Si hoy vendiéramos exclusividad o co-gobernanza al primero que llega, mañana te tocaría a ti negociar contra alguien con más músculo. La regla simétrica —la misma para todos— es la única que aguanta a largo plazo, y por eso es también la mejor garantía que podemos darte.

---

## 8. Niveles de colaboración

| Nivel | Para quién | Requisitos | Beneficios |
|-------|-----------|------------|------------|
| **Community** | Cualquier desarrollador u organización | Módulo publicable, cumple guía técnica y legal | Listado en marketplace, comisión estándar |
| **Verified** | Colaboradores con módulo en producción y soporte demostrable | Revisión técnica, SLA mínimo, política de soporte pública | Badge "Verified", placement mejorado, co-marketing puntual |
| **Strategic** | Colaboradores en categorías clave o con tracción significativa | Acuerdo escrito, compromisos de calidad y soporte reforzados | Trato prioritario en RFCs, co-marketing, aviso anticipado de cambios estructurales |
| **Founding Partner** | Primeros colaboradores en la fase inicial del proyecto | Acuerdo escrito; ver §5 | Beneficios completos del programa Founding Partners |

El paso entre niveles es discrecional de Dentaltix y se basa en criterios objetivos publicados (calidad, soporte, adopción, alineamiento con esta política). El nivel Founding Partner es un programa cerrado en el tiempo; los demás permanecen abiertos.

---

## 9. Compromisos del colaborador

Por su parte, quien publique un módulo o integración en el ecosistema DentalPin asume estos compromisos —que son los mismos que tú esperarías de cualquier proveedor que entra en una clínica:

1. **Calidad técnica.** Cumplir la guía de creación de módulos (`docs/technical/creating-modules.md`), pasar revisión y tests.
2. **Soporte.** Publicar canal y SLA. Mantener el módulo compatible con las versiones de DentalPin soportadas.
3. **Cumplimiento legal.** Respeto a RGPD y normativa aplicable de datos clínicos en cada jurisdicción donde opere. Encargado de tratamiento debidamente formalizado cuando proceda.
4. **Transparencia con la clínica.** Pricing claro, condiciones de cancelación claras, exportación de datos del módulo siempre disponible para la clínica.
5. **No fork hostil.** No promover, distribuir ni recomendar forks competitivos del core mientras se forme parte del ecosistema oficial.
6. **Uso correcto de la marca.** Seguir las guías de marca y co-branding publicadas por Dentaltix.
7. **Conflictos de interés.** Declarar cualquier interés relevante (participación cruzada, acuerdos de exclusividad con terceros, etc.) que pueda afectar a la neutralidad del ecosistema.

Si algo se rompe, primero hablamos. Solo si el problema no se puede arreglar —o no se quiere arreglar— llegaríamos a suspender un módulo del marketplace o a retirar a un colaborador del programa. Siempre con plazo de remediación cuando el problema sea subsanable, y siempre por escrito.

---

## 10. Económico (resumen de alto nivel)

- **Core SaaS gratuito** para clínicas. Coste cubierto por el margen del marketplace y por servicios premium operados por Dentaltix (hosting dedicado, soporte, cumplimiento avanzado, etc.).
- **Módulos de terceros**: precio fijado por el colaborador. Dentaltix actúa como procesador de pagos y aplica una comisión estándar, idéntica para todos los colaboradores del mismo nivel. Mientras no exista un portal público de partners, las cifras concretas se acuerdan por escrito en cada contrato de marketplace; cuando exista el portal, se publicarán en abierto.
- **Para qué sirve esa comisión.** No es margen oportunista: financia el desarrollo y mantenimiento continuo del core, la infraestructura del SaaS oficial gratuito para clínicas, el procesamiento de pagos del marketplace y el soporte de primera línea. Sin esa comisión, ni el core abierto ni la SaaS gratuita serían sostenibles a largo plazo.
- **Founding Partners**: comisión 0% durante los **18 primeros meses** desde la activación de su módulo en el marketplace, y **50% de descuento sobre la comisión estándar a partir del mes 19**, de forma indefinida, mientras el módulo siga activo y el colaborador siga cumpliendo los compromisos del programa.
- **Liquidaciones**: ciclo y condiciones publicados en el acuerdo de marketplace.

Las cifras concretas pueden actualizarse con preaviso razonable, y cualquier cambio se aplica de forma uniforme a todos los colaboradores del mismo nivel. Hoy viven en los acuerdos individuales; cuando haya portal público de partners, se publicarán abiertamente allí.

---

## 11. Proceso de incorporación

1. **Contacto inicial** escribiendo a **ramon.martinez@dentaltix.com**. En esta fase inicial del proyecto, no hay todavía formulario ni portal: todas las conversaciones de partners las llevo personalmente yo, Ramón, fundador de Dentaltix.
2. **Conversación de encaje**: caso de uso, categoría, modelo de negocio, alineamiento con esta política.
3. **Acuerdo escrito**: contrato de marketplace y, si aplica, addendum de Founding Partner o Strategic.
4. **Desarrollo** del módulo siguiendo la guía técnica.
5. **Revisión técnica y legal** por parte de Dentaltix.
6. **Publicación** en el marketplace.
7. **Operación continua**: métricas, soporte, renovación.

Habrá casos en los que no encajemos, y cuando sea así te lo diremos en abierto y con motivos: cuando una incorporación entre en conflicto con esta política, con la neutralidad del ecosistema o con los intereses de las clínicas usuarias.

---

## 12. Cambios a esta política

Esta política irá evolucionando con el proyecto —sería raro que no lo hiciera. Cuando la cambiemos:

- Se publican con número de versión y changelog.
- Se notifican a colaboradores activos con un preaviso razonable.
- **No se aplican retroactivamente en perjuicio de acuerdos firmados con Founding Partners o Strategic durante la vigencia de su acuerdo.**

La política vigente siempre es la publicada en este archivo del repositorio oficial.

---

## 13. Contacto

DentalPin está en una fase muy temprana, así que de momento el canal es directo y personal: **ramon.martinez@dentaltix.com**. Soy Ramón, fundador de Dentaltix, y llevo personalmente cada conversación con colaboradores. Cuando el equipo y la adopción crezcan, abriremos canales dedicados (`partners@`, `brand@`, portal de partners) y lo anunciaremos aquí.

- ¿Quieres explorar una colaboración? Escríbeme y nos sentamos lo antes posible a ver si tiene sentido.
- ¿Asuntos de marca o uso de logotipo? Mismo email, indícalo en el asunto.
- ¿Algo de esta política no te queda claro o te chirría? Puedes abrir un issue público en el repositorio etiquetado `governance` —preferimos discutir estas cosas en abierto— o escribirme directamente.

---

*DentalPin pertenece a las clínicas que lo usan, a los desarrolladores que contribuyen y al ecosistema dental que lo adopta. Dentaltix es el guardián que se asegura de que ese reparto siga siendo justo —y eso incluye proteger la apuesta de quien colabora desde el principio.*
