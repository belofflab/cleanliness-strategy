#!/usr/bin/env node
// Запуск Metro для тестирования на физических телефонах через Expo Go.
//
// Главная проблема при тестировании на устройстве — адрес backend API:
// `localhost` на телефоне указывает на сам телефон. Скрипт сам определяет
// IP машины в локальной сети, подставляет его в EXPO_PUBLIC_API_URL и
// запускает `expo start --go` в нужном режиме.
//
//   node scripts/dev.mjs                  # LAN: телефон и компьютер в одной Wi-Fi-сети
//   node scripts/dev.mjs --tunnel         # Metro через туннель Expo (разные сети / гостевой Wi-Fi)
//   node scripts/dev.mjs --api-tunnel     # + публичный HTTPS-туннель до локального API
//   node scripts/dev.mjs --api https://api.cleanliness.pro/api/v1   # явный адрес API
//   node scripts/dev.mjs --tunnel -- --port 8082                    # аргументы после `--` уходят в expo
//
// Переменные окружения: HOST_IP (переопределить IP), API_PORT (порт API, по умолчанию 8000),
// EXPO_PUBLIC_API_URL (если задана в shell — имеет приоритет над автоопределением).
// Значения из .env НЕ перекрывают то, что выставил скрипт (dotenv не трогает существующие env).

import { spawn, spawnSync } from "node:child_process";
import os from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";

const MOBILE_ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const API_PORT = Number(process.env.API_PORT || 8000);

// ---------- аргументы ----------
const argv = process.argv.slice(2);
const passthroughIndex = argv.indexOf("--");
const own = passthroughIndex === -1 ? argv : argv.slice(0, passthroughIndex);
const expoExtra = passthroughIndex === -1 ? [] : argv.slice(passthroughIndex + 1);

const flags = { tunnel: false, apiTunnel: false, api: null, help: false };
for (let i = 0; i < own.length; i += 1) {
  const arg = own[i];
  if (arg === "--tunnel") flags.tunnel = true;
  else if (arg === "--lan") flags.tunnel = false;
  else if (arg === "--api-tunnel") flags.apiTunnel = true;
  else if (arg === "--api") flags.api = own[++i];
  else if (arg.startsWith("--api=")) flags.api = arg.slice("--api=".length);
  else if (arg === "-h" || arg === "--help") flags.help = true;
  else {
    console.error(`Неизвестный аргумент: ${arg}`);
    flags.help = true;
  }
}

if (flags.help) {
  console.log(`Использование: node scripts/dev.mjs [--tunnel|--lan] [--api <url>] [--api-tunnel] [-- <аргументы expo start>]`);
  process.exit(flags.help && own.length ? 1 : 0);
}

// ---------- IP машины в локальной сети ----------
function detectLanIp() {
  if (process.env.HOST_IP) return process.env.HOST_IP;
  const skip = /^(docker|br-|veth|vbox|vmnet|utun|tun|tap|zt|tailscale)/i;
  const candidates = [];
  for (const [name, addresses] of Object.entries(os.networkInterfaces())) {
    if (skip.test(name)) continue;
    for (const address of addresses || []) {
      if (address.family !== "IPv4" || address.internal) continue;
      if (address.address.startsWith("169.254.")) continue; // link-local
      candidates.push({ name, address: address.address });
    }
  }
  // Предпочитаем «обычные» интерфейсы: en0/en1 (macOS Wi-Fi), wlan*/eth* (Linux).
  const preferred = candidates.find((c) => /^(en0|en1|wlan0|eth0|Wi-Fi|Ethernet)$/i.test(c.name));
  return (preferred ?? candidates[0])?.address ?? null;
}

// ---------- туннель до API (cloudflared или ngrok) ----------
function which(cmd) {
  const probe = process.platform === "win32" ? "where" : "which";
  const result = spawnSync(probe, [cmd], { encoding: "utf8" });
  return result.status === 0 ? result.stdout.trim().split("\n")[0] : null;
}

function startApiTunnel(port) {
  return new Promise((resolve, reject) => {
    let child;
    let pattern;
    if (which("cloudflared")) {
      // Quick tunnel без аккаунта: URL печатается в stderr.
      child = spawn("cloudflared", ["tunnel", "--url", `http://localhost:${port}`], { stdio: ["ignore", "pipe", "pipe"] });
      pattern = /https:\/\/[a-z0-9-]+\.trycloudflare\.com/;
    } else if (which("ngrok")) {
      // Нужен бесплатный аккаунт и `ngrok config add-authtoken …` (один раз).
      child = spawn("ngrok", ["http", String(port), "--log=stdout", "--log-format=json"], { stdio: ["ignore", "pipe", "pipe"] });
      pattern = /"url":"(https:\/\/[^"]+)"/;
    } else {
      reject(new Error("Для --api-tunnel нужен cloudflared (brew install cloudflared) или ngrok (brew install ngrok)."));
      return;
    }

    const timer = setTimeout(() => {
      child.kill();
      reject(new Error("Туннель до API не поднялся за 30 секунд"));
    }, 30_000);

    const onData = (chunk) => {
      const match = String(chunk).match(pattern);
      if (!match) return;
      clearTimeout(timer);
      const url = match[1] ?? match[0];
      resolve({ url, child });
    };
    child.stdout.on("data", onData);
    child.stderr.on("data", onData);
    child.on("exit", (code) => {
      clearTimeout(timer);
      reject(new Error(`Процесс туннеля завершился (код ${code})`));
    });
  });
}

// ---------- проверка доступности API ----------
async function apiReachable(baseUrl) {
  try {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), 3000);
    const response = await fetch(`${baseUrl}/health`, { signal: controller.signal });
    clearTimeout(timer);
    return response.ok;
  } catch {
    return false;
  }
}

// ---------- запуск ----------
const lanIp = detectLanIp();
let tunnelChild = null;
let apiUrl = flags.api || process.env.EXPO_PUBLIC_API_URL || null;

if (!apiUrl && flags.apiTunnel) {
  process.stdout.write("Поднимаю туннель до локального API… ");
  const tunnel = await startApiTunnel(API_PORT);
  tunnelChild = tunnel.child;
  apiUrl = `${tunnel.url}/api/v1`;
  console.log(tunnel.url);
} else if (!apiUrl) {
  if (!lanIp) {
    console.error("Не удалось определить IP машины в сети. Укажите HOST_IP=… или --api <url>.");
    process.exit(1);
  }
  apiUrl = `http://${lanIp}:${API_PORT}/api/v1`;
}

const reachable = await apiReachable(apiUrl);

console.log("");
console.log("┌─ Точка Чистоты · mobile dev ─────────────────────────────────────");
console.log(`│ Metro:     ${flags.tunnel ? "туннель Expo (--tunnel)" : `локальная сеть (${lanIp ?? "IP не определён"})`}`);
console.log(`│ API:       ${apiUrl}  ${reachable ? "✓ отвечает" : "✗ недоступен"}`);
console.log(`│ Город:     ${process.env.EXPO_PUBLIC_DEFAULT_CITY || "ufa (по умолчанию)"}`);
if (!reachable) {
  console.log("│");
  console.log("│ API не отвечает по этому адресу. Backend должен слушать 0.0.0.0, а не localhost:");
  console.log("│   make up                   (Docker, порт 8000 уже опубликован наружу)");
  console.log("│   make api-dev-lan          (uvicorn --host 0.0.0.0 без Docker)");
  console.log("│ Телефон и компьютер должны быть в одной Wi-Fi-сети (или используйте --api-tunnel).");
}
console.log("│");
console.log("│ Дальше: откройте Expo Go на телефоне и отсканируйте QR-код ниже.");
console.log("│ Гайд: docs/FREE_TESTING_GUIDE.md");
console.log("└──────────────────────────────────────────────────────────────────");
console.log("");

const expoArgs = ["expo", "start", "--go", flags.tunnel ? "--tunnel" : "--lan", ...expoExtra];
const metro = spawn("npx", expoArgs, {
  cwd: MOBILE_ROOT,
  stdio: "inherit",
  env: {
    ...process.env,
    EXPO_PUBLIC_API_URL: apiUrl,
    EXPO_PUBLIC_DEFAULT_CITY: process.env.EXPO_PUBLIC_DEFAULT_CITY || "ufa",
  },
});

function shutdown(code) {
  if (tunnelChild) tunnelChild.kill();
  process.exit(code ?? 0);
}
metro.on("exit", shutdown);
process.on("SIGINT", () => shutdown(0));
process.on("SIGTERM", () => shutdown(0));
