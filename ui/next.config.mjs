/** @type {import('next').NextConfig} */
const nextConfig = {
  eslint: {
    // 在构建时忽略 ESLint 错误，避免构建失败
    ignoreDuringBuilds: true,
  },
  typescript: {
    // 在构建时忽略 TypeScript 错误（如果还有的话）
    ignoreBuildErrors: false,
  },
};

export default nextConfig;
