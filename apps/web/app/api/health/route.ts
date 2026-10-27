import { NextResponse } from "next/server";

// Health-эндпоинт Node.js-сервера фронтенда (для Uptime Kuma / оркестратора).
// Лёгкая проверка живости процесса — без обращений к БД/бэкенду.
// force-dynamic: ответ не кэшируется, всегда свежий timestamp.
export const dynamic = "force-dynamic";

export async function GET() {
  return NextResponse.json(
    {
      status: "ok",
      service: "web",
      timestamp: new Date().toISOString(),
    },
    { status: 200 },
  );
}
