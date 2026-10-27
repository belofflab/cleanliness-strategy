# Образ frontend для монорепо (build context = корень репозитория).
# Использует output: "standalone" + outputFileTracingRoot (см. apps/web/next.config.ts).

# --- Этап 1: зависимости (workspaces) ---
FROM node:22-alpine AS deps
ARG ALPINE_MIRROR=https://mirror.yandex.ru/mirrors/alpine
ARG NPM_REGISTRY=https://registry.npmjs.org/
WORKDIR /repo
RUN sed -i "s|https://dl-cdn.alpinelinux.org/alpine|${ALPINE_MIRROR}|g" /etc/apk/repositories \
    && npm config set registry "${NPM_REGISTRY}"
COPY package.json package-lock.json ./
COPY apps/web/package.json ./apps/web/package.json
RUN npm ci

# --- Этап 2: сборка ---
FROM node:22-alpine AS builder
ARG ALPINE_MIRROR=https://mirror.yandex.ru/mirrors/alpine
ARG NPM_REGISTRY=https://registry.npmjs.org/
WORKDIR /repo
RUN sed -i "s|https://dl-cdn.alpinelinux.org/alpine|${ALPINE_MIRROR}|g" /etc/apk/repositories \
    && npm config set registry "${NPM_REGISTRY}"
COPY --from=deps /repo/node_modules ./node_modules
COPY package.json package-lock.json ./
COPY apps/web ./apps/web
# NEXT_PUBLIC_* инлайнятся в браузерный бандл на этапе сборки — передаём как build args.
ARG NEXT_PUBLIC_API_URL
ARG NEXT_PUBLIC_SITE_URL
ARG NEXT_PUBLIC_CALLTRACKING_SCRIPT_URL
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL
ENV NEXT_PUBLIC_SITE_URL=$NEXT_PUBLIC_SITE_URL
ENV NEXT_PUBLIC_CALLTRACKING_SCRIPT_URL=$NEXT_PUBLIC_CALLTRACKING_SCRIPT_URL
RUN npm run build --workspace apps/web

# --- Этап 3: минимальный runtime ---
FROM node:22-alpine AS runner
WORKDIR /repo
ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1
RUN addgroup --system --gid 1001 nodejs && adduser --system --uid 1001 nextjs

# standalone-вывод монорепо: корень со server.js в apps/web и общий node_modules.
COPY --from=builder --chown=nextjs:nodejs /repo/apps/web/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /repo/apps/web/.next/static ./apps/web/.next/static
COPY --from=builder --chown=nextjs:nodejs /repo/apps/web/public ./apps/web/public

USER nextjs
EXPOSE 3000
ENV PORT=3000
ENV HOSTNAME=0.0.0.0

CMD ["node", "apps/web/server.js"]
