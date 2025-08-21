import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

// Configuración optimizada para KRONOS con React Flow
export default defineConfig({
  plugins: [react()],
  
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  
  // Optimización crítica para React Flow y evitar error 'V'
  optimizeDeps: {
    include: [
      '@xyflow/react',
      'html-to-image',
      'react',
      'react-dom',
      'react-router-dom'
    ],
    force: true, // Fuerza re-bundling para resolver errores de inicialización
    esbuildOptions: {
      // Mejora compatibilidad con módulos ES
      target: 'es2020'
    }
  },
  
  // Configuración de build optimizada
  build: {
    target: 'es2020',
    rollupOptions: {
      output: {
        // Separación manual de chunks para mejor performance
        manualChunks: {
          'vendor': ['react', 'react-dom', 'react-router-dom'],
          'flow-libs': ['@xyflow/react', 'html-to-image']
        }
      }
    },
    // Mejora performance de build
    sourcemap: false,
    minify: 'esbuild',
    chunkSizeWarningLimit: 1000
  },
  
  // Configuración del servidor de desarrollo
  server: {
    port: 5173,
    host: true,
    open: false,
    cors: true
  },
  
  // Compatibilidad con Eel
  base: './',
  
  // Mejora compatibilidad con módulos
  esbuild: {
    jsxFactory: 'React.createElement',
    jsxFragment: 'React.Fragment',
    target: 'es2020'
  }
})