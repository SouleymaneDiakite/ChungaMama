"use client";

import { createContext, useContext, useEffect, useState } from "react";

export type Lang = "sw" | "en";

type LanguageContextValue = {
  lang: Lang;
  setLang: (l: Lang) => void;
};

const LanguageContext = createContext<LanguageContextValue>({
  lang: "sw",
  setLang: () => {},
});

export function LanguageProvider({ children }: { children: React.ReactNode }) {
  const [lang, setLangState] = useState<Lang>("sw");

  useEffect(() => {
    const stored = localStorage.getItem("chungamama_lang") as Lang | null;
    if (stored === "sw" || stored === "en") setLangState(stored);
  }, []);

  function setLang(l: Lang) {
    setLangState(l);
    localStorage.setItem("chungamama_lang", l);
    document.documentElement.lang = l;
  }

  return (
    <LanguageContext.Provider value={{ lang, setLang }}>
      {children}
    </LanguageContext.Provider>
  );
}

export function useLanguage() {
  return useContext(LanguageContext);
}

// Small helper so components can write t(ui.nav.guide) instead of
// ui.nav.guide[lang] everywhere.
export type L = { sw: string; en: string };
export function pick(text: L, lang: Lang): string {
  return text[lang];
}

export const ui = {
  nav: {
    guide: { sw: "Kitabu", en: "Guide" },
    assistant: { sw: "Msaidizi", en: "Assistant" },
    login: { sw: "Ingia", en: "Log in" },
    logout: { sw: "Toka", en: "Log out" },
    greeting: { sw: "Habari,", en: "Hi," },
  },
  footer: {
    tagline: {
      sw: "Kitabu chako cha afya, sasa kinazungumza nawe.",
      en: "Your health handbook, now talks back.",
    },
    copyright: {
      sw: "\u00a9 2026 ChungaMama. Haki zote zimehifadhiwa.",
      en: "\u00a9 2026 ChungaMama. All rights reserved.",
    },
  },
  home: {
    heroTitle: {
      sw: "Kitabu chako cha afya, sasa kinazungumza nawe.",
      en: "Your health handbook, now talks back.",
    },
    heroLede: {
      sw: "ChungaMama inachukua kile ulichojua tayari kutoka kitabu cha MOH cha afya ya mama na mtoto, na kukifanya kisikilize, kiulize, na kukushauri \u2014 kwa sauti au maandishi, kwa Kiswahili au Kiingereza.",
      en: "ChungaMama takes what you already know from the MOH mother and child health handbook, and makes it listen, ask, and advise you \u2014 by voice or text, in Swahili or English.",
    },
    ctaVoice: { sw: "Ongea nasi", en: "Talk to us" },
    ctaText: { sw: "Andika ujumbe", en: "Send a message" },
    trustLine: {
      sw: "Imejengwa juu ya miongozo ya WHO na Wizara ya Afya Kenya",
      en: "Built on WHO and Kenya Ministry of Health guidelines",
    },
    pillar1Title: { sw: "Kitabu bado ni chako", en: "The handbook is still yours" },
    pillar1Body: {
      sw: "Hakuna anayekuambia uache kitabu chako cha karatasi \u2014 tunakisaidia tu kikusikilize.",
      en: "No one is telling you to give up your paper handbook \u2014 we're just helping it listen back.",
    },
    pillar2Title: { sw: "Sauti kwanza", en: "Voice first" },
    pillar2Body: {
      sw: "Hakuna haja ya kusoma. Ongea tu, kama unavyozungumza na mkunga.",
      en: "No need to read. Just speak, the way you'd talk to a midwife.",
    },
    pillar3Title: { sw: "Imethibitishwa", en: "Verified" },
    pillar3Body: {
      sw: "Kila jibu limejikita kwenye miongozo ya WHO na Wizara ya Afya, si mawazo ya jumla.",
      en: "Every answer is grounded in WHO and Ministry of Health guidance, not general assumptions.",
    },
    guideSectionTitle: { sw: "Kila ukurasa, sasa una sauti", en: "Every page, now has a voice" },
    guideSectionLede: {
      sw: "Kitabu cha MOH kina kurasa za ukuaji wa mtoto na ujauzito. Tumezifanya kurasa hizo ziwe za mazungumzo \u2014 uliza wakati wowote.",
      en: "The MOH handbook has pages on child growth and pregnancy. We've turned those pages into conversation \u2014 ask anytime.",
    },
    seeAllTopics: { sw: "Ona mada zote", en: "See all topics" },
    chwPrompt: { sw: "Wewe ni mfanyakazi wa afya (CHW) au kliniki?", en: "Are you a health worker (CHW) or clinic staff?" },
    dashboardLink: { sw: "Fungua dashibodi ya takwimu", en: "Open the staff dashboard" },
  },
  guideIndex: {
    title: { sw: "Kitabu", en: "Guide" },
    lede: {
      sw: "Chagua mada kupata mwongozo kamili \u2014 kila ukurasa umejikita kwenye miongozo ya WHO na Wizara ya Afya.",
      en: "Choose a topic for the full guide \u2014 every page is grounded in WHO and Ministry of Health guidance.",
    },
  },
  guideDetail: {
    back: { sw: "Kitabu", en: "Guide" },
    dangerBanner: {
      sw: "Ukiwa na dalili yoyote hapa chini, nenda kliniki mara moja \u2014 usisubiri.",
      en: "If you have any of the signs below, go to a clinic immediately \u2014 don't wait.",
    },
    questionPrompt: { sw: "Una swali zaidi kuhusu hili?", en: "Have more questions about this?" },
    askAssistant: { sw: "Ongea na Msaidizi", en: "Talk to the Assistant" },
  },
  assistant: {
    title: { sw: "Msaidizi", en: "Assistant" },
    greeting: {
      sw: "Habari! Mimi ni msaidizi wako wa afya ya uzazi. Unaweza kuniuliza kuhusu ujauzito, lishe, chanjo, au kama unajisikia vibaya.",
      en: "Hello! I'm your maternal health assistant. You can ask me about pregnancy, nutrition, vaccination, or if you're feeling unwell.",
    },
    placeholder: { sw: "Andika ujumbe...", en: "Type your message..." },
    send: { sw: "Tuma", en: "Send" },
    thinking: { sw: "Inachakata\u2026", en: "Thinking\u2026" },
    disclaimer: { sw: "Kielelezo \u2014 si mbadala wa huduma ya afya.", en: "Prototype \u2014 not a substitute for medical care." },
    errorPrefix: { sw: "Hitilafu:", en: "Error:" },
  },
  login: {
    title: { sw: "Ingia", en: "Log in" },
    identifierPlaceholder: { sw: "Barua pepe au nambari ya simu", en: "Email or phone number" },
    passwordPlaceholder: { sw: "Nenosiri", en: "Password" },
    submit: { sw: "Ingia", en: "Log in" },
    submitting: { sw: "Inaingia...", en: "Logging in..." },
    noAccount: { sw: "Huna akaunti?", en: "Don't have an account?" },
    registerLink: { sw: "Jisajili hapa", en: "Sign up here" },
    forgotPassword: { sw: "Umesahau nenosiri?", en: "Forgot password?" },
  },
  register: {
    title: { sw: "Fungua akaunti", en: "Create an account" },
    namePlaceholder: { sw: "Jina lako", en: "Your name" },
    identifierPlaceholder: { sw: "Barua pepe au nambari ya simu", en: "Email or phone number" },
    passwordPlaceholder: { sw: "Nenosiri", en: "Password" },
    submit: { sw: "Jisajili", en: "Sign up" },
    submitting: { sw: "Inatuma...", en: "Submitting..." },
    successMessage: { sw: "Akaunti imeundwa. Sasa unaweza kuingia.", en: "Account created. You can now log in." },
    haveAccount: { sw: "Tayari una akaunti?", en: "Already have an account?" },
    loginLink: { sw: "Ingia hapa", en: "Log in here" },
    roleLabel: { sw: "Wewe ni nani?", en: "Which are you?" },
    roleMother: { sw: "Mama / Mjamzito", en: "Mother / Expecting" },
    roleChw: { sw: "Mfanyakazi wa Afya (CHW)", en: "Community Health Worker (CHW)" },
    roleClinician: { sw: "Kliniki / Muuguzi", en: "Clinician / Nurse" },
    roleAdmin: { sw: "Msimamizi", en: "Admin" },
  },
  forgotPassword: {
    title: { sw: "Umesahau Nenosiri", en: "Forgot Password" },
    lede: {
      sw: "Weka barua pepe au nambari ya simu uliyotumia kujisajili.",
      en: "Enter the email or phone number you registered with.",
    },
    submit: { sw: "Tuma", en: "Send" },
    submitting: { sw: "Inatuma...", en: "Sending..." },
    genericSuccess: {
      sw: "Kama akaunti hiyo ipo, kiungo cha kubadilisha nenosiri kimetumwa.",
      en: "If that account exists, a reset link has been sent.",
    },
    backToLogin: { sw: "Rudi kuingia", en: "Back to log in" },
  },
  resetPassword: {
    title: { sw: "Weka Nenosiri Jipya", en: "Set a New Password" },
    newPasswordPlaceholder: { sw: "Nenosiri jipya", en: "New password" },
    submit: { sw: "Badilisha Nenosiri", en: "Reset Password" },
    submitting: { sw: "Inabadilisha...", en: "Resetting..." },
    success: {
      sw: "Nenosiri limebadilishwa. Sasa unaweza kuingia.",
      en: "Password updated. You can now log in.",
    },
    invalidLink: {
      sw: "Kiungo hiki si sahihi au kimeisha muda. Omba kiungo kipya.",
      en: "This link is invalid or has expired. Request a new one.",
    },
    missingToken: {
      sw: "Hakuna token ya kubadilisha nenosiri katika kiungo hiki.",
      en: "No reset token found in this link.",
    },
  },
  dashboard: {
    title: { sw: "Dashibodi ya Wafanyakazi", en: "Staff Dashboard" },
    lede: {
      sw: "Kesi zilizoainishwa kuwa za hatari au zisizo na uhakika, kutoka kwa Msaidizi.",
      en: "Cases flagged as high-risk or uncertain, from the Assistant.",
    },
    noAccessError: {
      sw: "Akaunti hii si ya wafanyakazi wa afya (CHW/clinician/admin).",
      en: "This account is not a health worker account (CHW/clinician/admin).",
    },
    loading: { sw: "Inapakia...", en: "Loading..." },
    empty: { sw: "Hakuna kesi zilizopelekwa kwa sasa.", en: "No cases have been escalated yet." },
    markReviewed: { sw: "Tia alama imekaguliwa", en: "Mark as reviewed" },
  },
} as const;
