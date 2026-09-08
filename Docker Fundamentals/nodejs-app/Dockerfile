# Alpine base: ~5x smaller than the Debian-based node:20 tag.
# The tag is pinned to a major version so a new Node release cannot
# silently change the build.
FROM node:20-alpine

WORKDIR /usr/src/app

# No third-party packages are needed; the built-in http module is enough,
# so there is no npm install layer and nothing to cache.
COPY package.json app.js ./

# app.js reads process.env.PORT, so this is the single place the port is set.
ENV PORT=3000

# EXPOSE is documentation for whoever runs the image - it does not publish
# the port. That still needs `docker run -p 3000:3000`.
EXPOSE 3000

# The official node images ship an unprivileged `node` user. Dropping root
# here means a compromised process cannot write to the image filesystem.
USER node

# Exec form (JSON array): node becomes PID 1 and receives SIGTERM directly,
# so `docker stop` shuts the server down instead of waiting 10s for the kill.
CMD ["node", "app.js"]
