import Link from "next/link";

export type LegalFact = {
  label: string;
  value: string;
  note?: string;
};

export type LegalSection = {
  title: string;
  paragraphs: string[];
  bullets?: string[];
};

type LegalPageProps = {
  eyebrow: string;
  title: string;
  summary: string;
  updatedAt: string;
  facts: LegalFact[];
  sections: LegalSection[];
  note?: string;
};

export default function LegalPage({
  eyebrow,
  title,
  summary,
  updatedAt,
  facts,
  sections,
  note,
}: LegalPageProps) {
  return (
    <div className="min-h-screen bg-background text-foreground">
      <div className="px-4 py-8 sm:px-6 lg:px-10 lg:py-12">
        <article className="mx-auto max-w-5xl space-y-6">
          <Link href="/" className="inline-flex items-center gap-2 text-sm font-semibold text-brand-deep transition hover:text-brand">
            <span aria-hidden="true">←</span>
            На главную
          </Link>

          <header className="rounded-4xl border border-white/50 bg-surface p-6 shadow-xl shadow-slate-900/5 backdrop-blur-xl sm:p-8 lg:p-10">
            <p className="inline-flex rounded-full bg-white px-3 py-1 text-xs font-semibold uppercase tracking-[0.18em] text-brand-deep">
              {eyebrow}
            </p>
            <h1 className="mt-4 max-w-3xl font-display text-3xl font-semibold tracking-tight text-slate-950 sm:text-4xl">
              {title}
            </h1>
            <p className="mt-4 max-w-3xl text-base leading-relaxed text-muted sm:text-lg">
              {summary}
            </p>

            <div className="mt-6 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
              {facts.map((fact) => (
                <div key={fact.label} className="rounded-2xl border border-slate-200 bg-white p-4">
                  <p className="text-xs font-semibold uppercase tracking-[0.12em] text-slate-500">{fact.label}</p>
                  <p className="mt-2 text-sm font-semibold text-slate-900">{fact.value}</p>
                  {fact.note ? <p className="mt-1 text-xs leading-relaxed text-muted">{fact.note}</p> : null}
                </div>
              ))}
            </div>

            <p className="mt-6 text-xs text-muted">Актуальная версия: {updatedAt}</p>
          </header>

          <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_18rem]">
            <div className="space-y-4">
              {sections.map((section) => (
                <section key={section.title} className="rounded-[1.75rem] border border-white/50 bg-surface p-6 shadow-lg shadow-slate-900/5 backdrop-blur-xl sm:p-7">
                  <h2 className="font-display text-xl font-semibold tracking-tight text-slate-950 sm:text-2xl">
                    {section.title}
                  </h2>
                  <div className="mt-4 space-y-3 text-sm leading-7 text-slate-700 sm:text-base">
                    {section.paragraphs.map((paragraph, index) => (
                      <p key={`${section.title}-${index}`}>{paragraph}</p>
                    ))}
                  </div>
                  {section.bullets?.length ? (
                    <ul className="mt-4 grid gap-2 text-sm leading-6 text-slate-700 sm:text-base">
                      {section.bullets.map((bullet) => (
                        <li key={bullet} className="flex gap-3 rounded-2xl border border-slate-200 bg-white p-4">
                          <span className="mt-1 h-2 w-2 shrink-0 rounded-full bg-brand" aria-hidden="true" />
                          <span>{bullet}</span>
                        </li>
                      ))}
                    </ul>
                  ) : null}
                </section>
              ))}
            </div>

            <aside className="space-y-4 lg:sticky lg:top-6 lg:self-start">
              <div className="rounded-[1.75rem] border border-slate-200 bg-white p-5 shadow-lg shadow-slate-900/5">
                <p className="text-xs font-semibold uppercase tracking-[0.14em] text-slate-500">Что важно</p>
                <ul className="mt-4 space-y-3 text-sm leading-6 text-slate-700">
                  <li>• Цена на сайте — ориентир, итог подтверждаем до старта.</li>
                  <li>• Передача заявки через сайт означает согласие с документами.</li>
                  <li>• Cookie и аналитика включаются только после согласия пользователя.</li>
                </ul>
              </div>

              {note ? (
                <div className="rounded-[1.75rem] border border-sky-200 bg-sky-50 p-5 text-sm leading-6 text-sky-950 shadow-lg shadow-sky-900/5">
                  {note}
                </div>
              ) : null}
            </aside>
          </div>
        </article>
      </div>
    </div>
  );
}

