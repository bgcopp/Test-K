Visualización de Diagrama de Correlación de Red
📋 CONTEXTO
La funcionalidad de análisis de correlación está operativa y genera una tabla con las coincidencias entre números celulares y celdas. Se requiere agregar una visualización gráfica que represente estas relaciones de forma visual e intuitiva.
🎯 OBJETIVO
Implementar una visualización de diagrama de red que muestre las relaciones entre números celulares, indicando las celdas donde se realizaron las comunicaciones y la direccionalidad de las llamadas.
📐 ESPECIFICACIONES FUNCIONALES
1. Barra de Herramientas

Ubicación: Parte superior de la Tabla de Correlación
Componente principal: Botón con icono representativo de red/diagrama
Texto del botón: "Visualizar Diagrama de Correlación"
Acción: Abrir modal con el diagrama

2. Modal de Visualización

Tipo: Modal centrado con overlay oscuro
Tamaño: 90% del ancho y 85% del alto de la pantalla
Elementos:

Título: "Diagrama de Correlación de Red"
Botón cerrar (X) en esquina superior derecha
Área de visualización del diagrama
Controles de interacción en la parte inferior



3. Elementos del Diagrama
3.1 Nodos (Números Celulares)
Basado en la imagen de referencia:

Forma: Circular
Contenido: Icono de persona/avatar genérico
Colores de borde distintivos:

Rojo: Nodo principal o de mayor correlación
Naranja: Alta correlación
Rosa: Media correlación
Verde: Baja correlación
Morado: Relaciones indirectas


Etiqueta: Número celular debajo del nodo

3.2 Enlaces (Conexiones)

Representación: Flechas que conectan los nodos
Direccionalidad:

Flecha simple: Llamada unidireccional
Doble flecha: Comunicación bidireccional


Etiquetas en enlaces: IDs de celdas donde ocurrieron las comunicaciones (ej: "56124", "53591")
Visualización: Las etiquetas deben ser legibles con fondo blanco semi-transparente

3.3 Layout del Diagrama

Distribución: Force-directed (los nodos se auto-organizan evitando superposiciones)
Nodo central: El número con mayor correlación debe posicionarse al centro
Espaciado: Suficiente separación entre nodos para legibilidad

4. Interactividad
Acciones sobre nodos:

Hover: Resaltar el nodo y sus conexiones directas
Click: Mostrar información detallada del número
Arrastrar: Permitir reorganización manual de nodos

Acciones sobre enlaces:

Hover: Resaltar la conexión y mostrar detalles
Click: Ver historial de comunicaciones entre los números

Controles del diagrama:

Zoom in/out
Restablecer vista
Ajustar a pantalla
Cambiar tipo de layout (force-directed, circular, jerárquico)

5. Filtros y Opciones

Filtro de correlación mínima: Slider para mostrar solo nodos con correlación >= X
Mostrar/ocultar IDs de celda: Checkbox
Mostrar/ocultar nodos sin conexiones: Checkbox

6. Exportación

Exportar como imagen (PNG)
Exportar como imagen vectorial (SVG)
Exportar datos del diagrama (JSON)

📊 DATOS REQUERIDOS
El diagrama debe construirse con los siguientes datos:

Números celulares de la tabla de correlación
Score de correlación de cada número
IDs de celdas donde se detectaron coincidencias
Información de llamadas entre números (origen, destino)
Operador de cada número (si está disponible)

🎨 REFERENCIA VISUAL
El diagrama debe seguir el estilo de la imagen proporcionada:

Nodos circulares con avatar genérico
Números celulares como etiquetas
Flechas con IDs de celda
Colores distintivos para diferentes niveles de correlación
Layout que evite cruces excesivos de líneas

📚 LIBRERÍAS SUGERIDAS (Compatibles con Vite)
Se sugiere evaluar las siguientes opciones aunque preferiria algo como Cytoscape.js o React Flow:

Cytoscape.js: Especializada en grafos de red, excelente rendimiento
D3.js: Máxima flexibilidad y personalización
Vis.js / vis-network: Simple de implementar, buena documentación
Sigma.js: Optimizada para grafos grandes
React Flow: Si el proyecto usa React, integración nativa
G6 (AntV): Moderna, con layouts predefinidos

debes dejar ver tu preferencia.

✅ CRITERIOS DE ACEPTACIÓN

El diagrama debe visualizar todos los números de la tabla de correlación
Las conexiones deben mostrar los IDs de celda claramente
La direccionalidad de las llamadas debe ser evidente
Los colores deben corresponder al nivel de correlación
El diagrama debe ser interactivo y permitir exploración
Debe ser posible exportar la visualización
El rendimiento debe ser fluido con hasta 100 nodos
La interfaz debe ser intuitiva y no requerir manual

🧪 ESCENARIOS DE PRUEBA

Caso mínimo: 2 nodos con 1 conexión
Caso típico: 6-10 nodos con múltiples conexiones (como la imagen de referencia)
Caso complejo: 50+ nodos densamente conectados
Caso edge: Nodos sin conexiones (aislados)
Validación de datos: IDs de celda correctamente mostrados
Validación visual: Colores y direccionalidad según especificación

📝 NOTAS Y CONSIDERACIONES

El diagrama debe actualizarse si cambian los filtros de fecha en la vista principal
Considerar límite de nodos visibles para mantener legibilidad
Los IDs de celda deben permanecer legibles incluso con zoom out moderado
Mantener consistencia visual con el resto de la aplicación