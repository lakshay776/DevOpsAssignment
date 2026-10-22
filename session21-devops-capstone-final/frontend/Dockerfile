# Stage 1: build the static bundle.
FROM node:22-alpine AS builder

WORKDIR /app
COPY package.json package-lock.json* ./
# `npm ci` when a lockfile is present for a reproducible install, falling
# back to `npm install` when it is not.
RUN if [ -f package-lock.json ]; then npm ci; else npm install; fi

COPY . .
RUN npm run build


# Stage 2: serve it. Nothing from the build toolchain carries over.
FROM nginx:1.27-alpine AS runtime

# The base image ships with known CVEs in its OS packages; this clears them.
RUN apk upgrade --no-cache

COPY --from=builder /app/dist /usr/share/nginx/html
# Templates in this directory are rendered by the entrypoint with envsubst,
# which is how BACKEND_URL gets injected at container start rather than
# baked into the image.
COPY templates/default.conf.template /etc/nginx/templates/default.conf.template

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
