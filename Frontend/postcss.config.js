export default {
  plugins: {
    // Tailwind CSS v3 - plugin estable y compatible
    tailwindcss: {},
    // Autoprefixer - añade prefijos de navegador automáticamente
    autoprefixer: {
      // Configuración específica para aplicaciones de escritorio
      overrideBrowserslist: [
        'Chrome >= 70',
        'Firefox >= 60',
        'Safari >= 12',
        'Edge >= 79',
      ],
      // Soporte para aplicaciones Eel (Chromium embebido)
      flexbox: 'no-2009',
      grid: 'autoplace',
    },
  },
}