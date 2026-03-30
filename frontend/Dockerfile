# Build stage
FROM node:20-alpine AS builder

WORKDIR /app

# Build argument for API URL
ARG API_BASE_URL=http://localhost:8000
ENV API_BASE_URL=$API_BASE_URL

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy source code
COPY . .

# Build the application
RUN npm run build

# Production stage
FROM node:20-alpine

WORKDIR /app

# Copy built output
COPY --from=builder /app/.output /app/.output

# Set environment variables
ENV NODE_ENV=production
ENV HOST=0.0.0.0
ENV PORT=3000

EXPOSE 3000

# Start the application
CMD ["node", ".output/server/index.mjs"]
