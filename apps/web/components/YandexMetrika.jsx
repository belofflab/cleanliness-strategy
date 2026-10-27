'use client';

import { useEffect } from 'react';
import { usePathname, useSearchParams } from 'next/navigation';
import Script from 'next/script';

export default function YandexMetrika() {
    const pathname = usePathname();
    const searchParams = useSearchParams();

    useEffect(() => {
        // При изменении маршрута отправляем хит в Метрику
        if (typeof window !== 'undefined' && typeof window.ym !== 'undefined') {
            const url = `${pathname}${searchParams.toString() ? `?${searchParams.toString()}` : ''}`;
            window.ym(109824753, 'hit', url);
        }
    }, [pathname, searchParams]);

    return (
        <>
            <Script id="yandex-metrika" strategy="afterInteractive">
                {`
          (function(m,e,t,r,i,k,a){m[i]=m[i]||function(){(m[i].a=m[i].a||[]).push(arguments)};
          m[i].l=1*new Date();
          for (var j = 0; j < document.scripts.length; j++) {if (document.scripts[j].src === r) { return; }}
          k=e.createElement(t),a=e.getElementsByTagName(t)[0],k.async=1,k.src=r,a.parentNode.insertBefore(k,a)})
          (window, document, "script", "https://mc.yandex.ru/metrika/tag.js?id=109824753", "ym");

          ym(109824753, "init", {
            ssr: true,
            webvisor: true,
            clickmap: true,
            ecommerce: "dataLayer",
            accurateTrackBounce: true,
            trackLinks: true
          });
        `}
            </Script>
            <noscript>
                <div>
                    {/* eslint-disable-next-line @next/next/no-img-element -- пиксель Метрики в <noscript>: next/image неприменим */}
                    <img
                        src="https://mc.yandex.ru/watch/109824753"
                        style={{ position: 'absolute', left: '-9999px' }}
                        alt=""
                    />
                </div>
            </noscript>
        </>
    );
}