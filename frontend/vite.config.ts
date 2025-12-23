import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  base: "./",
  build: {
    outDir: process.env.VITE_OUT_DIR || "dist",
    sourcemap: false,
    emptyOutDir: true,
    minify: "esbuild",
    rollupOptions: {
      output: {
        entryFileNames: "js/[name].js",
        chunkFileNames: "js/[name].js",
        assetFileNames: ({ name }) => {
          if (/\.css$/.test(String(name))) {
            return "css/[name][extname]";
          }
          if (/\.(woff2?|eot|ttf|otf)$/.test(name ?? "")) {
            return "fonts/[name][extname]";
          }
          if (/\.(png|jpe?g|gif|svg)$/.test(name ?? "")) {
            return "img/[name][extname]";
          }
          return "js/[name][extname]";
        },
        manualChunks: {
          'react-vendor': ['react', 'react-dom'],
          'markdown-vendor': ['react-markdown', 'remark-gfm', 'remark-breaks', 'rehype-raw'],
          'syntax-highlighter': ['react-syntax-highlighter'],
          'primereact-vendor': ['primereact/dialog', 'primereact/accordion'],
        },
      },
    },
  },
  server: {
    proxy: {
      "/ai": {
        target: "http://127.0.0.1:8080",
        changeOrigin: true,
      },
    },
  },
});
