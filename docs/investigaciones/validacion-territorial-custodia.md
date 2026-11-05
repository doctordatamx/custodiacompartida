# Validación territorial del modelo de custodia

El error de calibración de CatBoost quedó por debajo de 2 puntos porcentuales en las tres categorías a nivel nacional. En la revisión de las 32 entidades, solo Coahuila reunió el volumen mínimo y quedó dentro del umbral de calibración para las tres categorías. Este resultado describe el modelo exploratorio y la edición de prueba de 2025.

Se consideró evaluable cada par de entidad y categoría con al menos 100 casos observados en esa categoría y 100 en el resto. Entre los pares evaluables, se aplicó el umbral exploratorio de 3 puntos porcentuales de error de calibración absoluto medio ponderado (ECE). El mínimo de 100 es un criterio operativo de revisión, sin interpretación como intervalo de confianza.

| Asignación | Entidades evaluables | Dentro del umbral |
| --- | ---: | ---: |
| Ambas personas | 22 | 7 |
| Un hombre | 15 | 7 |
| Una mujer | 29 | 4 |

En Ciudad de México hubo 1 306 registros elegibles. El error fue de 1,37 puntos para ambas personas, 3,41 para un hombre y 2,39 para una mujer. Las tres categorías alcanzaron el mínimo de casos.

La calibración y la clasificación responden a preguntas distintas. En la matriz nacional, al elegir la categoría con mayor probabilidad, el modelo acertó en 0 de 7 835 asignaciones a ambas personas, en 348 de 5 537 asignaciones a un hombre (6,3 %) y en 45 449 de 45 564 asignaciones a una mujer (99,7 %). La categoría mayoritaria domina las decisiones del clasificador.

El alcance respaldado por esta revisión es descriptivo. Un perfilador histórico puede mostrar frecuencias observadas con denominadores explícitos y reglas de publicación para grupos pequeños. La evaluación de un predictor para demandas nuevas requiere una cohorte de entrada con seguimiento de las resoluciones y de los casos pendientes. El análisis por composición de sexo tiene tamaño suficiente solo para parejas registradas con un hombre y una mujer.

## Detalle por entidad

Cada celda muestra casos observados y ECE en puntos porcentuales. Un guion indica que la categoría o su complemento tiene menos de 100 casos.

| Clave INEGI | Total elegible | Ambas personas | Un hombre | Una mujer |
| --- | ---: | ---: | ---: | ---: |
| 01 | 1 544 | 344 / 5,70 | 78 / — | 1 122 / 10,20 |
| 02 | 1 710 | 364 / 8,33 | 137 / 1,68 | 1 209 / 6,65 |
| 03 | 178 | 33 / — | 6 / — | 139 / — |
| 04 | 1 261 | 100 / 2,59 | 43 / — | 1 118 / 5,88 |
| 05 | 3 073 | 177 / 1,29 | 119 / 2,01 | 2 777 / 1,68 |
| 06 | 339 | 21 / — | 32 / — | 286 / — |
| 07 | 763 | 144 / 5,21 | 81 / — | 538 / 2,62 |
| 08 | 2 503 | 241 / 6,20 | 520 / 5,66 | 1 742 / 7,80 |
| 09 | 1 306 | 230 / 1,37 | 136 / 3,41 | 940 / 2,39 |
| 10 | 897 | 63 / — | 69 / — | 765 / 8,31 |
| 11 | 3 843 | 913 / 9,98 | 186 / 2,76 | 2 744 / 7,38 |
| 12 | 1 667 | 148 / 5,24 | 94 / — | 1 425 / 9,50 |
| 13 | 1 650 | 157 / 4,27 | 72 / — | 1 421 / 10,43 |
| 14 | 2 292 | 618 / 12,47 | 161 / 2,29 | 1 513 / 10,22 |
| 15 | 4 801 | 279 / 7,02 | 862 / 4,30 | 3 660 / 4,65 |
| 16 | 1 569 | 177 / 4,34 | 99 / — | 1 293 / 10,07 |
| 17 | 545 | 89 / — | 59 / — | 397 / 4,48 |
| 18 | 519 | 88 / — | 38 / — | 393 / 1,55 |
| 19 | 8 019 | 1 505 / 9,51 | 1 195 / 3,47 | 5 319 / 12,95 |
| 20 | 1 737 | 98 / — | 204 / 2,32 | 1 435 / 5,54 |
| 21 | 2 055 | 389 / 1,05 | 165 / 4,12 | 1 501 / 5,87 |
| 22 | 1 516 | 512 / 9,32 | 243 / 6,51 | 761 / 6,57 |
| 23 | 704 | 153 / 7,64 | 69 / — | 482 / 3,85 |
| 24 | 1 251 | 109 / 5,98 | 84 / — | 1 058 / 10,76 |
| 25 | 2 946 | 45 / — | 49 / — | 2 852 / — |
| 26 | 2 113 | 252 / 7,40 | 107 / 0,48 | 1 754 / 7,92 |
| 27 | 620 | 116 / 2,71 | 58 / — | 446 / 4,84 |
| 28 | 3 889 | 134 / 1,51 | 120 / 2,55 | 3 635 / 4,06 |
| 29 | 587 | 75 / — | 209 / 11,24 | 303 / 14,97 |
| 30 | 588 | 90 / — | 54 / — | 444 / 6,33 |
| 31 | 1 356 | 49 / — | 101 / 3,25 | 1 206 / 5,83 |
| 32 | 1 095 | 122 / 2,12 | 87 / — | 886 / 3,63 |

Las cifras provienen del [informe del laboratorio](laboratorio-custodia.md) y de su salida agregada local en `data/analytics/laboratorio-custodia.json`. Se calcularon a partir de `prueba_por_entidad`, las filas de las matrices de confusión y `ece_por_clase`.
