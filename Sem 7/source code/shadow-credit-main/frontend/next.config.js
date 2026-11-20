/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  pageExtensions: ['jsx', 'js', 'tsx', 'ts'],
  images: {
    domains: ['localhost'],
  },
}
module.exports = nextConfig
