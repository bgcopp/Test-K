/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
    "./components/**/*.{js,ts,jsx,tsx}",
    "./pages/**/*.{js,ts,jsx,tsx}",
    "./utils/**/*.{js,ts,jsx,tsx}",
    "./hooks/**/*.{js,ts,jsx,tsx}",
    "./examples/**/*.{js,ts,jsx,tsx}",
    "./types/**/*.{js,ts,jsx,tsx}",
    "./styles/**/*.{js,ts,jsx,tsx}",
  ],
  // Configuración de purge para optimización en v3
  safelist: [
    // Preservar clases dinámicas críticas del sistema KRONOS
    'bg-primary',
    'bg-primary-hover', 
    'bg-secondary',
    'bg-secondary-light',
    'bg-light',
    'bg-medium',
    'bg-dark',
    'text-primary',
    'text-secondary',
    'text-light', 
    'text-medium',
    'text-dark',
    'border-primary',
    'border-secondary',
    // Animaciones personalizadas
    'animate-fadeIn',
    'animate-slideIn', 
    'animate-shimmer',
    'animate-pulse-slow',
    'animate-rotate-slow',
    'animate-bounce-delayed',
    'animate-progress-glow',
    // Estados interactivos con patrones
    {
      pattern: /(bg|text|border)-(primary|secondary|light|medium|dark)/,
      variants: ['hover', 'focus', 'active', 'disabled'],
    },
    // Clases de React Flow específicas
    'react-flow__node',
    'react-flow__edge', 
    'react-flow__handle',
    'react-flow__background',
    'react-flow__controls',
    'react-flow__minimap',
  ],
  theme: {
    extend: {
      // Colores exactos preservados del CDN original
      colors: {
        'primary': '#4f46e5',
        'primary-hover': '#4338ca',
        'secondary': '#1f2937',
        'secondary-light': '#374151',
        'light': '#f3f4f6',
        'medium': '#9ca3af',
        'dark': '#111827',
      },
      // Optimizaciones adicionales para el proyecto KRONOS
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
      transitionDuration: {
        '400': '400ms',
        '600': '600ms',
      },
      zIndex: {
        '100': '100',
        '200': '200',
        '300': '300',
      },
      // Configuraciones específicas para React Flow
      screens: {
        'xs': '475px',
      },
      spacing: {
        '18': '4.5rem',
        '88': '22rem',
      },
      // Configuraciones para el sistema de diagramas
      backdropBlur: {
        'xs': '2px',
      },
      animation: {
        'fade-in': 'fadeIn 0.5s ease-in-out',
        'slide-up': 'slideUp 0.3s ease-out',
        'pulse-slow': 'pulse 3s infinite',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { transform: 'translateY(10px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
      },
    },
  },
  plugins: [],
  // Configuración específica para aplicación de escritorio Eel
  important: false,
  separator: ':',
  // Optimizaciones para producción
  corePlugins: {
    preflight: true,
  },
}