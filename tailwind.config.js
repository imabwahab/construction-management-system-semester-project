/** @type {import('tailwindcss').Config} */
module.exports = {
  // Scan every app's templates for class names.
  content: [
    "./templates/**/*.html",
    "./*/templates/**/*.html",
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          DEFAULT: "#1d4ed8",
          dark: "#1e3a8a",
        },
      },
    },
  },
  plugins: [],
};
