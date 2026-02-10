/** @type {import('tailwindcss').Config} */
/**
 * Tailwind CSS v3 Configuration
 *
 * This file defines the Tailwind CSS configuration including:
 * - Content paths (where to scan for class names)
 * - Custom Unitree color scheme
 * - Theme extensions
 */
module.exports = {
  content: [
    "./templates/**/*.html",
    "./static/**/*.js",
  ],
  theme: {
    extend: {
      colors: {
        'unitree-primary': '#00E8DA',
        'unitree-secondary': '#00B8AD',
        'unitree-dark': '#1e1e1e',
        'unitree-dark-lighter': '#2d2d2d',
        'unitree-success': '#10b981',
        'unitree-warning': '#f59e0b',
        'unitree-danger': '#ef4444',
        'unitree-info': '#3b82f6',
      }
    }
  },
  plugins: [],
}

