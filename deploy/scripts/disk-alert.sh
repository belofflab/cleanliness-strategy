#!/usr/bin/env bash
# Алерт на заполнение диска прод-сервера «Точка Чистоты».
#
# Контекст: 2026-09-01 лог pc_sip (24 ГБ) заполнил диск на 100%, PostgreSQL
# ушёл в PANIC — сайт и админка отдавали 500, мониторинг молчал. Этот скрипт
# закрывает дыру: предупреждает на 80%, пока всё ещё работает.
#
# Установка (cron, каждые 15 минут):
#   install -m 755 deploy/scripts/disk-alert.sh /opt/clean-comp/deploy/scripts/disk-alert.sh
#   printf 'MAILTO=""\n*/15 * * * * root /opt/clean-comp/deploy/scripts/disk-alert.sh >>/var/log/pointclean-disk-alert.log 2>&1\n' \
#     > /etc/cron.d/pointclean-disk-alert
#
# Каналы:
#   • письмо на ALERT_EMAIL через локальный docker-mailserver (pc_mailserver);
#   • Telegram — автоматически, если в deploy/.env заданы TELEGRAM_BOT_TOKEN
#     и TELEGRAM_CHAT_ID (те же ключи, что для пингов о лидах).
#
# Антиспам: повторный алерт не чаще раза в REALERT_HOURS, при возврате ниже
# порога (с гистерезисом 3 п.п.) — одно письмо «диск в норме».

set -uo pipefail
PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin

WARN_PCT=${WARN_PCT:-80}
CRIT_PCT=${CRIT_PCT:-90}
REALERT_HOURS=${REALERT_HOURS:-6}
ALERT_EMAIL=${ALERT_EMAIL:-ow@blanq.tech}
MAIL_FROM=${MAIL_FROM:-alerts@blanq.tech}
MAIL_CONTAINER=${MAIL_CONTAINER:-pc_mailserver}
ENV_FILE=${ENV_FILE:-/opt/clean-comp/deploy/.env}
STATE_DIR=/var/lib/pointclean
STATE_FILE=$STATE_DIR/disk-alert.state

mkdir -p "$STATE_DIR"
exec 9>"$STATE_DIR/disk-alert.lock"
flock -n 9 || exit 0

usage_pct=$(df --output=pcent / 2>/dev/null | tail -1 | tr -dc '0-9')
if [ -z "$usage_pct" ]; then
  echo "$(date -u '+%F %T') ERROR: df не вернул процент занятости" >&2
  exit 1
fi

level=OK
[ "$usage_pct" -ge "$WARN_PCT" ] && level=WARN
[ "$usage_pct" -ge "$CRIT_PCT" ] && level=CRIT

prev_level=OK
prev_ts=0
if [ -f "$STATE_FILE" ]; then
  read -r prev_level prev_ts <"$STATE_FILE" || true
fi
now=$(date -u +%s)

build_report() {
  echo "Диск прод-сервера (msk-1-vm-0007, cleanliness.pro): занято ${usage_pct}% — уровень ${level}."
  echo
  echo "--- df -h / ---"
  df -h /
  echo
  echo "--- Топ-5 docker-логов контейнеров ---"
  du -sm /var/lib/docker/containers/*/ 2>/dev/null | sort -rn | head -5 | while read -r size dir; do
    cid=$(basename "$dir")
    name=$(docker inspect --format '{{.Name}}' "$cid" 2>/dev/null | tr -d '/')
    printf '%6s МБ  %s\n' "$size" "${name:-$cid}"
  done
  echo
  echo "--- docker system df ---"
  timeout 30 docker system df 2>/dev/null || echo "(docker system df не ответил за 30с)"
  echo
  echo "Памятка: инцидент 2026-09-01 — лог pc_sip 24 ГБ уронил PostgreSQL."
  echo "Быстрая чистка: docker builder prune -af; docker image prune -af;"
  echo "битые логи: truncate -s 0 /var/lib/docker/containers/<id>/<id>-json.log"
}

send_mail() { # $1 subject; stdin body
  local subject=$1
  { printf 'Subject: %s\nFrom: %s\nTo: %s\nContent-Type: text/plain; charset=utf-8\n\n' \
      "$subject" "$MAIL_FROM" "$ALERT_EMAIL"; cat; } |
    docker exec -i "$MAIL_CONTAINER" sendmail -f "$MAIL_FROM" "$ALERT_EMAIL" 2>/dev/null ||
    echo "$(date -u '+%F %T') WARN: не удалось отправить письмо (mailserver недоступен?)" >&2
}

send_telegram() { # stdin text
  local token chat_id text
  [ -f "$ENV_FILE" ] || return 0
  token=$(sed -n 's/^TELEGRAM_BOT_TOKEN=//p' "$ENV_FILE" | tr -d '"' | head -1)
  chat_id=$(sed -n 's/^TELEGRAM_CHAT_ID=//p' "$ENV_FILE" | tr -d '"' | head -1)
  [ -n "$token" ] && [ -n "$chat_id" ] || return 0
  text=$(cat)
  curl -m 10 -s -o /dev/null \
    --data-urlencode "chat_id=${chat_id}" \
    --data-urlencode "text=${text}" \
    "https://api.telegram.org/bot${token}/sendMessage" || true
}

if [ "$level" != "OK" ]; then
  realert_after=$((REALERT_HOURS * 3600))
  if [ "$level" != "$prev_level" ] || [ $((now - prev_ts)) -ge "$realert_after" ]; then
    subject="[cleanliness.pro] ДИСК ${usage_pct}% — ${level}"
    report=$(build_report)
    printf '%s\n' "$report" | send_mail "$subject"
    printf '⚠️ %s\nЗанято %s%% диска. Подробности в письме на %s\n' "$subject" "$usage_pct" "$ALERT_EMAIL" | send_telegram
    echo "$(date -u '+%F %T') ALERT sent: ${level} ${usage_pct}%"
    printf '%s %s\n' "$level" "$now" >"$STATE_FILE"
  else
    printf '%s %s\n' "$level" "$prev_ts" >"$STATE_FILE"
  fi
else
  # Возврат в норму — с гистерезисом, чтобы не дребезжать на границе порога:
  # в «серой зоне» (WARN-3..WARN) состояние алерта сохраняется без писем.
  if [ "$prev_level" != "OK" ]; then
    if [ "$usage_pct" -le $((WARN_PCT - 3)) ]; then
      subject="[cleanliness.pro] Диск в норме (${usage_pct}%)"
      build_report | send_mail "$subject"
      printf '✅ %s\n' "$subject" | send_telegram
      echo "$(date -u '+%F %T') RECOVERY sent: ${usage_pct}%"
      printf 'OK %s\n' "$now" >"$STATE_FILE"
    else
      printf '%s %s\n' "$prev_level" "$prev_ts" >"$STATE_FILE"
    fi
  else
    printf 'OK %s\n' "$now" >"$STATE_FILE"
  fi
fi
