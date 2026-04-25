/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./frontend/templates/**/*.html",
    "./frontend/static/js/**/*.js",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        primary: {
          50:  '#eff6ff',
          100: '#dbeafe',
          200: '#bfdbfe',
          300: '#93c5fd',
          400: '#60a5fa',
          500: '#3b82f6',
          600: '#2563eb',
          700: '#1d4ed8',
          800: '#1e40af',
          900: '#1e3a8a',
        },
        surface: {
          DEFAULT: '#1e2130',
          50:  '#f8fafc',
          100: '#f1f5f9',
          200: '#e2e8f0',
          700: '#2d3748',
          800: '#1e2130',
          900: '#131720',
        },
      },
      // F-19: Font 'Inter' chỉ hiển thị nếu MÁY của cán bộ CÀI SẴN.
      // KHÔNG @import từ Google Fonts / CDN ở input.css -> không có
      // network call ra ngoài khi vận hành offline. Khi máy không có
      // Inter, trình duyệt fallback ngay sang ui-sans-serif/system-ui
      // (font hệ thống) -> giao diện vẫn hiển thị bình thường.
      // Nếu tương lai cần đồng bộ giao diện 100% giữa các máy, hãy:
      //   1) Tải Inter .woff2 về frontend/static/fonts/
      //   2) Khai báo @font-face trong input.css với src local
      //   3) Build lại Tailwind
      fontFamily: {
        sans: ['Inter', 'ui-sans-serif', 'system-ui', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
