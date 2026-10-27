"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { useAdmin } from "@/lib/admin-context";
import {
  adminApi,
  AdminApiError,
  AdminUser,
  Lead,
  LeadFilters,
  LEAD_SOURCE_LABELS,
  LEAD_STATUS_LABELS,
  LEAD_STATUS_ORDER,
} from "@/lib/admin";
import { api, CatalogService } from "@/lib/api";
import { formatPhone } from "@/lib/phone";
import { useAdminData } from "@/lib/use-admin-data";

const STATUS_BADGE_CLS: Record<string, string> = {
  new: "bg-amber-50 text-amber-700",
  in_progress: "bg-sky-50 text-sky-700",
  converted: "bg-emerald-50 text-emerald-700",
  rejected: "bg-slate-200 text-slate-600",
};

function sourceBadge(source: string) {
  const label = LEAD_SOURCE_LABELS[source] || source;
  const cls =
    source === "call"
      ? "bg-emerald-50 text-emerald-700"
      : source === "quiz"
        ? "bg-sky-50 text-sky-700"
        : "bg-slate-100 text-slate-600";
  return <span className={`rounded-full px-2 py-0.5 text-xs ${cls}`}>{label}</span>;
}

// Сводная карточка сегментации (по источникам / каналам / кампаниям).
function SummaryCard({ title, items }: { title: string; items: { value: string; count: number }[] }) {
  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-4">
      <p className="text-xs font-semibold uppercase tracking-wide text-muted">{title}</p>
      <ul className="mt-2 space-y-1">
        {items.slice(0, 5).map((item) => (
          <li key={item.value} className="flex items-center justify-between gap-2 text-sm">
            <span className="truncate text-slate-700">{item.value}</span>
            <span className="shrink-0 font-semibold text-slate-900">{item.count}</span>
          </li>
        ))}
        {items.length === 0 && <li className="text-sm text-muted">Нет данных</li>}
      </ul>
    </div>
  );
}

const SOURCE_FILTER_OPTIONS = [
  { value: "", label: "Все источники" },
  { value: "quiz", label: "Квиз" },
  { value: "callback", label: "Обратный звонок" },
  { value: "call", label: "Звонок (Calltracking)" },
  { value: "booking", label: "Букинг" },
];

function formatUtm(lead: Lead): string {
  const parts: string[] = [];
  if (lead.utm?.source) parts.push(lead.utm.source);
  if (lead.utm?.campaign) parts.push(lead.utm.campaign);
  return parts.join(" / ");
}

// Модалка «Создать заказ из лида»: услуга города лида + параметры.
function ConvertModal({
  lead,
  onClose,
  onConverted,
}: {
  lead: Lead;
  onClose: () => void;
  onConverted: () => void;
}) {
  const [services, setServices] = useState<CatalogService[]>([]);
  const [serviceType, setServiceType] = useState("");
  const [rooms, setRooms] = useState(2);
  const [bathrooms, setBathrooms] = useState(1);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!lead.city_slug) return;
    api
      .getCityCatalog(lead.city_slug)
      .then((catalog) => {
        setServices(catalog.services);
        if (catalog.services.length) setServiceType(catalog.services[0].type);
      })
      .catch(() => setError("Не удалось загрузить услуги города"));
  }, [lead.city_slug]);

  const submit = async () => {
    if (!serviceType || saving) return;
    setSaving(true);
    setError(null);
    try {
      await adminApi.convertLead(lead.id, {
        service_type: serviceType,
        rooms,
        bathrooms,
      });
      onConverted();
    } catch (err) {
      setError(err instanceof AdminApiError ? err.message : "Ошибка конверсии");
      setSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/50 p-4" onMouseDown={onClose} role="presentation">
      <div
        className="w-full max-w-md rounded-2xl bg-white p-6 shadow-2xl"
        onMouseDown={(e) => e.stopPropagation()}
        role="dialog"
        aria-modal="true"
      >
        <h3 className="font-display text-xl font-semibold text-slate-900">
          Создать заказ из лида
        </h3>
        <p className="mt-1 text-sm text-muted">
          {lead.name} · {lead.phone} · {lead.city || "город не указан"}
        </p>

        <div className="mt-4 space-y-3">
          <label className="block">
            <span className="mb-1 block text-sm font-medium text-slate-700">Услуга</span>
            <select
              value={serviceType}
              onChange={(e) => setServiceType(e.target.value)}
              className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm"
            >
              {services.map((s) => (
                <option key={s.type} value={s.type}>{s.name}</option>
              ))}
            </select>
          </label>
          <div className="grid grid-cols-2 gap-3">
            <label className="block">
              <span className="mb-1 block text-sm font-medium text-slate-700">Комнаты</span>
              <input
                type="number" min={0} max={20} value={rooms}
                onChange={(e) => setRooms(Number(e.target.value))}
                className="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm"
              />
            </label>
            <label className="block">
              <span className="mb-1 block text-sm font-medium text-slate-700">Санузлы</span>
              <input
                type="number" min={0} max={10} value={bathrooms}
                onChange={(e) => setBathrooms(Number(e.target.value))}
                className="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm"
              />
            </label>
          </div>
          <p className="text-xs text-muted">
            Стоимость рассчитается по тарифам города автоматически. Доп.услуги и клинера
            назначите в карточке заказа.
          </p>
          {error && <p className="text-sm text-red-600">{error}</p>}
        </div>

        <div className="mt-5 flex justify-end gap-2">
          <button
            type="button"
            onClick={onClose}
            className="rounded-lg border border-slate-200 px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50"
          >
            Отмена
          </button>
          <button
            type="button"
            onClick={submit}
            disabled={!serviceType || saving}
            className="rounded-lg bg-slate-900 px-4 py-2 text-sm font-semibold text-white hover:bg-slate-800 disabled:bg-slate-400"
          >
            {saving ? "Создаём…" : "Создать заказ"}
          </button>
        </div>
      </div>
    </div>
  );
}

export default function LeadsPage() {
  const { city } = useAdmin();
  const [staff, setStaff] = useState<AdminUser[]>([]);
  const [sourceFilter, setSourceFilter] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [utmFilter, setUtmFilter] = useState("");
  const [editingNoteId, setEditingNoteId] = useState<string | null>(null);
  const [noteDraft, setNoteDraft] = useState("");
  const [convertLead, setConvertLead] = useState<Lead | null>(null);

  // Список лидов и сводка грузятся вместе; смена города/фильтров перезапускает запрос.
  const loadLeads = useCallback(async () => {
    const filters: LeadFilters = {};
    if (sourceFilter) filters.source = sourceFilter;
    if (statusFilter) filters.status = statusFilter;
    if (utmFilter) filters.utm_source = utmFilter;

    const [page, summary] = await Promise.all([
      adminApi.listLeads(city, filters),
      adminApi.leadsSummary(city),
    ]);
    return { page, summary };
  }, [city, sourceFilter, statusFilter, utmFilter]);
  const { data, error, loading, reload, setError, setData } = useAdminData(loadLeads);
  const leads = data?.page.items ?? [];
  const total = data?.page.total ?? 0;
  const summary = data?.summary ?? null;

  // Менеджеры/админы для селекта «Ответственный» (грузим один раз).
  useEffect(() => {
    adminApi
      .listUsers()
      .then((page) => setStaff(page.items.filter((u) => u.role === "manager" || u.role === "admin")))
      .catch(() => {
        // Селект ответственного просто останется пустым.
      });
  }, []);

  // Оптимистичное обновление строки без перезапроса списка.
  const applyLead = useCallback(
    (updated: Lead) => {
      setData((prev) =>
        prev
          ? {
              ...prev,
              page: {
                ...prev.page,
                items: prev.page.items.map((l) => (l.id === updated.id ? updated : l)),
              },
            }
          : prev,
      );
    },
    [setData],
  );

  const changeStatus = async (lead: Lead, status: string) => {
    try {
      applyLead({ ...lead, status });
      const updated = await adminApi.updateLead(lead.id, { status });
      applyLead(updated);
    } catch (err) {
      applyLead(lead);
      setError(err instanceof AdminApiError ? err.message : "Не удалось обновить статус");
    }
  };

  const changeAssignee = async (lead: Lead, assigneeId: string) => {
    try {
      const updated = await adminApi.updateLead(lead.id, {
        assignee_id: assigneeId || null,
      });
      applyLead(updated);
    } catch (err) {
      setError(err instanceof AdminApiError ? err.message : "Не удалось назначить ответственного");
    }
  };

  const saveNote = async (lead: Lead) => {
    try {
      const updated = await adminApi.updateLead(lead.id, { manager_note: noteDraft });
      applyLead(updated);
      setEditingNoteId(null);
    } catch (err) {
      setError(err instanceof AdminApiError ? err.message : "Не удалось сохранить заметку");
    }
  };

  const summaryStatusItems = useMemo(
    () =>
      summary?.by_status.map((i) => ({ ...i, value: LEAD_STATUS_LABELS[i.value] || i.value })) ?? [],
    [summary],
  );

  return (
    <div>
      <div className="mb-4 flex items-center justify-between">
        <h1 className="font-display text-2xl font-semibold text-slate-900">
          Лиды <span className="text-base font-normal text-muted">({total})</span>
        </h1>
        <button
          type="button"
          onClick={reload}
          className="rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-sm font-medium text-slate-700 hover:bg-slate-50"
        >
          Обновить
        </button>
      </div>

      <p className="mb-4 text-sm text-muted">
        Собственная CRM: заявки с сайта и звонки Calltracking с полной атрибуцией. Ведите
        воронку (Новый → В работе → Заказ создан / Отказ), назначайте ответственного,
        оставляйте заметки и создавайте заказ из лида в один клик.
      </p>

      {/* Дашборд-сегментация */}
      {summary ? (
        <div className="mb-5 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          <SummaryCard title="По воронке" items={summaryStatusItems} />
          <SummaryCard title="По источникам" items={summary.by_source.map((i) => ({ ...i, value: LEAD_SOURCE_LABELS[i.value] || i.value }))} />
          <SummaryCard title="По каналам (utm_source)" items={summary.by_utm_source} />
          <SummaryCard title="По кампаниям" items={summary.by_campaign} />
        </div>
      ) : null}

      {/* Фильтры */}
      <div className="mb-4 flex flex-wrap items-center gap-2">
        <select
          value={sourceFilter}
          onChange={(e) => setSourceFilter(e.target.value)}
          className="rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-sm text-slate-700"
        >
          {SOURCE_FILTER_OPTIONS.map((o) => (
            <option key={o.value} value={o.value}>{o.label}</option>
          ))}
        </select>
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-sm text-slate-700"
        >
          <option value="">Вся воронка</option>
          {LEAD_STATUS_ORDER.map((s) => (
            <option key={s} value={s}>{LEAD_STATUS_LABELS[s]}</option>
          ))}
        </select>
        <input
          value={utmFilter}
          onChange={(e) => setUtmFilter(e.target.value)}
          placeholder="utm_source (напр. yandexpoisk)"
          className="w-56 rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-sm text-slate-700"
        />
        {(sourceFilter || statusFilter || utmFilter) && (
          <button
            type="button"
            onClick={() => { setSourceFilter(""); setStatusFilter(""); setUtmFilter(""); }}
            className="text-sm font-medium text-slate-500 hover:text-slate-700"
          >
            Сбросить
          </button>
        )}
      </div>

      {error && (
        <div className="mb-4 rounded-xl border border-red-200 bg-red-50 px-4 py-2 text-sm text-red-700">
          {error}
        </div>
      )}

      {loading ? (
        <p className="text-muted">Загрузка…</p>
      ) : (
        <div className="overflow-x-auto rounded-2xl border border-slate-200 bg-white">
          <table className="w-full text-sm">
            <thead className="bg-slate-50 text-left text-xs uppercase text-muted">
              <tr>
                <th className="px-4 py-3">Дата</th>
                <th className="px-4 py-3">Имя / телефон</th>
                <th className="px-4 py-3">Источник</th>
                <th className="px-4 py-3">Город</th>
                <th className="px-4 py-3">Услуга / расчёт</th>
                <th className="px-4 py-3">UTM / клики</th>
                <th className="px-4 py-3">Воронка</th>
                <th className="px-4 py-3">Ответственный</th>
                <th className="px-4 py-3">Заметка</th>
                <th className="px-4 py-3">Действия</th>
              </tr>
            </thead>
            <tbody>
              {leads.map((lead) => (
                <tr key={lead.id} className="border-t border-slate-100 align-top">
                  <td className="px-4 py-3 whitespace-nowrap text-slate-600">
                    {new Date(lead.created_at).toLocaleString("ru-RU")}
                  </td>
                  <td className="px-4 py-3">
                    <span className="font-medium text-slate-900">{lead.name}</span>
                    <a href={`tel:${lead.phone}`} className="block text-brand-deep hover:underline">
                      {formatPhone(lead.phone)}
                    </a>
                    {lead.context ? (
                      <span className="mt-1 block max-w-[220px] text-xs text-muted" title={lead.context}>
                        {lead.context.length > 96 ? `${lead.context.slice(0, 96)}…` : lead.context}
                      </span>
                    ) : null}
                  </td>
                  <td className="px-4 py-3">{sourceBadge(lead.source)}</td>
                  <td className="px-4 py-3 text-slate-600">{lead.city || "—"}</td>
                  <td className="px-4 py-3 text-slate-600">
                    {lead.service_type || "—"}
                    {lead.price != null ? (
                      <span className="block whitespace-nowrap font-medium text-slate-900">
                        {lead.price.toLocaleString("ru-RU")} ₽
                      </span>
                    ) : null}
                  </td>
                  <td className="px-4 py-3 text-xs text-slate-600">
                    <div className="max-w-[160px]">
                      {formatUtm(lead) || "—"}
                      {lead.yclid ? <div className="truncate text-slate-400" title={lead.yclid}>yclid</div> : null}
                      {lead.gclid ? <div className="truncate text-slate-400" title={lead.gclid}>gclid</div> : null}
                      {lead.ym_uid ? <div className="truncate text-slate-400" title={lead.ym_uid}>ym: {lead.ym_uid.slice(0, 10)}…</div> : null}
                    </div>
                  </td>
                  <td className="px-4 py-3">
                    <select
                      value={lead.status}
                      onChange={(e) => changeStatus(lead, e.target.value)}
                      className={`rounded-full border-0 px-2 py-1 text-xs font-medium ${STATUS_BADGE_CLS[lead.status] || "bg-slate-100"}`}
                    >
                      {LEAD_STATUS_ORDER.map((s) => (
                        <option key={s} value={s}>{LEAD_STATUS_LABELS[s]}</option>
                      ))}
                    </select>
                  </td>
                  <td className="px-4 py-3">
                    <select
                      value={lead.assignee_id || ""}
                      onChange={(e) => changeAssignee(lead, e.target.value)}
                      className="max-w-[140px] rounded-lg border border-slate-200 bg-white px-2 py-1 text-xs text-slate-700"
                    >
                      <option value="">Не назначен</option>
                      {staff.map((u) => (
                        <option key={u.id} value={u.id}>{u.full_name || u.phone}</option>
                      ))}
                    </select>
                  </td>
                  <td className="px-4 py-3">
                    {editingNoteId === lead.id ? (
                      <span className="flex flex-col gap-1">
                        <textarea
                          value={noteDraft}
                          onChange={(e) => setNoteDraft(e.target.value)}
                          rows={2}
                          className="w-44 rounded-lg border border-slate-200 px-2 py-1 text-xs"
                          autoFocus
                        />
                        <span className="flex gap-1">
                          <button type="button" onClick={() => saveNote(lead)} className="rounded bg-slate-900 px-2 py-0.5 text-xs font-medium text-white">
                            Сохранить
                          </button>
                          <button type="button" onClick={() => setEditingNoteId(null)} className="rounded border border-slate-200 px-2 py-0.5 text-xs text-slate-600">
                            Отмена
                          </button>
                        </span>
                      </span>
                    ) : (
                      <button
                        type="button"
                        onClick={() => { setEditingNoteId(lead.id); setNoteDraft(lead.manager_note || ""); }}
                        className="max-w-[176px] text-left text-xs text-slate-600 hover:text-slate-900"
                        title="Изменить заметку"
                      >
                        {lead.manager_note ? lead.manager_note : <span className="text-slate-400">+ заметка</span>}
                      </button>
                    )}
                  </td>
                  <td className="px-4 py-3">
                    {lead.status !== "converted" ? (
                      <button
                        type="button"
                        onClick={() => setConvertLead(lead)}
                        disabled={!lead.city_slug}
                        title={lead.city_slug ? "Создать заказ из лида" : "У лида не указан город"}
                        className="whitespace-nowrap rounded-lg bg-slate-900 px-3 py-1.5 text-xs font-semibold text-white hover:bg-slate-800 disabled:bg-slate-300"
                      >
                        Создать заказ
                      </button>
                    ) : (
                      <span className="text-xs font-medium text-emerald-700">→ в «Заказах»</span>
                    )}
                  </td>
                </tr>
              ))}
              {leads.length === 0 && (
                <tr>
                  <td colSpan={10} className="px-4 py-6 text-center text-muted">
                    Заявок по выбранным фильтрам нет
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      )}

      {convertLead ? (
        <ConvertModal
          lead={convertLead}
          onClose={() => setConvertLead(null)}
          onConverted={() => {
            setConvertLead(null);
            reload();
          }}
        />
      ) : null}
    </div>
  );
}
