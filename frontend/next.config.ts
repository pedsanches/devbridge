import type { NextConfig } from "next";
import bundleAnalyzer from "@next/bundle-analyzer";

const withBundleAnalyzer = bundleAnalyzer({
    enabled: process.env.ANALYZE === "true",
});

const nextConfig: NextConfig = {
    // Enable React strict mode for better development experience
    reactStrictMode: true,

    // Experimental features
    experimental: {
        // Enable typed routes
        typedRoutes: true,
        // Enable filesystem caching for faster builds (Next.js 16)
        turbopackFileSystemCacheForDev: true,
        turbopackFileSystemCacheForBuild: true,
    },

    // Image optimization
    images: {
        remotePatterns: [
            {
                protocol: "https",
                hostname: "avatars.githubusercontent.com",
            },
        ],
        // Modern formats for better LCP
        formats: ["image/avif", "image/webp"],
    },

    // Redirects
    async redirects() {
        return [];
    },

    // Headers
    async headers() {
        return [
            {
                source: "/:path*",
                headers: [
                    {
                        key: "X-Frame-Options",
                        value: "DENY",
                    },
                    {
                        key: "X-Content-Type-Options",
                        value: "nosniff",
                    },
                    {
                        key: "Referrer-Policy",
                        value: "strict-origin-when-cross-origin",
                    },
                ],
            },
        ];
    },
};

export default withBundleAnalyzer(nextConfig);
