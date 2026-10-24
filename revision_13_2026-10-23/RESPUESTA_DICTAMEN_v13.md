# Respuesta focalizada al dictamen de v12

La revisión conserva el argumento y la organización del artículo. Añade únicamente la comprobación numérica de S20 y aclara el alcance de las observaciones retenidas. No se repite la campaña de 1800 inversiones ni se presenta el dictamen simulado como una decisión oficial de MMT.

## M1 Precisión del contraste nanométrico

Se repiten las ocho fases de S20 a h=0.35 mm con cuatro variantes: referencia; ordenación alternativa de LU y cuatro correcciones residuales elásticas con pulido del sistema de contacto a 80 dígitos; extensión armónica ponderada con el mismo contorno; e interfaz de 0.01 mm sobre estas mismas fases. El ensamblaje global elástico conserva aritmética float64. LU es un método directo, por lo que cambiar solamente una tolerancia del optimizador de contacto no certificaría la precisión del sistema elástico.

| Control | Profundidad µm | RMS señal nm | Cambio RMS de curva nm |
|---|---|---|---|
| baseline | 10 | 0.3996764 | 0 |
| baseline | 50 | 2.0787033 | 0 |
| enhanced_algebra | 10 | 0.39967641 | 7.5433963e-09 |
| enhanced_algebra | 50 | 2.0787033 | 9.0580616e-09 |
| weighted_morph | 10 | 0.39961986 | 7.3414243e-05 |
| weighted_morph | 50 | 2.0784306 | 0.00035819312 |
| fine_interface | 10 | 0.39787946 | 0.0037806656 |
| fine_interface | 50 | 2.0692672 | 0.019724714 |

Máximo cambio nominal por reensamblaje: 2.13995e-08 nm. Máximo cambio de la repetición respecto a los registros v12: 1.38778e-11 nm. Los cambios de curva se calculan después de centrar en las mismas ocho fases; no son sólo diferencias entre dos valores RMS.

La Tabla S21 informa controles empíricos de estabilidad. No se presenta una cota rigurosa del error total ni una validación metrológica del efecto. La aritmética de 80 dígitos se aplica únicamente al sistema condensado de contacto, no a todo el FE. El nivel de ruido supuesto es 100 nm por muestra; la pequeña variación estructural no acredita detectabilidad ni recuperación de parámetros.

## M2 Información excluida

La discusión declara ahora expresamente que la falta de identificación con los datos FE retenidos no demuestra insuficiencia de todas las observaciones posibles. Las fases de transición excluidas pueden aportar información; el modelo analítico lo sugiere, pero no reemplaza el contacto FE que falta resolver.

## M3 Alcance de la interfaz

S19 conserva su alcance: 24 fases, elementos P2 y geometría fija; no certifica la inversión P1 de 102 fases. El nuevo control de interfaz S21 utiliza las ocho fases de retirada física y tampoco se convierte en un certificado del ciclo completo. Esta distinción se mantiene en la documentación del paquete.

## M4 Benchmark y reconstrucción física

No se añaden afirmaciones de precisión experimental ni de reconstrucción fiable de perfiles manufacturados. La discrepancia externa permanece sin resolver y la contribución sigue condicionada al operador declarado.

## Paquete de envío

El kit contiene cuatro archivos de carga: artículo DOCX, suplemento DOCX, Highlights DOCX y ZIP reproducible. CONTENIDO_Y_SHA256.json identifica cada archivo. El ZIP del kit facilita trasladarlos conjuntamente; los cuatro deben seleccionarse individualmente en el sistema editorial según sus categorías. Preparar este kit no constituye un envío a la revista.