import fs from "node:fs";
import path from "node:path";

const appPath = path.resolve("apps/web/app/App.jsx");
const citySelectorPath = path.resolve("apps/web/components/CitySelectorModal.tsx");

const appSource = fs.readFileSync(appPath, "utf8");
const citySelectorSource = fs.readFileSync(citySelectorPath, "utf8");

const checks = [
  {
    ok: appSource.includes("usePathname") && appSource.includes("useRouter"),
    message: "App должен использовать usePathname/useRouter для синхронизации города.",
  },
  {
    ok: appSource.includes("router.replace(") && appSource.includes("setCitySlug(resolvedNextCity);"),
    message: "Смена города на same-origin должна обновлять state и делать клиентскую навигацию без full reload.",
  },
  {
    ok: citySelectorSource.includes("fixed inset-x-3") && citySelectorSource.includes("sm:absolute"),
    message: "Модалка выбора города должна иметь mobile-safe fixed режим и desktop absolute режим.",
  },
];

const failedChecks = checks.filter((check) => !check.ok);

if (failedChecks.length > 0) {
  for (const failedCheck of failedChecks) {
    console.error(failedCheck.message);
  }
  process.exit(1);
}

console.log("city-ui-regression-check: ok");