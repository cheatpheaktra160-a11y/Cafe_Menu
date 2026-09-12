import type { Config } from 'tailwindcss';

const config: Config = {
  content: ['./app/**/*.{js,ts,jsx,tsx}', './components/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        coffee: {
          50: '#fef8f3',
          100: '#f9eee0',
          200: '#f1d8c2',
          300: '#e4b89a',
          400: '#c2835d',
          500: '#a56d3a',
          600: '#8b5024',
          700: '#6b3a1c',
          800: '#4b2b16',
          900: '#311b10'
        }
      }
    }
  },
  plugins: []
};

export default config;
