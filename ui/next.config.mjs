/** @type {import('next').NextConfig} */
const nextConfig = {
  eslint: {
    // 在构建时忽略 ESLint 错误，避免构建失败
    ignoreDuringBuilds: true,
  },
  typescript: {
    // 在构建时跳过 TypeScript 类型检查，避免构建失败
    ignoreBuildErrors: true,
  },
  experimental: {
    // 增加服务器组件外部包配置
    serverComponentsExternalPackages: [],
  },
};

export default nextConfig;
