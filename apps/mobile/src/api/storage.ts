// Безопасное хранилище токенов на основе expo-secure-store (Keychain/Keystore).
//
// Если Keychain недоступен (например, неподписанная сборка в симуляторе или
// сбой системного хранилища), токены живут в памяти процесса до перезапуска:
// приложение не зависает на старте и вход остаётся возможным.
import * as SecureStore from "expo-secure-store";

const ACCESS_KEY = "tochka.access_token";
const REFRESH_KEY = "tochka.refresh_token";

const memory = new Map<string, string>();
let secureStoreUnavailable = false;

function markUnavailable(error: unknown) {
  if (secureStoreUnavailable) return;
  secureStoreUnavailable = true;
  console.warn("SecureStore недоступен — токены хранятся в памяти до перезапуска приложения", error);
}

async function read(key: string): Promise<string | null> {
  if (!secureStoreUnavailable) {
    try {
      return await SecureStore.getItemAsync(key);
    } catch (error) {
      markUnavailable(error);
    }
  }
  return memory.get(key) ?? null;
}

async function write(key: string, value: string): Promise<void> {
  if (!secureStoreUnavailable) {
    try {
      await SecureStore.setItemAsync(key, value);
      return;
    } catch (error) {
      markUnavailable(error);
    }
  }
  memory.set(key, value);
}

async function remove(key: string): Promise<void> {
  memory.delete(key);
  if (secureStoreUnavailable) return;
  try {
    await SecureStore.deleteItemAsync(key);
  } catch (error) {
    markUnavailable(error);
  }
}

export const tokenStorage = {
  getAccess() {
    return read(ACCESS_KEY);
  },
  getRefresh() {
    return read(REFRESH_KEY);
  },
  async save(access: string, refresh: string) {
    await write(ACCESS_KEY, access);
    await write(REFRESH_KEY, refresh);
  },
  async clear() {
    await remove(ACCESS_KEY);
    await remove(REFRESH_KEY);
  },
};
