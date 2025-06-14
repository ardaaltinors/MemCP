import { defineConfig } from "astro/config";
import react from "@astrojs/react";
import CompressionPlugin from "vite-plugin-compression";
import sitemap from "@astrojs/sitemap";
import svgr from "vite-plugin-svgr";

// Use environment variables for production-ready configuration
export const siteUrl = process.env.FRONTEND_URL || "http://localhost:4321";
const backendUrl = process.env.BACKEND_URL || "http://localhost:8000";
const mcpUrl = process.env.MCP_URL || "http://localhost:4200";

const date = new Date().toISOString();
// https://astro.build/config
export default defineConfig({
    site: siteUrl + "/",

    integrations: [
        react(),
        svgr(),
        sitemap({
            serialize(item) {
                // Default values for pages
                item.priority = siteUrl + "/" === item.url ? 1.0 : 0.9;
                item.changefreq = "weekly";
                item.lastmod = date;

                // if you want to exclude a page from the sitemap, do it here
                // if (/exclude-from-sitemap/.test(item.url)) {
                //     return undefined;
                // }

                // if any page needs a different priority, changefreq, or lastmod, uncomment the following lines and adjust as needed
                // if (/test-sitemap/.test(item.url)) {
                //     item.changefreq = "daily";
                //     item.lastmod = date;
                //     item.priority = 0.9;
                // }

                // if you want to change priority of all subpages like "/posts/*", you can use:
                // if (/\/posts\//.test(item.url)) {
                //     item.priority = 0.7;
                // }
                return item;
            },
        }),
    ],
    renderers: ["@astrojs/renderer-react"],
    prerender: true,
    vite: {
        plugins: [CompressionPlugin(), svgr()],
        server: {
            proxy: {
                '/api': {
                    target: backendUrl,
                    changeOrigin: true,
                    rewrite: (path) => path.replace(/^\/api/, '')
                },
                '/mcp': {
                    target: mcpUrl,
                    changeOrigin: true
                }
            }
        },
        // Define environment variables for the client-side
        define: {
            'import.meta.env.PUBLIC_BACKEND_URL': JSON.stringify(backendUrl),
            'import.meta.env.PUBLIC_FRONTEND_URL': JSON.stringify(siteUrl),
        }
    },
    buildOptions: {
        minify: true,
    },
});
