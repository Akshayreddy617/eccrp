/** @type {import('next').NextConfig} */
const nextConfig = {
  output: "standalone",
  experimental: { typedRoutes: false },
  images: { remotePatterns: [] },
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api"}/:path*`,
      },
    ];
  },
};

module.exports = nextConfig;
