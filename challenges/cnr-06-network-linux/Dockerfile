# CNR-06 disposable Linux service (SSH on 2222). Flag is NOT in any layer or env: it is written at start from a Docker secret.
FROM alpine:3.20
ARG SSH_PASSWORD
RUN test -n "$SSH_PASSWORD" && apk add --no-cache openssh-server \
 && addgroup -g 3001 labaudit \
 && adduser -D -s /bin/sh tmendis && addgroup tmendis labaudit \
 && echo "tmendis:${SSH_PASSWORD}" | chpasswd \
 && ssh-keygen -A \
 && mkdir -p /var/empty /srv/campus-archive \
 && printf 'Archive exports are handled by the labaudit group (see /srv/campus-archive).\nSome export files are hidden.\n' > /home/tmendis/NOTES.txt \
 && chown tmendis:tmendis /home/tmendis/NOTES.txt
COPY sshd_config /etc/ssh/sshd_config
COPY entrypoint.sh /entrypoint.sh
RUN chmod 755 /entrypoint.sh
EXPOSE 2222
ENTRYPOINT ["/entrypoint.sh"]
