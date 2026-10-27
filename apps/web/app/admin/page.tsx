"use client";

import { useCallback } from "react";
import { useAdmin } from "@/lib/admin-context";
import {
  adminApi,
  AdminApiError,
  Master,
  Order,
  OrderBoard,
  ORDER_STATUSES,
  STATUS_LABELS,
} from "@/lib/admin";
import { useAdminData } from "@/lib/use-admin-data";

function formatPrice(value: number) {
  return new Intl.NumberFormat("ru-RU").format(value) + " ₽";
}

function OrderCard({
  order,
  masters,
  onStatus,
  onAssign,
}: {
  order: Order;
  masters: Master[];
  onStatus: (id: string, status: string) => void;
  onAssign: (id: string, masterId: string | null) => void;
}) {
  return (
    <article className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
      <div className="flex items-start justify-between gap-2">
        <div>
          <p className="font-semibold text-slate-900">{order.customer_name || "—"}</p>
          <p className="text-xs text-muted">{order.customer_phone}</p>
        </div>
        <span className="text-sm font-semibold text-slate-900">
          {formatPrice(order.total_price)}
        </span>
      </div>

      <p className="mt-2 text-sm text-slate-700">
        {order.service || order.service_type} · {order.rooms} комн. · {order.bathrooms} с/у
      </p>
      {order.city && <p className="text-xs text-muted">{order.city}</p>}
      {order.scheduled_at && (
        <p className="mt-1 text-xs text-muted">
          🗓 {new Date(order.scheduled_at).toLocaleString("ru-RU")}
        </p>
      )}

      <div className="mt-3 space-y-2 border-t border-slate-100 pt-3">
        <label className="block text-xs font-medium text-muted">
          Статус
          <select
            value={order.status}
            onChange={(e) => onStatus(order.id, e.target.value)}
            className="mt-1 w-full rounded-lg border border-slate-200 bg-white px-2 py-1.5 text-sm text-slate-900 outline-none focus:border-brand"
          >
            {ORDER_STATUSES.map((s) => (
              <option key={s} value={s}>
                {STATUS_LABELS[s]}
              </option>
            ))}
          </select>
        </label>

        <label className="block text-xs font-medium text-muted">
          Клинер
          <select
            value={order.master_id || ""}
            onChange={(e) => onAssign(order.id, e.target.value || null)}
            className="mt-1 w-full rounded-lg border border-slate-200 bg-white px-2 py-1.5 text-sm text-slate-900 outline-none focus:border-brand"
          >
            <option value="">— не назначен</option>
            {masters.map((m) => (
              <option key={m.id} value={m.id}>
                {m.full_name}
              </option>
            ))}
          </select>
        </label>
      </div>
    </article>
  );
}

export default function OrdersBoardPage() {
  const { city } = useAdmin();

  // Канбан и список клинеров грузятся вместе; смена города перезапускает загрузку.
  const loadBoard = useCallback(async () => {
    const [board, masters] = await Promise.all([
      adminApi.ordersBoard(city),
      adminApi.listMasters(city).catch(() => [] as Master[]),
    ]);
    return { board, masters: masters.filter((m) => m.is_active) };
  }, [city]);
  const { data, error, loading, reload, setError } = useAdminData(loadBoard);
  const board: OrderBoard = data?.board ?? {};
  const masters = data?.masters ?? [];

  const handleStatus = async (id: string, status: string) => {
    try {
      await adminApi.setOrderStatus(id, status);
      reload();
    } catch (err) {
      setError(err instanceof AdminApiError ? err.message : "Не удалось сменить статус");
    }
  };

  const handleAssign = async (id: string, masterId: string | null) => {
    try {
      await adminApi.assignMaster(id, masterId);
      reload();
    } catch (err) {
      setError(err instanceof AdminApiError ? err.message : "Не удалось назначить клинера");
    }
  };

  return (
    <div>
      <div className="mb-4 flex items-center justify-between">
        <h1 className="font-display text-2xl font-semibold text-slate-900">Заказы</h1>
        <button
          type="button"
          onClick={reload}
          className="rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-sm font-medium text-slate-700 hover:bg-slate-50"
        >
          Обновить
        </button>
      </div>

      {error && (
        <div className="mb-4 rounded-xl border border-red-200 bg-red-50 px-4 py-2 text-sm text-red-700">
          {error}
        </div>
      )}

      {loading ? (
        <p className="text-muted">Загрузка…</p>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-5">
          {ORDER_STATUSES.map((status) => {
            const orders = board[status] || [];
            return (
              <section key={status} className="rounded-2xl bg-slate-100/60 p-3">
                <h2 className="mb-3 flex items-center justify-between text-sm font-semibold text-slate-700">
                  {STATUS_LABELS[status]}
                  <span className="rounded-full bg-white px-2 py-0.5 text-xs text-muted">
                    {orders.length}
                  </span>
                </h2>
                <div className="space-y-3">
                  {orders.map((order) => (
                    <OrderCard
                      key={order.id}
                      order={order}
                      masters={masters}
                      onStatus={handleStatus}
                      onAssign={handleAssign}
                    />
                  ))}
                  {orders.length === 0 && (
                    <p className="px-1 text-xs text-muted">Пусто</p>
                  )}
                </div>
              </section>
            );
          })}
        </div>
      )}
    </div>
  );
}
