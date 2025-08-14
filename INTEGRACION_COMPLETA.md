# KRONOS - Integración Frontend-Backend Completa

Esta guía te ayuda a ejecutar la aplicación KRONOS completa con frontend y backend integrados.

## ¿Qué se ha configurado?

✅ **Backend configurado** para servir desde `Frontend/dist/` (build de producción) o `Frontend/` (desarrollo)
✅ **Script de automatización** `build.bat` creado para build de frontend
✅ **Vite configurado** con optimizaciones para aplicación de escritorio
✅ **Documentación actualizada** con instrucciones de uso integrado
✅ **Archivo .gitignore** configurado para excluir archivos de build

## Instrucciones de Uso

### OPCIÓN 1: Uso Rápido (Recomendado)

```bash
# 1. Desde el directorio raíz del proyecto
build.bat

# 2. Ejecutar aplicación completa
cd Backend
python main.py
```

### OPCIÓN 2: Comandos Manuales

```bash
# 1. Instalar dependencias (primera vez)
cd Frontend
npm install

# 2. Compilar frontend para producción
npm run build

# 3. Ejecutar backend (desde Backend/)
cd ../Backend
python main.py
```

## Modos de Ejecución

### Modo Producción (Recomendado)
- El backend busca archivos compilados en `Frontend/dist/`
- Mejor rendimiento y carga más rápida
- Requiere ejecutar build cada vez que cambies el frontend

### Modo Desarrollo (Fallback)
- El backend usa archivos fuente de `Frontend/` directamente
- Se activa automáticamente si no existe `Frontend/dist/`
- Útil para depuración, pero más lento

## Verificación

Si todo está configurado correctamente:

1. Ejecutas `build.bat` → Compila frontend sin errores
2. Ejecutas `cd Backend && python main.py` → Se abre ventana de la aplicación
3. El log del backend debe mostrar: "Usando build de producción desde Frontend/dist/"

## Troubleshooting

### Error: "No se encontró ni build de producción ni fuentes de desarrollo"
**Solución**: Ejecuta `build.bat` desde el directorio raíz del proyecto

### Error: "npm run build falló"
**Solución**: 
```bash
cd Frontend
npm install
npm run build
```

### Error: "python main.py no funciona"
**Solución**: 
```bash
cd Backend
pip install -r requirements.txt
python main.py
```

### La aplicación carga lento
**Causa**: Estás en modo desarrollo. Ejecuta `build.bat` para usar modo producción.

## Archivos Importantes

- `build.bat` - Script de automatización para build
- `Backend/main.py` - Backend con lógica de detección automática
- `Frontend/vite.config.ts` - Configuración optimizada para Eel
- `Frontend/dist/` - Archivos compilados (generados por build)

## Flujo de Desarrollo

1. **Desarrollo frontend**: `cd Frontend && npm run dev` (para desarrollo en vivo)
2. **Test integrado**: `build.bat && cd Backend && python main.py`
3. **Distribución**: Usa siempre el build de producción

---

**¡La integración está completa!** Solo ejecuta `build.bat` y luego `cd Backend && python main.py` para tener la aplicación funcionando.