# Laboratorio de asignación de custodia

El experimento estima la distribución de tres asignaciones registradas entre divorcios judiciales con menores y un destinatario clasificable. Las clases son ambas personas, una mujer y un hombre. La asignación individual se clasifica con el sexo registrado de la persona correspondiente. Se excluyen del modelado las demás asignaciones y los registros sin clasificación suficiente. Los conteos de cada exclusión se conservan en el reporte por edición.

## Variables y periodo

| Uso | Variables | Decisión |
| --- | --- | --- |
| Predictores | Composición por sexo, edades aproximadas al registro de la demanda, años entre el registro del matrimonio y el de la demanda, entidad de registro del matrimonio | Derivados de datos que corresponden al inicio de la demanda o a hechos anteriores. Las edades y la duración se calculan por diferencia de años calendario. Se ordena a las personas por sexo y año de nacimiento para evitar que su posición en el expediente actúe como predictor. |
| Selección del universo | Trámite judicial, número de menores registrado y categoría de custodia | Delimitan una cohorte retrospectiva. El número de menores se usa solo para identificar los casos elegibles. |
| Evaluación | Edición, año de registro de la demanda y entidad de registro del divorcio | La edición define los cortes temporales. La entidad se usa para desglosar métricas. La prueba de sensibilidad conserva únicamente las demandas registradas en 2025 dentro de esa edición. |
| Campos excluidos | Fecha y resultado de sentencia, ejecutoria, pensión, patria potestad, duración publicada, edad al divorcio y variables de residencia o empleo | Los primeros describen la resolución o se calculan con información posterior. Para residencia y empleo se desconoce si el valor en el archivo representa la situación al inicio. |

[Diccionario de la Estadística de Divorcios 2024](https://www.inegi.org.mx/rnm/index.php/catalog/1133/data-dictionary/F4), [datos abiertos del INEGI](https://www.inegi.org.mx/programas/ed/#datos_abiertos)

El análisis final entrenó con las ediciones 2018–2022. Se excluyó 2017 tras detectar una ruptura en la distribución de asignaciones por sexo respecto de las ediciones contiguas. El origen de esa ruptura queda por confirmar. La edición 2025 ya se había evaluado en la primera corrida, que incluyó 2017. Las ediciones 2023–2024 se usaron para calibrar las probabilidades mediante ajuste de temperatura y elegir entre regresión logística y CatBoost. La edición 2025 se reservó para evaluar el desempeño. La referencia asigna a todos los casos las frecuencias de las tres clases durante el entrenamiento.

Para considerar que un modelo merece evaluación adicional se exigió una reducción de al menos 1% en la pérdida logarítmica frente a la referencia, un error de calibración de hasta 3 puntos porcentuales en cada clase y una mejora en el subconjunto de demandas de 2025. Estos son criterios exploratorios. La sensibilidad por año de demanda sigue condicionada a que el divorcio haya quedado registrado en 2025. El archivo carece de las demandas todavía pendientes, por lo que el estudio caracteriza divorcios observados y deja por evaluar el uso prospectivo.

## Resultados de la prueba de 2025

Se evaluaron 58 936 registros elegibles. CatBoost, elegido con los datos de 2023–2024, redujo la pérdida logarítmica un 5,2 % frente a las frecuencias históricas y cumplió los tres criterios exploratorios.

| Modelo | Pérdida logarítmica | Brier multiclase |
| --- | ---: | ---: |
| Frecuencias históricas | 0,6966 | 0,3786 |
| Regresión logística | 0,6673 | 0,3660 |
| CatBoost | 0,6602 | 0,3612 |

El error de calibración de CatBoost fue de 1,70 puntos porcentuales para ambas personas, 1,84 para un hombre y 1,18 para una mujer. La prueba se limita a divorcios registrados con asignación clasificable. El desempeño agregado tampoco establece que la calibración se mantenga en cada entidad o en grupos con pocos registros.

[Validación territorial de CatBoost](validacion-territorial-custodia.md)

## Reproducción

Desde la raíz, con los microdatos y las auditorías locales disponibles:

```powershell
python -m pip install -r pipelines/requirements-lab.txt --target data/analytics/model-deps
$env:PYTHONPATH = (Resolve-Path data/analytics/model-deps).Path
python pipelines/evaluate_custody_models.py
```

El programa escribe métricas agregadas en `data/analytics/laboratorio-custodia.json`. El orden de las clases para las matrices de confusión figura en el propio reporte. Los desgloses de desempeño requieren al menos 100 registros por grupo. Los valores SHAP resumen contribuciones al modelo CatBoost en una muestra fija de 400 registros de 2025.
