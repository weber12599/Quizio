# ==========================================
# Base Stage
# ==========================================
FROM node:20-slim AS base
WORKDIR /app
COPY package*.json ./
RUN npm install

# ==========================================
# Development Stage
# ==========================================
FROM base AS dev
EXPOSE 5174
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]

# ==========================================
# Builder Stage
# ==========================================
FROM base AS builder
COPY . .
RUN npm run build

# ==========================================
# Production Stage
# ==========================================
FROM nginx:alpine AS prod
COPY --from=builder /app/dist /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]