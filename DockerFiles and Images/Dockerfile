# Multi-stage build: the Go toolchain is ~365 MB, the shipped image is ~7 MB.

# Stage 1: compile. Named "compile" so stage 2 can copy from it by name
# instead of by index. The toolchain lives only in this stage.
FROM golang:1.23-alpine AS compile
WORKDIR /src
COPY main.go .
# CGO_ENABLED=0 forces a fully static binary - without it the build links
# against libc, which does not exist in the scratch image below.
# -ldflags="-s -w" strips the symbol table and DWARF debug info.
RUN go mod init hello-multistage >/dev/null 2>&1 \
 && CGO_ENABLED=0 GOOS=linux go build -ldflags="-s -w" -o /out/hello .

# Stage 2: run. scratch is the empty image - no shell, no package manager,
# no libc. Only the static binary is copied over, so the attack surface is
# the binary itself and nothing else.
FROM scratch
COPY --from=compile /out/hello /hello
EXPOSE 8080
# 65534 is nobody. scratch has no /etc/passwd, so the UID must be numeric -
# a name would fail at container start with "unable to find user".
USER 65534
# ENTRYPOINT, not CMD: there is no shell in scratch, so the exec form is the
# only thing that can run at all.
ENTRYPOINT ["/hello"]
