FROM node:22-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build
FROM nginx:1.27-alpine
# Base image lags behind Alpine security fixes; pull them in so the Trivy gate passes.
RUN apk upgrade --no-cache
COPY --from=build /app/dist /usr/share/nginx/html
# The nginx image renders templates/*.template into conf.d at startup, filling in BACKEND_URL.
COPY templates /etc/nginx/templates
ENV BACKEND_URL=http://backend:8000
EXPOSE 80
