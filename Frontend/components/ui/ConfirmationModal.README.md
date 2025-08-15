# Sistema de Confirmación Modal - KRONOS

## Descripción General

El sistema de confirmación modal de KRONOS reemplaza los `window.confirm()` y `window.alert()` básicos con una interfaz moderna, profesional y accesible diseñada específicamente para aplicaciones enterprise.

## Características Principales

### ✨ Diseño y UX
- **Tema oscuro** coherente con la aplicación KRONOS
- **Animaciones suaves** de entrada y salida
- **Responsive design** para todos los dispositivos
- **Iconos contextuales** para mejor comunicación visual
- **Tipografía profesional** con jerarquía clara

### 🎨 Tipos de Confirmación
- **Destructive**: Para acciones irreversibles (eliminar misiones, usuarios)
- **Warning**: Para acciones que requieren precaución
- **Info**: Para confirmaciones informativas
- **Danger**: Para operaciones críticas del sistema

### ♿ Accesibilidad (A11y)
- **Soporte completo de teclado** (Escape para cancelar)
- **ARIA attributes** apropiados
- **Focus management** automático
- **Screen reader friendly**
- **Alto contraste** para mejor legibilidad

### ⚡ Funcionalidades Avanzadas
- **Backdrop click configurable** (habilitado/deshabilitado)
- **Callbacks personalizados** (onConfirm, onCancel)
- **Promesas nativas** para flujo async/await
- **Presets predefinidos** para casos comunes
- **Bloqueo de scroll** del body cuando está activo

## Estructura de Archivos

```
Frontend/
├── components/ui/
│   └── ConfirmationModal.tsx      # Componente modal principal
├── hooks/
│   └── useConfirmation.tsx        # Hook y provider global
├── types.ts                       # Interfaces TypeScript
├── constants.tsx                  # Iconos adicionales
└── examples/
    └── ConfirmationExamples.tsx   # Ejemplos de uso
```

## Instalación y Configuración

### 1. Envolver la aplicación con ConfirmationProvider

```tsx
// App.tsx
import { ConfirmationProvider } from './hooks/useConfirmation';

function App() {
  return (
    <ConfirmationProvider>
      <div className="App">
        {/* Tu aplicación existente */}
      </div>
    </ConfirmationProvider>
  );
}
```

### 2. Usar en componentes

```tsx
import { useConfirmation, confirmationPresets } from '../hooks/useConfirmation';

const MissionComponent = () => {
  const { showConfirmation } = useConfirmation();

  const handleDelete = async () => {
    const confirmed = await showConfirmation(
      confirmationPresets.deleteMission("Misión Norte 2024")
    );
    
    if (confirmed) {
      // Proceder con eliminación
    }
  };
};
```

## API Reference

### useConfirmation Hook

```tsx
const { showConfirmation, hideConfirmation, isVisible } = useConfirmation();
```

#### showConfirmation(config: ConfirmationConfig): Promise<boolean>

Muestra un modal de confirmación y retorna una promesa que resuelve `true` si se confirma o `false` si se cancela.

### ConfirmationConfig Interface

```tsx
interface ConfirmationConfig {
  type: 'destructive' | 'warning' | 'info' | 'danger';
  title: string;
  message: string;
  details?: string;                 // Texto adicional en caja gris
  confirmText?: string;            // Default: "Confirmar"
  cancelText?: string;             // Default: "Cancelar"
  confirmButtonVariant?: 'danger' | 'warning' | 'primary' | 'secondary';
  showIcon?: boolean;              // Default: true
  allowBackdropClick?: boolean;    // Default: true
  onConfirm?: () => void | Promise<void>;
  onCancel?: () => void;
}
```

## Presets Predefinidos

### deleteMission(missionName: string)
```tsx
const config = confirmationPresets.deleteMission("Misión Norte 2024");
```

### deleteUser(userName: string)
```tsx
const config = confirmationPresets.deleteUser("Boris González");
```

### deleteRole(roleName: string)
```tsx
const config = confirmationPresets.deleteRole("Administrador");
```

### deleteDataFile(fileName: string)
```tsx
const config = confirmationPresets.deleteDataFile("datos_celulares.xlsx");
```

### clearCellularData(recordCount: number)
```tsx
const config = confirmationPresets.clearCellularData(1250);
```

## Ejemplos de Uso

### Reemplazo directo de window.confirm()

**ANTES:**
```tsx
if (window.confirm('¿Eliminar este archivo?')) {
  deleteFile();
}
```

**DESPUÉS:**
```tsx
const confirmed = await showConfirmation({
  type: 'warning',
  title: 'Confirmar Eliminación',
  message: '¿Eliminar este archivo?',
  confirmText: 'Eliminar',
  cancelText: 'Cancelar'
});

if (confirmed) {
  deleteFile();
}
```

### Confirmación con detalles adicionales

```tsx
const confirmed = await showConfirmation({
  type: 'destructive',
  title: 'Eliminar Misión',
  message: '¿Estás seguro de que deseas eliminar esta misión?',
  details: 'Esta acción no se puede deshacer. Todos los datos celulares y archivos asociados se perderán permanentemente.',
  confirmText: 'Sí, Eliminar',
  cancelText: 'Cancelar',
  confirmButtonVariant: 'danger'
});
```

### Confirmación con callbacks

```tsx
const confirmed = await showConfirmation({
  type: 'warning',
  title: 'Procesar Datos',
  message: '¿Deseas procesar todos los archivos seleccionados?',
  onConfirm: () => {
    console.log('Iniciando procesamiento...');
  },
  onCancel: () => {
    console.log('Procesamiento cancelado');
  }
});
```

## Personalización de Estilos

### Colores por Tipo

- **Destructive/Danger**: Rojo (`text-red-500`, `bg-red-600`)
- **Warning**: Amarillo (`text-yellow-500`, `bg-yellow-600`)
- **Info**: Azul (`text-blue-500`, `bg-blue-600`)

### Variables CSS Personalizables

El componente usa clases de Tailwind CSS que pueden personalizarse a través del tema:

```tsx
// theme.ts
export const colors = {
  'danger': '#dc2626',
  'warning': '#d97706',
  'info': '#2563eb',
  // ... otros colores
};
```

## Casos de Uso en KRONOS

1. **Eliminación de Misiones**: Confirmar antes de eliminar misiones y sus datos
2. **Gestión de Usuarios**: Confirmar eliminación/desactivación de usuarios
3. **Gestión de Roles**: Confirmar cambios de permisos críticos
4. **Procesamiento de Datos**: Confirmar operaciones que afecten datos celulares
5. **Exportación/Importación**: Confirmar operaciones de archivos grandes

## Mejores Prácticas

### ✅ Recomendado
- Usar presets cuando sea posible para consistencia
- Incluir detalles para acciones irreversibles
- Usar tipo 'destructive' para eliminaciones permanentes
- Proporcionar texto de botón descriptivo ("Eliminar Misión" vs "Aceptar")

### ❌ Evitar
- Usar para confirmaciones triviales que no requieren atención especial
- Sobrecargar con demasiado texto en el mensaje principal
- Usar tipo 'info' para acciones destructivas
- Permitir backdrop click en operaciones críticas

## Compatibilidad con Navegadores

- ✅ Chrome 90+
- ✅ Firefox 88+
- ✅ Safari 14+
- ✅ Edge 90+

## Rendimiento

- **Bundle size**: ~3KB adicionales (minificado + gzipped)
- **Memory impact**: Mínimo (componente se monta/desmonta según necesidad)
- **Animations**: Optimizadas con `transform` y `opacity` para mejor rendimiento

## Troubleshooting

### El modal no aparece
Verifica que `ConfirmationProvider` esté envolviendo tu aplicación correctamente.

### Estilos no se aplican
Asegúrate de que Tailwind CSS esté configurado correctamente y que las clases custom estén incluidas.

### TypeScript errors
Verifica que todas las interfaces estén importadas correctamente desde `types.ts`.

---

**Desarrollado para KRONOS Enterprise Application**  
*Versión: 1.0.0*