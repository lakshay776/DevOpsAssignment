# The JDK is needed at build time for javac. A real service would use a
# multi-stage build and ship the smaller -jre image - see
# ../../DockerFiles and Images/Dockerfile for that pattern.
FROM eclipse-temurin:21-jdk

WORKDIR /opt/app

# Compiling during the build means the image ships Main.class, so container
# start-up is a plain `java Main` with no compile step.
COPY Main.java .
RUN javac Main.java

EXPOSE 8080

# Main.java hardcodes port 8080, which is unprivileged, so run as nobody.
# The class file is world-readable, so it stays readable after the switch.
USER nobody

CMD ["java", "Main"]
