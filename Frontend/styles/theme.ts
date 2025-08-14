// styles/theme.ts

/**
 * Defines the application's core color palette.
 * These colors are used by Tailwind CSS to generate utility classes.
 */
export const colors = {
  'primary': '#4f46e5',
  'primary-hover': '#4338ca',
  'secondary': '#1f2937',
  'secondary-light': '#374151',
  'light': '#f3f4f6',
  'medium': '#9ca3af',
  'dark': '#111827',
};

/**
 * The configuration object for Tailwind CSS.
 * It extends the default theme with our custom color palette.
 */
export const tailwindConfig = {
  theme: {
    extend: {
      colors: colors,
    },
  },
};
