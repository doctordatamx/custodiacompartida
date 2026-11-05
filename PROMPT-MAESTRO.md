# PROMPT MAESTRO PARA CODEX
## Observatorio de Divorcios y Custodia en México
### Plataforma nacional de análisis estadístico, visualización interactiva y aprendizaje automático

**Rol:** Actúa como un equipo multidisciplinario de ingeniería de datos, ciencia de datos, estadística aplicada, demografía, investigación jurídica, aprendizaje automático, UX/UI y desarrollo web.

Tu objetivo es diseñar, desarrollar, documentar, validar y publicar una plataforma científica de código abierto denominada provisionalmente:

**Observatorio de Divorcios y Custodia en México**

Lema: *Datos, familias y justicia.*

El proyecto tendrá su propio repositorio de GitHub, independiente de los observatorios ENARM, Insumos y Epidemiología, aunque podrá mantener estándares tecnológicos y metodológicos similares.

La plataforma deberá ser moderna, interactiva, visualmente elegante, adaptable a dispositivos móviles y orientada tanto a la ciudadanía como a investigadores, profesionales del derecho, instituciones públicas y responsables de políticas públicas.

---

# 1. OBJETIVO GENERAL

Desarrollar un observatorio nacional de divorcios, custodia, patria potestad, pensiones alimenticias y dinámicas familiares en México, utilizando principalmente los microdatos oficiales del INEGI.

La plataforma deberá permitir:

1. Analizar integralmente las variables disponibles en los microdatos.
2. Explorar tendencias históricas, territoriales y sociodemográficas.
3. Estudiar las modalidades registradas de guarda y custodia.
4. Comparar resultados estadísticos entre hombres y mujeres sin presuponer discriminación, ventajas o desventajas.
5. Analizar las características de los divorcios que involucran hijos menores de edad.
6. Desarrollar modelos estadísticos multivariables y algoritmos de aprendizaje automático.
7. Construir un perfilador interactivo de probabilidades estadísticas de custodia.
8. Comparar escenarios hipotéticos.
9. Incorporar información sobre legislación y justicia familiar en las 32 entidades federativas.
10. Generar investigaciones, visualizaciones, tablas e informes reproducibles.

**Principio rector:** describir lo que muestran los datos, identificar asociaciones y cuantificar incertidumbre, sin convertir las correlaciones en afirmaciones causales ni atribuir automáticamente diferencias a discriminación.

---

# 2. FUENTES DE DATOS

## 2.1 Fuente principal: INEGI

Localizar y utilizar la Estadística de Divorcios del INEGI, priorizando sus microdatos, diccionarios de datos, catálogos, metadatos, documentación técnica y tabulados oficiales.

Portal:

https://www.inegi.org.mx/programas/ed/#datos_abiertos

Comenzar con el año 2024 como referencia para estudiar la estructura de los microdatos. Incorporar 2025 y otros años cuando los archivos oficiales estén disponibles y su compatibilidad haya sido verificada.

Extender posteriormente el análisis histórico hasta el año más antiguo con microdatos utilizables y comparables.

No asumir que todos los años contienen las mismas variables, categorías o unidades de observación.

## 2.2 Auditoría del diccionario de variables

Antes de desarrollar los análisis:

- Descargar el diccionario oficial.
- Identificar todas las variables disponibles.
- Registrar nombres, etiquetas, tipos, códigos y valores especiales.
- Identificar las variables correspondientes al Divorciante 1 y Divorciante 2.
- Verificar cómo se codifican sexo, edad, escolaridad, ocupación, condición laboral, residencia y demás características.
- Verificar la codificación de custodia, patria potestad, hijos y pensiones alimenticias.
- Identificar valores faltantes, no especificados y no aplicables.
- Determinar qué variables permiten comparaciones históricas.
- Documentar diferencias entre divorcios judiciales y administrativos.

No asumir que Divorciante 1 corresponde a hombre ni que Divorciante 2 corresponde a mujer.

No asumir que la categoría «ambos» significa automáticamente una modalidad jurídica homogénea de custodia compartida. Verificar su definición oficial y documentar su interpretación operativa.

## 2.3 Fuentes complementarias

Explorar la disponibilidad y pertinencia de:

- Censo Nacional de Impartición de Justicia Estatal del INEGI.
- Estadísticas de los poderes judiciales estatales.
- Información estadística pública sobre procedimientos familiares.
- Legislación civil y familiar estatal.
- Código Nacional de Procedimientos Civiles y Familiares y su implementación.
- Datos públicos de transparencia sobre guarda y custodia.
- Información oficial sobre población, matrimonios y estructura familiar.

No unir registros individuales de fuentes diferentes sin identificadores legítimos y compatibles.

Las fuentes complementarias deberán integrarse preferentemente mediante indicadores agregados, dimensiones territoriales y periodos de referencia.

---

# 3. ARQUITECTURA DE DATOS

Implementar un flujo reproducible:

**Fuente oficial → Descarga → Validación → Estandarización → Análisis → Modelos → Visualización → Publicación.**

Utilizar una arquitectura de datos por capas:

- `raw/`: archivos originales inalterados.
- `staging/`: datos extraídos y normalizados.
- `curated/`: conjuntos homologados y validados.
- `analytics/`: indicadores, tablas y agregaciones.
- `models/`: modelos entrenados y metadatos.
- `public/`: archivos optimizados para el sitio web.

Tecnologías sugeridas:

- Python y Polars para procesamiento.
- DuckDB para consultas analíticas.
- Parquet para almacenamiento columnar.
- R para análisis estadístico complementario.
- Quarto para informes científicos.
- GitHub Actions para automatización.

Los archivos originales grandes no deberán incorporarse indiscriminadamente al repositorio.

Cada descarga deberá registrar:

- URL oficial.
- Fecha de descarga.
- Año de referencia.
- Tamaño del archivo.
- Hash SHA-256.
- Número de registros.
- Variables detectadas.
- Estado de validación.

Crear un manifiesto de procedencia y versiones.

---

# 4. AUDITORÍA AUTOMÁTICA DE INTEGRIDAD

Este componente es obligatorio y debe implementarse antes de publicar indicadores.

Crear un sistema que compruebe:

1. Que los archivos realmente se descargaron.
2. Que se descomprimieron correctamente.
3. Que el número de registros es consistente con la fuente.
4. Que las variables corresponden al diccionario.
5. Que no existen duplicaciones inesperadas.
6. Que las claves geográficas son válidas.
7. Que los valores categóricos pertenecen a sus catálogos.
8. Que los indicadores coinciden con tabulados oficiales cuando sean comparables.
9. Que las transformaciones son reproducibles.
10. Que las gráficas utilizan datos reales y completos.

Generar un reporte de calidad por año y entidad.

**Prohibido sustituir silenciosamente datos faltantes por ceros o utilizar datos sintéticos como si fueran oficiales.**

Si una descarga falla, conservar el último conjunto validado, mostrar su fecha y registrar el error.

---

# 5. MÓDULOS DE LA PLATAFORMA

## Módulo A. Panorama nacional

Crear un dashboard interactivo con:

- Número anual de divorcios.
- Tasas y denominadores documentados.
- Divorcios judiciales y administrativos.
- Evolución histórica.
- Distribución por entidad y municipio.
- Edad de las personas divorciantes.
- Duración del matrimonio.
- Escolaridad y características sociodemográficas.
- Presencia y número de hijos menores.
- Indicadores de custodia y patria potestad.

Incorporar mapas, gráficas de tendencias, distribuciones y tablas.

Todos los indicadores deberán mostrar periodo, fuente y definición.

## Módulo B. Explorador avanzado de variables

Desarrollar una interfaz que permita al usuario seleccionar libremente:

- Año o periodo.
- Estado y municipio.
- Tipo de divorcio.
- Sexo de los divorciantes.
- Edad y grupos de edad.
- Escolaridad.
- Condición económica o laboral, según disponibilidad real.
- Número de hijos.
- Duración del matrimonio.
- Modalidad de custodia.
- Patria potestad.
- Pensión alimenticia.
- Residencia habitual de ambos divorciantes.

Los filtros deberán actualizar las visualizaciones de forma coordinada.

Permitir análisis de dos o más variables, tablas cruzadas, porcentajes, distribuciones, diferencias absolutas e intervalos de confianza cuando correspondan.

Crear un constructor visual de consultas para usuarios sin conocimientos de programación.

## Módulo C. Hijos y divorcio

Analizar específicamente:

- Divorcios con y sin hijos menores.
- Número de hijos involucrados.
- Modalidades registradas de custodia.
- Diferencias territoriales.
- Evolución histórica.
- Relaciones con edad, duración matrimonial y características sociodemográficas.
- Patria potestad.
- Pensiones alimenticias.

Distinguir rigurosamente el número de divorcios del número de menores involucrados.

No extrapolar decisiones registradas a todos los niños afectados por separaciones familiares.

## Módulo D. Custodia compartida

Construir un módulo especializado con:

- Frecuencia registrada de custodia atribuida a ambas personas.
- Custodia exclusiva materna.
- Custodia exclusiva paterna.
- Otras categorías oficiales.
- Evolución histórica.
- Diferencias entre entidades.
- Diferencias por características sociodemográficas.
- Comparaciones entre hombres y mujeres.
- Análisis por municipio cuando los datos sean suficientes.

Crear indicadores con denominadores explícitos.

Separar los casos sin información válida y los casos no aplicables.

No interpretar las diferencias territoriales como evidencia directa de mejor o peor funcionamiento judicial.

## Módulo E. Análisis por sexo

Implementar análisis estratificados por sexo con enfoque descriptivo y estadístico.

Calcular, cuando sea pertinente:

- Frecuencias y proporciones.
- Diferencias absolutas.
- Razones de prevalencia o proporciones.
- Odds ratios.
- Intervalos de confianza.
- Modelos ajustados.
- Tendencias temporales.
- Interacciones estadísticas.

Verificar la correspondencia entre los códigos de Divorciante 1/2 y el sexo registrado antes de clasificar la custodia como materna o paterna.

Documentar explícitamente las observaciones que no puedan clasificarse de forma inequívoca.

Evitar expresiones como «sesgo judicial demostrado» o «discriminación comprobada» a partir de simples diferencias observadas.

---

# 6. LABORATORIO DE APRENDIZAJE AUTOMÁTICO

Implementar un laboratorio reproducible con dos enfoques principales.

## 6.1 Regresión logística multinomial

Utilizarla como modelo interpretable de referencia para desenlaces mutuamente excluyentes:

- Custodia materna.
- Custodia paterna.
- Custodia conjunta.

Incluir otras categorías solamente cuando la estructura y frecuencia de los datos justifiquen su modelado.

Evaluar:

- Coeficientes.
- Razones de riesgo relativo multinomial.
- Intervalos de confianza.
- Variables asociadas.
- Interacciones.
- Calibración.
- Estabilidad temporal.

Considerar modelos multinivel cuando la estructura territorial y temporal lo justifique.

## 6.2 CatBoost

Entrenar modelos de clasificación multiclase con CatBoost.

Explorar relaciones no lineales e interacciones entre variables.

Comparar contra la regresión multinomial utilizando:

- Log-loss.
- Brier score multiclase.
- Calibración por categoría.
- Matrices de confusión.
- Métricas por clase.
- Desempeño por entidad.
- Desempeño por sexo.
- Robustez temporal.

Utilizar SHAP para interpretación, aclarando que las contribuciones del modelo no demuestran causalidad.

No seleccionar el modelo únicamente por exactitud global.

## 6.3 Validación temporal

Evitar particiones aleatorias como única estrategia de validación.

Usar años anteriores para entrenamiento, años posteriores para validación y el periodo más reciente disponible como prueba temporal final.

Definir los cortes según la disponibilidad real de los datos.

Prevenir fugas de información, especialmente cuando las variables se generan durante o después de la resolución de custodia.

Separar variables predictoras conocidas antes de la resolución de aquellas que describen el resultado judicial.

Realizar análisis de sensibilidad por entidad, periodo y categorías poco frecuentes.

## 6.4 Aprendizaje no supervisado

Explorar técnicas de agrupamiento para identificar perfiles sociodemográficos de divorcio.

Considerar métodos apropiados para variables mixtas y evaluar estabilidad e interpretabilidad.

No presentar los grupos como tipos psicológicos o categorías clínicas.

---

# 7. PERFILADOR ESTADÍSTICO INTERACTIVO

Crear una experiencia visual denominada:

**Explora tu perfil estadístico de custodia**

El usuario podrá seleccionar características disponibles en los microdatos, por ejemplo:

- Entidad.
- Municipio.
- Año o periodo.
- Sexo y edad de ambos divorciantes.
- Escolaridad.
- Situación laboral.
- Número de hijos.
- Duración del matrimonio.
- Municipio de residencia habitual de cada persona.

No solicitar nombres, domicilios exactos, expedientes ni información identificable de menores.

La interfaz mostrará tres resultados diferentes.

### A. Evidencia histórica

Frecuencias observadas en registros comparables.

Mostrar número de observaciones, periodo y grado de comparabilidad.

### B. Estimación estadística

Si el modelo supera los criterios de validación, mostrar probabilidades estimadas de las distintas categorías de custodia.

Las probabilidades deberán sumar 100% dentro del conjunto de categorías modeladas.

Presentar incertidumbre, desempeño del modelo y limitaciones.

### C. Comparación territorial

Comparar el perfil con estadísticas nacionales, estatales y municipales.

No producir estimaciones municipales específicas cuando el volumen o calidad de los datos sea insuficiente.

Mostrar un aviso permanente:

*Esta herramienta describe patrones históricos y estimaciones estadísticas. No predice la decisión de un juez en un caso individual ni constituye asesoría jurídica.*

No publicar el perfilador hasta demostrar calibración y desempeño aceptables.

---

# 8. COMPARADOR DE ESCENARIOS

Permitir comparar dos perfiles hipotéticos simultáneamente.

Ejemplos:

- Misma entidad frente a otra entidad.
- Mismo municipio frente a municipios diferentes.
- Diferentes niveles de escolaridad.
- Diferentes periodos.
- Diferencias de edad.
- Cambios en el número de hijos.

Mostrar diferencias absolutas entre estimaciones y gráficos comparativos.

Permitir mantener constantes las demás variables.

Explicar que cambiar una variable en el modelo no equivale a demostrar que modificarla en la realidad cambiaría una decisión judicial.

---

# 9. ATLAS GEOGRÁFICO

Construir mapas interactivos de México con MapLibre GL y datos geográficos oficiales.

Permitir navegación:

Nacional → Estado → Municipio.

Incluir:

- Tasas de divorcio.
- Frecuencia de custodia conjunta.
- Distribución de modalidades de custodia.
- Cambios históricos.
- Indicadores de calidad de datos.
- Comparación entre territorios.

Usar claves oficiales de entidad y municipio.

No calcular distancias entre domicilios individuales a partir de simples códigos municipales.

Si se dispone de residencia municipal de ambas personas, permitir clasificar coincidencia o diferencia de municipio y, opcionalmente, estimar distancia entre centroides municipales, etiquetándola claramente como aproximación geográfica.

Aplicar supresión o agregación cuando existan celdas pequeñas que puedan comprometer la privacidad.

---

# 10. OBSERVATORIO LEGISLATIVO

Crear un módulo independiente que documente:

- Legislación aplicable en las 32 entidades.
- Disposiciones sobre guarda y custodia.
- Regulación de custodia compartida.
- Patria potestad.
- Convivencia familiar.
- Reformas relevantes.
- Fechas de entrada en vigor.
- Fuentes oficiales y enlaces.

Distinguir entre existencia de una norma, fecha de vigencia y aplicación efectiva.

Permitir análisis exploratorios entre cambios normativos y tendencias estadísticas, sin atribuir causalidad automáticamente.

---

# 11. INVESTIGACIÓN Y PUBLICACIONES

Incorporar un laboratorio de investigación con capacidad para generar:

- Tablas descriptivas.
- Análisis bivariados.
- Modelos multivariables.
- Gráficas exportables.
- Informes estatales.
- Series históricas.
- Documentos metodológicos.
- Reportes reproducibles con Quarto.

Incluir un catálogo de investigaciones potenciales:

1. Evolución de la custodia conjunta en México.
2. Diferencias estadísticas de custodia según sexo.
3. Características sociodemográficas asociadas a modalidades de custodia.
4. Variabilidad territorial en decisiones registradas.
5. Cambios normativos y tendencias de custodia.
6. Predicción estadística de modalidades de custodia.
7. Calidad y completitud de los registros oficiales.
8. Diferencias entre divorcios judiciales y administrativos.
9. Relación entre duración matrimonial, hijos y custodia.
10. Cambios históricos en patria potestad y pensiones alimenticias.

Los informes deberán poder reproducirse a partir de datos y código versionados.

---

# 12. DISEÑO WEB Y EXPERIENCIA DE USUARIO

Desarrollar una aplicación moderna utilizando:

- React.
- TypeScript.
- Vite.
- Tailwind CSS.
- Apache ECharts.
- MapLibre GL.
- DuckDB-Wasm cuando resulte apropiado.

La plataforma deberá funcionar en:

- Computadoras.
- Tabletas.
- Teléfonos Android e iOS.

Utilizar una identidad visual propia, independiente de Doctor Data MX.

Paleta sugerida:

- Azul petróleo.
- Turquesa.
- Blanco cálido.
- Gris pizarra.
- Acentos dorados discretos.

Diseñar una experiencia profesional, académica y contemporánea.

Evitar interfaces recargadas.

Incluir:

- Filtros persistentes.
- Gráficas interactivas.
- Tooltips informativos.
- Comparaciones visuales.
- Modo claro y oscuro.
- Exportación CSV, PNG y SVG.
- Enlaces para compartir exploraciones.
- Navegación accesible.
- Indicadores de carga.
- Mensajes claros cuando no existan datos suficientes.

No almacenar datos personales introducidos por usuarios.

Si se comparten perfiles mediante URL, evitar incluir información potencialmente sensible en enlaces públicos.

---

# 13. ESTRUCTURA DEL REPOSITORIO

Nombre sugerido:

`observatorio-divorcios-mx`

Organización propuesta:

```text
observatorio-divorcios-mx/
├── README.md
├── LICENSE
├── CITATION.cff
├── docs/
│   ├── metodologia/
│   ├── diccionario/
│   ├── fuentes/
│   └── investigaciones/
├── data/
│   ├── raw/
│   ├── staging/
│   ├── curated/
│   └── analytics/
├── pipelines/
│   ├── download/
│   ├── validate/
│   ├── transform/
│   └── aggregate/
├── analysis/
│   ├── descriptive/
│   ├── inferential/
│   └── geospatial/
├── ml/
│   ├── training/
│   ├── evaluation/
│   ├── explainability/
│   └── artifacts/
├── reports/
├── web/
│   ├── src/
│   ├── public/
│   └── package.json
├── tests/
└── .github/
    └── workflows/
```

Ajustar la estructura si existe una alternativa más eficiente, manteniendo separación clara entre fuentes, procesamiento, análisis, modelos e interfaz.

---

# 14. ACTUALIZACIÓN AUTOMÁTICA

Implementar GitHub Actions para:

1. Verificar periódicamente nuevas publicaciones del INEGI.
2. Detectar nuevos archivos y cambios de versión.
3. Descargar fuentes oficiales.
4. Ejecutar validaciones.
5. Actualizar indicadores.
6. Ejecutar pruebas automatizadas.
7. Generar artefactos optimizados.
8. Publicar la nueva versión del sitio.

No reentrenar modelos automáticamente sin validación de desempeño.

Registrar fecha de última actualización y periodo cubierto.

Si una fuente cambia de estructura, detener el procesamiento correspondiente y generar un reporte de incompatibilidad.

---

# 15. PRINCIPIOS METODOLÓGICOS Y ÉTICOS

La plataforma deberá cumplir estos principios:

**Neutralidad analítica:** presentar diferencias estadísticas sin conclusiones preconcebidas.

**Reproducibilidad:** permitir auditar procedimientos y resultados.

**Transparencia:** documentar fuentes, definiciones, transformaciones y limitaciones.

**Privacidad:** evitar exposición de registros potencialmente identificables.

**Precisión:** distinguir observaciones, asociaciones y predicciones.

**No causalidad implícita:** no interpretar automáticamente asociaciones como efectos causales.

**Responsabilidad jurídica:** no presentar estimaciones estadísticas como pronósticos legales individuales.

**Enfoque en infancia:** reconocer que los registros de divorcio no permiten evaluar directamente el bienestar infantil ni la calidad de las relaciones familiares.

**Calidad de datos:** no generar indicadores ni predicciones con información insuficiente sin advertencias explícitas.

---

# 16. PLAN DE EJECUCIÓN

Desarrollar el proyecto por fases.

## Fase 1. Descubrimiento y auditoría

- Localizar fuentes oficiales.
- Descargar microdatos y diccionarios.
- Auditar variables y codificaciones.
- Verificar cobertura histórica.
- Identificar variables disponibles para custodia.
- Construir matriz de comparabilidad.
- Generar informe de factibilidad.

Entregable: auditoría completa y pipeline reproducible.

## Fase 2. Plataforma estadística

- Dashboard nacional.
- Explorador de variables.
- Mapas.
- Series históricas.
- Análisis por sexo.
- Módulo de hijos y custodia.

Entregable: plataforma funcional con datos validados.

## Fase 3. Laboratorio estadístico y ML

- Regresión multinomial.
- CatBoost.
- Validación temporal.
- Calibración.
- Análisis SHAP.
- Evaluación por sexo y entidad.

Entregable: informe comparativo y modelos versionados.

## Fase 4. Perfilador interactivo

- Constructor de perfiles.
- Frecuencias históricas.
- Predicciones validadas.
- Comparador de escenarios.
- Visualización de incertidumbre.

Entregable: perfilador público, únicamente si cumple los criterios de calidad.

## Fase 5. Expansión

- Observatorio legislativo.
- Informes estatales.
- Laboratorio de investigación.
- Automatización de actualizaciones.
- Documentación científica.

Entregable: observatorio integral.

---

# 17. INSTRUCCIONES FINALES PARA CODEX

Comienza inspeccionando el entorno de trabajo y el repositorio.

Si el repositorio no existe, prepara la estructura del proyecto y verifica la configuración de Git y GitHub antes de intentar publicarlo.

**No afirmes haber descargado, procesado o validado archivos si no existen evidencias verificables de esas operaciones.**

Primero ejecuta la auditoría de fuentes y variables.

Después desarrolla una versión mínima funcional del observatorio con datos oficiales validados.

No utilices datos inventados para alimentar indicadores públicos.

No publiques modelos predictivos sin evaluación temporal, calibración y documentación.

Prioriza código mantenible, pruebas automatizadas, rendimiento y trazabilidad.

Documenta cada decisión metodológica importante.

Al terminar cada fase, informa:

- Qué se implementó.
- Qué archivos se descargaron realmente.
- Cuántos registros se procesaron.
- Qué pruebas se ejecutaron.
- Qué resultados se validaron.
- Qué limitaciones se detectaron.
- Qué tareas quedan pendientes.

**Objetivo final:** construir un observatorio nacional interactivo, científicamente defendible, visualmente atractivo y reproducible, que permita explorar integralmente el divorcio y la custodia en México, así como investigar patrones estadísticos mediante métodos tradicionales y aprendizaje automático.

Inicia con la Fase 1 y avanza a las siguientes fases cuando sus criterios de validación estén satisfechos.
