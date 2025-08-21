import path from 'path';
import { defineConfig, loadEnv } from 'vite';
import { resolve } from 'path';

export default defineConfig(({ mode }) => {
    const env = loadEnv(mode, '.', '');
    const isProduction = mode === 'production';
    
    return {
      // Configuración CSS y PostCSS profesional
      css: {
        postcss: {
          plugins: [
            // Tailwind y Autoprefixer se cargan automáticamente desde postcss.config.js
          ],
        },
        // Optimizaciones para desarrollo y producción
        devSourcemap: !isProduction,
        preprocessorOptions: {
          css: {
            additionalData: `/* Archivo generado automáticamente por Tailwind CSS */`
          }
        }
      },
      define: {
        'process.env.API_KEY': JSON.stringify(env.GEMINI_API_KEY),
        'process.env.GEMINI_API_KEY': JSON.stringify(env.GEMINI_API_KEY)
      },
      resolve: {
        alias: {
          '@': path.resolve(__dirname, '.'),
          // Alias para facilitar imports
          '@styles': resolve(__dirname, 'src'),
          '@components': resolve(__dirname, 'components'),
          '@pages': resolve(__dirname, 'pages'),
          '@utils': resolve(__dirname, 'utils'),
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
          // Configuración especial para archivos externos como eel.js
          external: ['/eel.js'],
          output: {
            manualChunks: {
              // Separar vendor chunks para mejor caching
              vendor: ['react', 'react-dom', 'react-router-dom'],
              // Separar Tailwind CSS en su propio chunk si es grande
              ...(isProduction && {
                tailwind: ['src/index.css']
              })
            },
            // Asegurar nombres consistentes para archivos
            entryFileNames: 'assets/[name].[hash].js',
            chunkFileNames: 'assets/[name].[hash].js',
            assetFileNames: (assetInfo) => {
              // Nombrar archivos CSS de manera consistente
              if (assetInfo.name?.endsWith('.css')) {
                return 'assets/[name].[hash][extname]';
              }
              return 'assets/[name].[hash].[ext]';
            }
          }
        },
        // Optimización para aplicación de escritorio con Tailwind
        chunkSizeWarningLimit: 1000,
        // Configuraciones específicas para CSS
        cssCodeSplit: isProduction, // Solo dividir CSS en producción
        cssMinify: isProduction ? 'esbuild' : false,
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