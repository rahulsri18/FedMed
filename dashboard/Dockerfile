# Stage 1: Build React App with Vite
FROM node:20-alpine AS build

# Owner: M5 (Dashboard Lead)
WORKDIR /app

COPY dashboard/package*.json ./
RUN npm ci

COPY dashboard/ ./
RUN npm run build

# Stage 2: Serve with lightweight Nginx
FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
