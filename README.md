# Observatorio de Divorcios y Custodia en México

Datos, familias y justicia.

La primera fase audita los microdatos de la Estadística de Divorcios del INEGI. Los informes cubren las 41 ediciones anuales de 1985 a 2025 y registran los límites para comparar periodos.

- [Auditoría histórica 1985–2022](docs/fuentes/auditoria-ed-historica.md)
- [Auditoría de fuentes y factibilidad 2023–2025](docs/fuentes/auditoria-ed.md)
- [Prompt maestro](PROMPT-MAESTRO.md)

## Reproducir la auditoría

Con Python 3.11 o posterior, desde la raíz del proyecto:

```powershell
python pipelines/audit_ed.py --year 2024 --download
```

También se admiten los años 2023 y 2025. Si ya existe `data/raw/ed2024.zip`, el comando usa esa copia. Para una ejecución sin red, se puede guardar el ZIP de INEGI en esa ruta y ejecutar el comando sin `--download`. El reporte local `data/analytics/auditoria-ed2024.json` incluye SHA-256, esquema, conteos por entidad, frecuencias y excepciones de calidad. El ZIP y el reporte generado se excluyen de Git.

Para reproducir el tramo histórico, ejecuta `python pipelines/audit_ed_historica.py --download`. El comando usa el inventario oficial, descarga los ZIP faltantes y genera `data/analytics/auditoria-ed-historica.json`.

## Ejecutar el tablero

```powershell
python pipelines/build_dashboard_data.py
cd web
npm ci
npm run dev
```

Vite muestra la dirección local en la terminal. `npm run build` genera la versión estática en `web/dist/`.

El panorama y la comparación estatal abarcan 1985–2025. La vista de custodia empieza en 2014 y usa como denominador los divorcios judiciales registrados. El exportador concilia los conteos por entidad con los informes de auditoría y publica únicamente agregados. Los filtros usan la entidad de registro del divorcio.

La sección **Menores** compara la entidad seleccionada con el total nacional para 2014–2025. Cuenta los divorcios judiciales con un valor positivo de `hij_men` y suma los menores registrados en esos divorcios. Los valores especiales 98 y 99 y los campos vacíos se reportan aparte. La descarga CSV contiene los dos ámbitos cuando se selecciona una entidad.

## Mapa municipal 2024–2025

En **Mapa**, selecciona el año, la entidad y el municipio o demarcación. Los conteos se vinculan por clave de registro con el Marco Geoestadístico de cada edición. Los indicadores de cambio restan 2024 a 2025 y muestran el numerador y denominador cuando la proporción de custodia está disponible.

La comparación requiere la misma clave, geometrías simplificadas iguales tras normalizar el orden de sus coordenadas y cifras disponibles en ambos años. Este criterio conservador deja 38 geometrías fuera del cálculo de cambios. La igualdad se verifica sobre las capas simplificadas.

Para regenerar el atlas, instala Shapely 2.1 o posterior y ejecuta `python pipelines/build_municipal_atlas.py --download` desde la raíz. Se requieren los microdatos y las auditorías de ambas ediciones. [Cartografía municipal 2024 del INEGI](https://lcidsig.inegi.org.mx/server/rest/services/Hosted/%C3%81reas_geoestad%C3%ADsticas_municipales_2024/FeatureServer/0), [cartografía municipal 2025 del INEGI](https://lcidsig.inegi.org.mx/server/rest/services/Hosted/Municipios_2025/FeatureServer/0).

## Laboratorio estadístico

El [informe de asignación de custodia](docs/investigaciones/laboratorio-custodia.md) documenta la cohorte, los predictores, la prueba temporal y los pasos para reproducir la evaluación.

## Perfiles históricos de custodia

La sección **Perfiles** cubre 2018–2025 y usa los mismos registros auditados del laboratorio. Los filtros agrupan por periodo, entidad de registro del divorcio, edad aproximada de la persona más joven y años de matrimonio al registrar la demanda. Se incluyen divorcios judiciales con menores, entre un hombre y una mujer, con las variables de edad y duración disponibles y una asignación a una o ambas personas.

El sitio usa conteos agregados con un mínimo de 100 divorcios por perfil y 10 por categoría. Si la diferencia respecto del total nacional revelaría un único grupo estatal reservado, se reserva un grupo adicional. Con el entorno del laboratorio activo, ejecuta `python pipelines/build_custody_profiles.py` para regenerar los perfiles.

El filtro de residencia habitual compara los municipios registrados para ambas personas según los catálogos anuales del INEGI. Distingue el mismo municipio, municipios distintos de la misma entidad, entidades distintas y registros sin dos claves municipales mexicanas válidas. Los cruces con pocos casos se reservan y se aplican reservas adicionales cuando los totales permitirían deducirlos.
