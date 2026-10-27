// Маска и валидация российского телефона (+7 (XXX) XXX-XX-XX).
// Используется формами: обратный звонок и квиз-калькулятор.

export const PHONE_PREFIX = "+7 ";

export function formatPhone(value) {
  const digits = value.replace(/\D/g, "").replace(/^7|^8/, "").slice(0, 10);
  const p1 = digits.slice(0, 3);
  const p2 = digits.slice(3, 6);
  const p3 = digits.slice(6, 8);
  const p4 = digits.slice(8, 10);

  let result = PHONE_PREFIX;
  if (p1) result += `(${p1}`;
  if (p1.length === 3) result += ") ";
  if (p2) result += p2;
  if (p2.length === 3) result += "-";
  if (p3) result += p3;
  if (p3.length === 2) result += "-";
  if (p4) result += p4;

  return result;
}

export function isCompletePhone(value) {
  return value.replace(/\D/g, "").length >= 11;
}
