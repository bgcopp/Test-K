import path from 'path';
import { defineConfig, loadEnv } from 'vite';

export default defineConfig(({ mode }) => {
    const env = loadEnv(mode, '.', '');
    const isProduction = mode === 'production';
    
    return {
      define: {
        'process.env.API_KEY': JSON.stringify(env.GEMINI_API_KEY),
        'process.env.GEMINI_API_KEY': JSON.stringify(env.GEMINI_API_KEY)
      },
      resolve: {
        alias: {
          '@': path.resolve(__dirname, '.'),
        }
      },
      base: './',  // Rutas relativas para compatibilidad con Eel
      build: {
        outDir: 'dist',
        emptyOutDir: true,
        sourcemap: false,
        minify: isProduction,
        target: ['es2015', 'chrome58'], // Compatibilidad con navegadores integrados
        rollupOptions: {
          output: {
            manualChunks: {
              // Separar vendor chunks para mejor caching
              vendor: ['react', 'react-dom', 'react-router-dom']
            },
            // Asegurar nombres consistentes para archivos
            entryFileNames: 'assets/[name].[hash].js',
            chunkFileNames: 'assets/[name].[hash].js',
            assetFileNames: 'assets/[name].[hash].[ext]'
          }
        },
        // Optimización para aplicación de escritorio
        chunkSizeWarningLimit: 1000
      },
      server: {
        port: 5173,
        host: 'localhost',
        strictPort: true
      },
      preview: {
        port: 4173,
        host: 'localhost'
      }
    };
});