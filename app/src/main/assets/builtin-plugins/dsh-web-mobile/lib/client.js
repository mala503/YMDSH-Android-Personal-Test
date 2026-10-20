/* YMDSH 0.2.1 mobile view: zero third-party runtime imports and no polling. */
(() => {
  'use strict';
  const loader = window.__ModuleLoader__;
  if (!loader || typeof loader.load !== 'function') return;

  const CSS = `
    @media screen and (max-width: 768px) {
      html, body, #root { width: 100%; max-width: 100%; overflow-x: clip; }
      main, [role="main"], article, section { min-width: 0; }
      [role="dialog"], [data-radix-dialog-content] {
        box-sizing: border-box;
        max-width: calc(100vw - 24px) !important;
        max-height: calc(100dvh - 32px) !important;
        overflow-y: auto;
        overscroll-behavior: contain;
      }
      [role="menu"], [role="listbox"] { max-width: calc(100vw - 20px); }
      textarea, input[type="text"], input[type="search"], input[type="password"] {
        font-size: max(16px, 1em);
      }
      pre, code, table { max-width: 100%; overflow-x: auto; }
      img, video, canvas, svg { max-width: 100%; }
      button, [role="button"], a { touch-action: manipulation; }
      :focus-visible { outline-offset: 2px; }
    }
    @media (prefers-reduced-motion: reduce) {
      [data-ymdsh-mobile] * { scroll-behavior: auto !important; }
    }
  `;

  loader.load({
    id: 'dsh-web-mobile',
    factory: () => ({
      name: 'dsh-web-mobile',
      inject: [],
      apply(ctx) {
        // One small stylesheet per plugin lifetime. No resize listener, observer,
        // background timer, layout polling, or network permission.
        ctx.effect(() => {
          const existing = document.getElementById('ymdsh-mobile-021');
          if (existing) return () => {};
          const style = document.createElement('style');
          style.id = 'ymdsh-mobile-021';
          style.textContent = CSS;
          (document.head || document.documentElement).appendChild(style);
          return () => style.remove();
        }, 'ymdsh-mobile-responsive');
      },
    }),
  });
})();
