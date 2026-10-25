import { defineConfig } from 'vite';
import vue from '@vitejs/plugin-vue';
export default defineConfig({ plugins: [vue()], cacheDir: '../.tmp/frontend/vite-cache', build: { outDir: '../.tmp/frontend/dist', emptyOutDir: true }, server: { proxy: { '/api': { target: 'https://localhost:7242', changeOrigin: true, secure: false }, '/_evaluation': { target: 'https://localhost:7242', changeOrigin: true, secure: false } } } });
