"use client";

// Загрузка данных страниц админ-CRM.
//
// Ограничение React (правило react-hooks/set-state-in-effect): внутри эффекта
// нельзя синхронно вызывать setState — в том числе через функцию вроде
// `load()`, которая выставляет loading/error перед запросом. Поэтому здесь
// состояние меняется только в колбэках промиса, а «идёт загрузка» выводится
// из того, относится ли последняя завершённая попытка к текущему запросу
// (пара loader + tick).

import { useCallback, useEffect, useState, type Dispatch, type SetStateAction } from "react";
import { AdminApiError } from "@/lib/admin";

type Loader<T> = () => Promise<T>;

// Завершённая попытка загрузки для конкретной пары (loader, tick).
interface Attempt<T> {
  loader: Loader<T>;
  tick: number;
  error: string | null;
}

// Ошибка действия (мутации) поверх загруженных данных; привязана к паре
// (loader, tick), чтобы автоматически скрываться при следующей загрузке.
interface ActionError<T> {
  loader: Loader<T>;
  tick: number;
  message: string;
}

export interface AdminData<T> {
  /** Последние успешно загруженные данные; сохраняются на время перезагрузки. */
  data: T | null;
  /** Ошибка загрузки или действия; null, пока идёт загрузка. */
  error: string | null;
  loading: boolean;
  /** Перезапросить данные (после мутации или по кнопке «Обновить»). */
  reload: () => void;
  /** Показать/сбросить ошибку действия (create/update/delete). */
  setError: (message: string | null) => void;
  /** Оптимистичное обновление данных без перезапроса. */
  setData: Dispatch<SetStateAction<T | null>>;
}

/**
 * `loader` должен быть стабильным (useCallback): смена его идентичности —
 * сигнал «параметры изменились (город, фильтры), загрузи заново».
 */
export function useAdminData<T>(
  loader: Loader<T>,
  fallbackError = "Ошибка загрузки",
): AdminData<T> {
  const [tick, setTick] = useState(0);
  const [data, setData] = useState<T | null>(null);
  const [attempt, setAttempt] = useState<Attempt<T> | null>(null);
  const [action, setAction] = useState<ActionError<T> | null>(null);

  useEffect(() => {
    let cancelled = false;
    loader().then(
      (result) => {
        if (cancelled) return;
        setData(result);
        setAttempt({ loader, tick, error: null });
      },
      (err: unknown) => {
        if (cancelled) return;
        setAttempt({
          loader,
          tick,
          error: err instanceof AdminApiError ? err.message : fallbackError,
        });
      },
    );
    return () => {
      cancelled = true;
    };
  }, [loader, tick, fallbackError]);

  // Попытка/ошибка от другой пары (loader, tick) устарели: актуальные данные
  // ещё загружаются.
  const current = attempt && attempt.loader === loader && attempt.tick === tick ? attempt : null;
  const currentAction = action && action.loader === loader && action.tick === tick ? action : null;

  const reload = useCallback(() => setTick((t) => t + 1), []);
  const setError = useCallback(
    (message: string | null) => {
      setAction(message === null ? null : { loader, tick, message });
    },
    [loader, tick],
  );

  return {
    data,
    error: currentAction ? currentAction.message : current ? current.error : null,
    loading: current === null,
    reload,
    setError,
    setData,
  };
}
