/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'http://backend:8000/:path*',
      },
      {
        source: '/static/:path*',
        destination: 'http://backend:8000/static/:path*',
      },
    ];
  },
};

module.exports = nextConfig;
