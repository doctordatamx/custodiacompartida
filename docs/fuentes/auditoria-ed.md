# Auditoría de la Estadística de Divorcios

El 5 de noviembre de 2026 se descargaron los paquetes oficiales de 2023, 2024 y 2025. Cada paquete contiene los microdatos, su diccionario, catálogos y metadatos. La unidad de observación es un registro de divorcio. [Portal oficial de datos abiertos](https://www.inegi.org.mx/programas/ed/#datos_abiertos)

| Año | Registros | Judiciales | Administrativos | Bytes del ZIP | SHA-256 |
| --- | ---: | ---: | ---: | ---: | --- |
| [2023](https://www.inegi.org.mx/contenidos/programas/ed/datosabiertos/conjunto_de_datos_ed2023_csv.zip) | 163 587 | 147 262 | 16 325 | 4 496 289 | `7ffce6d3d5e6e5833320595789a26ba8eedb21e93759bb34b746dc1b17717a7c` |
| [2024](https://www.inegi.org.mx/contenidos/programas/ed/datosabiertos/conjunto_de_datos_ed2024_csv.zip) | 161 932 | 145 043 | 16 889 | 4 871 390 | `13e0c2c72f90ea0d1900c2dfaae782bcd7a77cb80126abfbd53375ad5d61fbf2` |
| [2025](https://www.inegi.org.mx/contenidos/programas/ed/datosabiertos/conjunto_de_datos_ed2025_csv.zip) | 155 254 | 137 155 | 18 099 | 4 714 180 | `e909937c42bbb2872d78e9afa8c583c3798a92b07ee8383c817340543391d4c2` |

Los tres ZIP pasaron la comprobación CRC. Cada CSV contiene las 64 variables declaradas y registros de las 32 entidades. Los totales y los porcentajes judiciales redondeados coinciden con los comunicados. Los siete conteos por código de custodia de 2024 coinciden con la Red Nacional de Metadatos. Las combinaciones geográficas observadas coinciden con el catálogo distribuido para cada año, que incluye claves especiales. [Resultados 2023](https://www.inegi.org.mx/contenidos/saladeprensa/boletines/2024/ED/ED2023.pdf), [resultados 2024](https://www.inegi.org.mx/contenidos/saladeprensa/boletines/2025/ed/ed2024_RR.pdf), [resultados 2025](https://en.www.inegi.org.mx/app/saladeprensa/noticia/11248), [frecuencias de custodia 2024](https://www.inegi.org.mx/rnm/index.php/catalog/1133/variable/F4/V27?name=Custodia)

## Hallazgos de calidad

- **2023.** Hay dos filas adicionales idénticas a otras filas. Se conservan porque la tabla pública carece de un identificador que permita establecer que corresponden al mismo expediente. También hay 637 registros con municipio de matrimonio `999`, presente en el catálogo geográfico y fuera del rango declarado en el diccionario de ese año.
- **2024.** Hay 21 registros con años de matrimonio de 1950 a 1956 que el diccionario admite y el catálogo de años omite.
- **2025.** El catálogo de años omite 2025, aunque el diccionario admite el valor para año de matrimonio y de presentación de la demanda. Afecta a 1 033 y 94 671 registros, respectivamente. El programa corrige la codificación de seis referencias a catálogos de año al abrir los archivos y conserva el diccionario original en el reporte.

## Comparabilidad y factibilidad

| Variables | 2023–2025 | Criterio de uso |
| --- | --- | --- |
| Tipo de trámite, custodia, sexo, número de hijos, patria potestad y pensión | Mismas columnas y catálogos idénticos en los paquetes | Comparar en el mismo universo y conservar los códigos especiales por separado. |
| Entidad, municipio y localidad | Misma estructura, catálogos específicos del año | Distinguir registro de divorcio, registro de matrimonio y residencia. Homologar cambios de clave antes de publicar series municipales. |
| Edad, escolaridad y actividad económica | Columnas presentes los tres años | Auditar códigos especiales, cobertura y universo por trámite antes de combinar periodos. |
| Años anteriores a 2023 | Microdatos auditados desde 1985 | Consulta la [auditoría histórica](auditoria-ed-historica.md) para los cambios de captación, codificación y cobertura territorial. |

[Tabulador histórico](https://www.inegi.org.mx/sistemas/olap/Proyectos/bd/continuas/nupcialidad/Divorcios.asp?s=est), [metodología de la edición 2024](https://www.inegi.org.mx/rnm/index.php/catalog/1133)

En custodia, el CSV usa `0` para no otorgada, `1` y `2` para la persona divorciante correspondiente, `3` para ambas, `4` para otra persona, `98` para no aplicable y `99` para no especificada. Las etiquetas de sexo deben derivarse de `sexo_div1` o `sexo_div2` según la persona registrada. La categoría «ambos» se presenta con la etiqueta del catálogo. El registro carece del detalle necesario para determinar el arreglo concreto de guarda. [Ficha de custodia](https://www.inegi.org.mx/rnm/index.php/catalog/1133/variable/F4/V27?name=Custodia)

Para el panorama general se usa el total de divorcios registrados. Para replicar la distribución de custodia publicada por INEGI se usa el total judicial. Un análisis centrado en hijos menores utiliza los divorcios judiciales con `hij_men` positivo y conocido. Debe distinguirse ese universo de una proporción calculada exclusivamente entre asignaciones documentadas. El conteo de divorcios y la suma de menores son medidas distintas. [Reporte de resultados 2024](https://www.inegi.org.mx/contenidos/saladeprensa/boletines/2025/ed/ed2024_RR.pdf)

La conciliación permite preparar indicadores descriptivos nacionales y estatales para 2023–2025. Queda pendiente resolver la homologación municipal y revisar las variables disponibles antes de la resolución para cualquier análisis predictivo.
