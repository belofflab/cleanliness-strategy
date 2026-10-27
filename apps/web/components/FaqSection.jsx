"use client";

import { useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { ChevronDown } from "lucide-react";
import { FAQ_ITEMS } from "@/lib/faq";

const FAQ = FAQ_ITEMS;

export default function FaqSection() {
  const [activeIndex, setActiveIndex] = useState(0);

  return (
    <section id="faq" className="px-4 py-16 sm:px-6 lg:px-10">
      <div className="mx-auto w-full max-w-6xl rounded-[2rem] border border-white/40 bg-surface p-6 shadow-xl shadow-slate-900/5 backdrop-blur-xl md:p-10">
        <h2 className="font-display text-2xl font-semibold tracking-tight text-slate-900 sm:text-3xl">
          Частые вопросы
        </h2>
        <div className="mt-6 space-y-3">
          {FAQ.map((item, index) => {
            const isOpen = activeIndex === index;

            return (
              <article key={item.question} className="rounded-2xl border border-slate-200 bg-white">
                <button
                  type="button"
                  onClick={() => setActiveIndex(isOpen ? -1 : index)}
                  className="flex w-full items-center justify-between gap-3 px-4 py-4 text-left"
                  aria-expanded={isOpen}
                >
                  <span className="text-sm font-semibold text-slate-900 sm:text-base">{item.question}</span>
                  <ChevronDown
                    size={18}
                    className={`shrink-0 text-slate-500 transition ${isOpen ? "rotate-180" : ""}`}
                  />
                </button>
                <AnimatePresence initial={false}>
                  {isOpen ? (
                    <motion.div
                      initial={{ height: 0, opacity: 0 }}
                      animate={{ height: "auto", opacity: 1 }}
                      exit={{ height: 0, opacity: 0 }}
                      transition={{ duration: 0.2 }}
                      className="overflow-hidden"
                    >
                      <p className="px-4 pb-4 text-sm leading-relaxed text-muted">{item.answer}</p>
                    </motion.div>
                  ) : null}
                </AnimatePresence>
              </article>
            );
          })}
        </div>
      </div>
    </section>
  );
}

