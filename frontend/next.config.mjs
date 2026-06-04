/** @type {import('next').NextConfig} */
const nextConfig = {
  output: "standalone",
  reactStrictMode: true,
  // The @ricky0123/vad-web package ships its own worker + WASM. We tell
  // webpack to leave them alone so it can fetch them at runtime via the
  // package's bundled paths.
  webpack: (config) => {
    config.resolve.fallback = { ...config.resolve.fallback, fs: false };
    return config;
  },
  // Allow the VAD package to be loaded even when bundled by Next.
  transpilePackages: ["@ricky0123/vad-web"],
};

export default nextConfig;
