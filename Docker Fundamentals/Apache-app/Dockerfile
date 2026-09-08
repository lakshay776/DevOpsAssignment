# httpd 2.4 with its default configuration; nothing is overridden here.
FROM httpd:2.4

# httpd serves files from htdocs by default, so dropping a file in is the
# whole "build". No config file, no CMD - the base image already has both.
COPY index.html /usr/local/apache2/htdocs/index.html

# Port 80 is privileged, so this image keeps the base image's root user.
EXPOSE 80
