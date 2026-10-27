const CONSENT_KEY = "blanq_cookie_consent";
const ACCEPTED = "accepted";
const REJECTED = "rejected";

function getStorage() {
  if (typeof window === "undefined") return null;
  return window.localStorage;
}

function getCookieConsent() {
  const storage = getStorage();
  if (!storage) return null;

  const value = storage.getItem(CONSENT_KEY);
  return value === ACCEPTED || value === REJECTED ? value : null;
}

function hasCookieConsent() {
  return getCookieConsent() === ACCEPTED;
}

function acceptCookieConsent() {
  const storage = getStorage();
  if (!storage) return;
  storage.setItem(CONSENT_KEY, ACCEPTED);
}

function rejectCookieConsent() {
  const storage = getStorage();
  if (!storage) return;
  storage.setItem(CONSENT_KEY, REJECTED);
}

const cookieConsent = {
  get: getCookieConsent,
  hasAccepted: hasCookieConsent,
  accept: acceptCookieConsent,
  reject: rejectCookieConsent,
};

export default cookieConsent;



