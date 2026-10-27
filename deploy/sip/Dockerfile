# Легковесный SIP-сервер для приёма звонков Calltracking.ru.
# Alpine + Asterisk из штатного репозитория (~30 МБ поверх базового слоя).
# Собирается на сервере: docker compose -f deploy/docker-compose.sip.yml build
FROM alpine:3.20

RUN apk add --no-cache asterisk \
    && mkdir -p /var/run/asterisk /var/log/asterisk /var/spool/asterisk \
    && chown -R asterisk:asterisk /var/run/asterisk /var/log/asterisk /var/spool/asterisk /etc/asterisk

USER asterisk

# -f — форграунд (журналы в stdout контейнера), -p — без смены приоритета.
CMD ["asterisk", "-f", "-p"]
