# Почтовый сервис PointClean — настройка (mail.blanq.tech)

Стек: **docker-mailserver** (SMTP/IMAP) + **Roundcube** (веб-почта).
Файлы: `deploy/docker-compose.mail.yml`, `deploy/mail/mailserver.env`.

> ⚠️ **Два внешних предусловия, которые нельзя закрыть из кода:**
> 1. **DNS** для `blanq.tech` должен указывать на сервер `81.31.247.79`.
> 2. **Исходящий порт 25** на этом сервере **заблокирован** провайдером
>    (проверено: `PORT25_BLOCKED`). Без его разблокировки или SMTP-релея
>    почта сможет только приниматься, но не отправляться.
>    Решение: запросить разблокировку 25 у хостера **или** прописать `RELAY_HOST`
>    в `deploy/mail/mailserver.env` (Яндекс 360, SendGrid, Mailgun и т.п.).

---

## 1. DNS-записи (добавить у регистратора blanq.tech)

| Тип   | Имя                 | Значение                                   | Назначение            |
|-------|---------------------|--------------------------------------------|-----------------------|
| A     | `mail`              | `81.31.247.79`                            | хост почтового сервера|
| MX    | `@` (blanq.tech) | `10 mail.blanq.tech.`                   | приём почты           |
| TXT   | `@`                 | `v=spf1 mx ~all`                           | SPF                   |
| TXT   | `_dmarc`            | `v=DMARC1; p=quarantine; rua=mailto:postmaster@blanq.tech` | DMARC |
| TXT   | `mail._domainkey`   | (значение DKIM, генерируется на шаге 4)     | DKIM                  |
| PTR   | (rDNS для IP)       | `mail.blanq.tech`                        | обратная зона — у хостера |

> PTR/rDNS настраивается **в панели хостинга** (не у DNS-регистратора).

---

## 2. SSL-сертификат для mail
После того как `mail.blanq.tech` резолвится на сервер:
```bash
sudo certbot --nginx -d mail.blanq.tech
```
(docker-mailserver берёт его из смонтированного `/etc/letsencrypt`).

---

## 3. Запуск стека
```bash
cd /opt/clean-dot
docker compose -f deploy/docker-compose.mail.yml --env-file deploy/.env up -d
```

## 4. Создание ящиков и DKIM
```bash
# Аккаунт (пароль задаётся интерактивно/аргументом)
docker exec -it pc_mailserver setup email add postmaster@blanq.tech 'СильныйПароль'
docker exec -it pc_mailserver setup email add info@blanq.tech 'СильныйПароль'
docker exec -it pc_mailserver setup email add support@blanq.tech 'СильныйПароль'
docker exec -it pc_mailserver setup email add b2b@blanq.tech 'СильныйПароль'
docker exec -it pc_mailserver setup email add ow@blanq.tech 'СильныйПароль'

# Генерация DKIM-ключа -> вывести значение для TXT-записи mail._domainkey
docker exec -it pc_mailserver setup config dkim
cat deploy/mail/config/opendkim/keys/blanq.tech/mail.txt
```
Значение из `mail.txt` внести в DNS (TXT `mail._domainkey`).

## 5. Проверка
- Веб-почта: `https://mail.blanq.tech` (Roundcube), вход по созданному ящику.
- Диагностика доставляемости: https://www.mail-tester.com, https://mxtoolbox.com.

---

## Связь с приложением
Чтобы бэкенд слал письма (уведомления о заявках и т.п.) через этот сервер,
в `deploy/.env` можно добавить SMTP-параметры и реализовать отправку
(в текущем MVP уведомления клиенту идут по SMS/в CRM; email — опциональное расширение).

