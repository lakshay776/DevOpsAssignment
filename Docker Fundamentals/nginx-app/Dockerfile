# nginx on Alpine: the smallest of the six Hello World images in this folder.
FROM nginx:alpine

# The default server block roots at /usr/share/nginx/html, so replacing
# index.html is enough - no nginx.conf change needed.
COPY index.html /usr/share/nginx/html/index.html

# The base image's CMD already runs nginx in the foreground ("daemon off"),
# which is what a container needs; overriding it would break `docker stop`.
EXPOSE 80
