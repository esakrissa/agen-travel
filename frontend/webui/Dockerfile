# Frontend WebUI Dockerfile
FROM node:20-alpine

WORKDIR /app

# Install pnpm globally
RUN npm install -g pnpm

# Copy package files
COPY package.json pnpm-lock.yaml* ./

# Install dependencies
RUN pnpm install

# Copy source code
COPY . .

# Expose port 3000
EXPOSE 3000

# Start the application in development mode (simple and proven working)
CMD ["pnpm", "dev"]
