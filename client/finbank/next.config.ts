import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  /* config options here */
  outputFileTracingRoot: __dirname,
    allowedDevOrigins: ['192.168.0.113'],
};

export default nextConfig;
