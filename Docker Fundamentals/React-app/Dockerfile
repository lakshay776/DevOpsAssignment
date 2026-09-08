# Stage 1: install dependencies and produce the static bundle.
# Everything here - node, npm, the whole node_modules tree - is thrown away
# once the build finishes.
FROM node:20-alpine AS builder
WORKDIR /app

# package.json alone first, so the npm install layer is cached and only
# re-runs when dependencies change rather than on every source edit.
COPY package.json ./
RUN npm install

# Source files come after the install for the same caching reason.
COPY index.html vite.config.js ./
COPY src ./src
RUN npm run build

# Stage 2: ship only the built files on a tiny web server.
# React is a build-time tool - the browser gets plain HTML, CSS and JS, so
# the runtime image needs no Node at all.
FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
EXPOSE 80
