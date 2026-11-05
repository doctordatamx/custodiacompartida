# Auditoría histórica de divorcios, 1985–2022

Se descargaron 16 ZIP oficiales del inventario de la Estadística de Divorcios. Diez contienen los DBF de los 38 años y seis contienen una edición CSV adicional de 2017 a 2022. Los originales están en `data/raw/`. En el [portal oficial](https://www.inegi.org.mx/programas/ed/#microdatos), 1985 es el primer año del inventario de microdatos. La [cobertura estadística del programa](https://www.inegi.org.mx/programas/ed/) comienza en 1926.

## Resultados

- Los 38 DBF contienen 2 964 001 registros. Cada total anual coincide con una publicación del INEGI y cada archivo anual cubre las 32 entidades de registro. [Anuario 1996, cuadro 2.11](https://www.inegi.org.mx/contenidos/productos/prod_serv/contenidos/espanol/bvinegi/productos/historicos/1329/702825149253/702825149253_1.pdf), [Anuario 2019, cuadro 2.14](https://en.www.inegi.org.mx/contenidos/productos/prod_serv/contenidos/espanol/bvinegi/productos/nueva_estruc/AEGEUM_2019/702825192235.pdf), [ED 2023, gráfica 1](https://www.inegi.org.mx/contenidos/saladeprensa/boletines/2024/ED/ED2023.pdf)
- Los CSV de 2017–2022 coinciden con los DBF en el total, los conteos por entidad y las frecuencias de 13 campos clave. Sus encabezados coinciden con los diccionarios CSV. El diccionario de 2017 declara 2016 como año de ejecutoria, mientras que el DBF y el CSV contienen 2017 en los 147 581 registros.
- Se identificaron 824 filas adicionales idénticas a otras filas del DBF del mismo año. Se conservan para conciliar con los totales oficiales. La coincidencia de campos por sí sola es insuficiente para identificar un mismo expediente.

- La clave de matrimonio es `88/888` en todos los registros de 1985–1992. En 2012 quedaron 4 064 combinaciones de matrimonio sin correspondencia en el catálogo del ZIP. En 2020 quedaron 123 registros con claves de localidad de divorcio sin correspondencia y también se observaron excepciones de matrimonio y residencia. El reporte conserva los códigos originales y sus frecuencias.

## Comparabilidad

| Periodo | Campos en el DBF | Tratamiento |
| --- | ---: | --- |
| 1985–1992 | 52 | Custodia contiene exclusivamente el código 88. Excluir estas ediciones de las series de modalidades. |
| 1993–2001 | 52 | Ya se observan varias categorías de custodia. INEGI cambió el proceso de captación en 1993 para reducir la duplicación entre fuentes. Oaxaca se publica por distrito hasta 2001. |
| 2002–2013 | 56 | El diccionario describe madre y padre como destinatarios de custodia. Las ediciones 2004 y 2005 contienen el código 9 en lugar de los códigos especiales 98 y 99 observados en ediciones cercanas. INEGI modificó la captación de custodia y patria potestad en 2010. |
| 2014 | 59 | La asignación pasa a identificar a la primera o segunda persona divorciante. Se agregan los campos de sexo y tipo de divorciante. |
| 2015–2022 | 64 | Se mantiene el esquema general reciente. Las comparaciones requieren controlar cambios de catálogo y usar el mismo denominador. |

[Metadatos 1985–2001](https://www.inegi.org.mx/rnm/index.php/catalog/267), [diccionario 2002–2013](https://www.inegi.org.mx/rnm/index.php/catalog/261/data-dictionary/F2), [metodología 2002–2013](https://www.inegi.org.mx/rnm/index.php/catalog/261), [diccionario 2014](https://www.inegi.org.mx/rnm/index.php/catalog/256/data-dictionary/F1)

La revisión geográfica contrasta las claves de registro, matrimonio y residencia con los catálogos de cada paquete. La coincidencia de una clave con su catálogo anual es una comprobación de integridad. Para comparar municipios entre años todavía se necesita homologar los cambios territoriales.

## Reproducción

Con Python 3.11 o posterior:

```powershell
python pipelines/audit_ed_historica.py --download
```

El comando descarga los archivos faltantes y genera `data/analytics/auditoria-ed-historica.json`. El reporte incluye URL, tamaño, SHA-256, miembros del ZIP, campos DBF, excepciones geográficas, conteos por entidad y la conciliación anual. Los DBF se leen directamente del ZIP. Los rangos del diccionario se verificaron en los campos clave de las seis ediciones CSV. En DBF se registró el esquema, la integridad estructural y las frecuencias, con las guías PDF originales disponibles dentro de cada paquete para la homologación.
