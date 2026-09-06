/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        navy: {
          DEFAULT: '#1A2B4A',
          50: '#E8EDF5',
          100: '#C5D1E6',
          200: '#9DB3D2',
          300: '#7595BE',
          400: '#4D78AA',
          500: '#1A2B4A',
          600: '#162440',
          700: '#121D34',
          800: '#0E1629',
          900: '#0A0F1D',
        },
        amber: {
          DEFAULT: '#F28A1E',
          50: '#FEF3E2',
          100: '#FDE0B6',
          200: '#FBCD89',
          300: '#F9BA5C',
          400: '#F7A72F',
          500: '#F28A1E',
          600: '#D4770F',
          700: '#A85E0B',
          800: '#7C4508',
          900: '#502C05',
        },
        green: {
          DEFAULT: '#0EA570',
          50: '#E1F5EE',
          500: '#0EA570',
          600: '#0B8A5E',
        },
      },
      fontFamily: {
        heading: ['Nunito', 'sans-serif'],
        body: ['DM Sans', 'sans-serif'],
      },
      fontWeight: {
        '700': '700',
      },
    },
  },
  plugins: [],
}
