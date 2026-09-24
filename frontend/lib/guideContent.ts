// Content adapted from the Kenya Ministry of Health Mother & Child Health
// Handbook (MOH216, revised edition September 2020), paraphrased rather
// than reproduced verbatim. Where the handbook itself already provides
// English terminology (danger signs, food groups, immunization schedule),
// that terminology is used directly for accuracy.

import type { L } from "./i18n";

export type GuideTopic = {
  slug: string;
  title: L;
  shortDesc: L;
  icon: "calendar" | "leaf" | "warning" | "syringe" | "heart" | "clipboard" | "support";
  accent: "blue" | "gold" | "maroon";
  image: string;
  sections: { heading: L; body: L[] }[];
};

export const guideTopics: GuideTopic[] = [
  {
    slug: "mpango-wa-kuzaa",
    title: { sw: "Mpango wa Kuzaa", en: "Birth Plan" },
    shortDesc: {
      sw: "Jitayarishe mapema kwa kujifungua salama na kwa afya.",
      en: "Prepare early for a safe and healthy childbirth.",
    },
    icon: "clipboard",
    accent: "blue",
    image: "/images/guide/mpango-wa-kuzaa.jpg",
    sections: [
      // Source: Birth Plan, p.2
      {
        heading: { sw: "Jiandae Pamoja na Mkunga Wako", en: "Prepare Together With Your Midwife" },
        body: [
          { sw: "Tarehe inayotarajiwa ya kujifungua (EDD).", en: "Expected date of childbirth (EDD)." },
          { sw: "Kituo cha afya utakachojifungulia, na jina lake.", en: "The health facility name where you'll give birth." },
          { sw: "Nani atakayesaidia kukuzalisha (mkunga au daktari).", en: "Who your birth attendant will be." },
          { sw: "Namba ya simu ya kituo cha afya, iwe tayari kwa dharura.", en: "The health facility's contact number, ready for emergencies." },
          { sw: "Mtu wa kukusindikiza wakati wa kujifungua.", en: "Your support person or birth companion." },
          { sw: "Usafiri utakaotumia kufika kituoni, hasa ukiwa mbali.", en: "Transport arrangements to reach the facility, especially if far." },
          { sw: "Kama utahitaji mchangiaji damu, mpange mapema.", en: "A blood donor, arranged in advance if needed." },
          { sw: "Mpango wa kifedha kwa gharama za kujifungua.", en: "A financial plan for childbirth costs." },
        ],
      },
      {
        heading: { sw: "Kwa Nini Hii Ni Muhimu", en: "Why This Matters" },
        body: [
          { sw: "Mpango ulioandaliwa mapema hupunguza wasiwasi na kuchelewa wakati uchungu unapoanza.", en: "A plan made early reduces worry and delay once labor starts." },
          { sw: "Familia inayojua mpango huu inaweza kukusaidia haraka zaidi katika dharura.", en: "A family that knows this plan can help you faster in an emergency." },
        ],
      },
    ],
  },
  {
    slug: "wiki-kwa-wiki",
    title: { sw: "Ziara za Kliniki (ANC)", en: "Clinic Visits (ANC)" },
    shortDesc: {
      sw: "Ratiba ya ziara nane za kliniki wakati wa ujauzito.",
      en: "The schedule of eight antenatal clinic visits during pregnancy.",
    },
    icon: "calendar",
    accent: "blue",
    image: "/images/guide/wiki-kwa-wiki.jpg",
    sections: [
      // Source: Malaria Prophylaxis / IFAS contact schedule, p.10; Care During Pregnancy, p.13
      {
        heading: { sw: "Ziara Nane Zinazopendekezwa", en: "The Eight Recommended Visits" },
        body: [
          { sw: "Ziara ya 1: kabla ya wiki 12 \u2014 anza mapema iwezekanavyo.", en: "Visit 1: before 12 weeks \u2014 start as early as possible." },
          { sw: "Ziara ya 2: wiki 20.", en: "Visit 2: week 20." },
          { sw: "Ziara ya 3: wiki 26.", en: "Visit 3: week 26." },
          { sw: "Ziara ya 4: wiki 30.", en: "Visit 4: week 30." },
          { sw: "Ziara ya 5: wiki 34.", en: "Visit 5: week 34." },
          { sw: "Ziara ya 6: wiki 36.", en: "Visit 6: week 36." },
          { sw: "Ziara ya 7: wiki 38.", en: "Visit 7: week 38." },
          { sw: "Ziara ya 8: wiki 40.", en: "Visit 8: week 40." },
        ],
      },
      {
        heading: { sw: "Kila Ziara, Hivi Hufanyika", en: "What Happens at Every Visit" },
        body: [
          { sw: "Uzito na shinikizo la damu hupimwa na kurekodiwa.", en: "Weight and blood pressure are measured and recorded." },
          { sw: "Unapewa dawa za IFAS (chuma na folic acid) za kutosha hadi ziara ijayo.", en: "You receive enough IFAS (iron and folic acid) tablets to last until the next visit." },
          { sw: "Unapata dozi ya IPTp dhidi ya malaria (kila baada ya wiki 4 kuanzia wiki 13).", en: "You receive an IPTp dose against malaria (every 4 weeks from week 13)." },
          { sw: "Msogeo wa mtoto na mapigo ya moyo wake huchunguzwa kadri ujauzito unavyoendelea.", en: "The baby's movement and heart rate are checked as the pregnancy progresses." },
        ],
      },
      {
        heading: { sw: "Kabla ya Ziara ya Kwanza", en: "Before Your First Visit" },
        body: [
          { sw: "Nenda kliniki mara tu unapojua kuwa una ujauzito \u2014 usisubiri dalili au wiki fulani.", en: "Go to clinic as soon as you know you're pregnant \u2014 don't wait for symptoms or a specific week." },
          { sw: "Beba kitabu hiki kila ziara na uonyeshe mhudumu wa afya.", en: "Carry this handbook to every visit and show it to the health worker." },
        ],
      },
    ],
  },
  {
    slug: "lishe-na-mazoezi",
    title: { sw: "Lishe na Mazoezi", en: "Nutrition and Exercise" },
    shortDesc: {
      sw: "Makundi 10 ya vyakula na jinsi ya kula vizuri wakati wa ujauzito.",
      en: "The 10 food groups and how to eat well during pregnancy.",
    },
    icon: "leaf",
    accent: "gold",
    image: "/images/guide/lishe-na-mazoezi.png",
    sections: [
      // Source: Healthy Eating During Pregnancy and Breastfeeding, p.18; Care During Pregnancy, p.13
      {
        heading: { sw: "Makundi 10 ya Vyakula", en: "The 10 Food Groups" },
        body: [
          { sw: "Nafaka na vyakula vya wanga (mahindi, mchele, ngano).", en: "Grains, grain products and other starchy foods." },
          { sw: "Mikunde na jamii ya maharage.", en: "Legumes and pulses." },
          { sw: "Karanga na mbegu.", en: "Nuts and seeds." },
          { sw: "Maziwa na bidhaa za maziwa.", en: "Dairy and milk products." },
          { sw: "Mayai.", en: "Eggs." },
          { sw: "Nyama, samaki, kuku, na wadudu wanaoliwa.", en: "Flesh foods \u2014 beef, fish, poultry, insects, organ meat." },
          { sw: "Matunda na mboga za rangi ya chungwa au njano.", en: "Orange or yellow-fleshed fruits and vegetables." },
          { sw: "Mboga za majani ya kijani kibichi.", en: "Dark green leafy vegetables." },
          { sw: "Mboga nyingine.", en: "Other vegetables." },
          { sw: "Matunda mengine.", en: "Other fruits." },
        ],
      },
      {
        heading: { sw: "Kanuni za Msingi", en: "The Basics" },
        body: [
          { sw: "Kula angalau makundi 5 kati ya 10 kila siku.", en: "Eat at least 5 of the 10 food groups every day." },
          { sw: "Kula chakula cha ziada kimoja kila siku wakati wa ujauzito.", en: "Eat one extra meal every day during pregnancy." },
          { sw: "Kunywa maji glasi 8 (lita 2) kila siku.", en: "Drink at least 8 glasses (2 litres) of water every day." },
          { sw: "Chukua dawa za IFAS kila siku wakati wote wa ujauzito.", en: "Take IFAS supplements every day throughout pregnancy." },
          { sw: "Lala chini ya neti iliyowekwa dawa (LLIN) kila usiku.", en: "Sleep under a long-lasting insecticidal net (LLIN) every night." },
          { sw: "Fanya mazoezi mepesi, yasiyo makali, mara kwa mara.", en: "Do regular, non-strenuous exercise." },
          { sw: "Epuka kazi nzito \u2014 pumzika zaidi.", en: "Avoid heavy work \u2014 rest more." },
        ],
      },
    ],
  },
  {
    slug: "dalili-za-hatari",
    title: { sw: "Dalili za Hatari", en: "Danger Signs" },
    shortDesc: {
      sw: "Dalili za mama na mtoto zinazohitaji uende kliniki mara moja.",
      en: "Signs in mother and baby that mean you should go to clinic immediately.",
    },
    icon: "warning",
    accent: "maroon",
    image: "/images/guide/dalili-za-hatari.jpg",
    sections: [
      // Source: Danger Signs During Pregnancy, p.14
      {
        heading: { sw: "Wakati wa Ujauzito", en: "During Pregnancy" },
        body: [
          { sw: "Kutokwa na damu ukeni.", en: "Vaginal bleeding." },
          { sw: "Maumivu makali ya kichwa.", en: "Severe headache." },
          { sw: "Homa.", en: "Fever." },
          { sw: "Kuonekana mweupe/rangi hafifu (pale).", en: "Looking pale." },
          { sw: "Uvimbe wa uso na mikono.", en: "Swelling of face and hands." },
          { sw: "Maji kutoka kabla ya uchungu kuanza.", en: "Breaking of water before labor starts." },
          { sw: "Kifafa au kutetemeka mwilini (convulsions).", en: "Convulsions or fits." },
          { sw: "Maumivu makali ya tumbo.", en: "Severe abdominal pain." },
          { sw: "Kupungua au kukosekana kwa msogeo wa mtoto tumboni.", en: "Reduced or no movement of the unborn baby." },
        ],
      },
      // Source: Danger Signs for Mother after Childbirth, p.19
      {
        heading: { sw: "Mama, Baada ya Kujifungua", en: "Mother, After Childbirth" },
        body: [
          { sw: "Kutokwa na damu nyingi.", en: "Heavy bleeding." },
          { sw: "Homa.", en: "Fever." },
          { sw: "Maumivu makali ya kichwa.", en: "Severe headache." },
          { sw: "Majimaji yenye harufu mbaya ukeni.", en: "Foul-smelling vaginal discharge." },
          { sw: "Kifafa au kutetemeka mwilini.", en: "Fits or convulsions." },
        ],
      },
      // Source: Danger Signs for Mother after Childbirth (Baby), p.19
      {
        heading: { sw: "Mtoto Mchanga", en: "Newborn Baby" },
        body: [
          { sw: "Anaacha kunyonya vizuri.", en: "Stops breastfeeding well." },
          { sw: "Anapumua kwa shida au haraka sana.", en: "Has difficult or fast breathing." },
          { sw: "Anahisi joto kupita kiasi au baridi kupita kiasi.", en: "Feels unusually hot or cold." },
          { sw: "Anapungua nguvu au kutotaka kucheza kama kawaida.", en: "Becomes less active than usual." },
          { sw: "Mwili unageuka rangi ya njano, hasa machoni, vitanga vya mikono, na nyayo za miguu.", en: "Body becomes yellow, especially the eyes, palms, and soles." },
        ],
      },
      {
        heading: { sw: "Ukiwa na Dalili Yoyote Hapo Juu", en: "If You Have Any of the Signs Above" },
        body: [
          { sw: "Nenda kliniki au hospitali mara moja \u2014 usisubiri iishe yenyewe.", en: "Go to a clinic or hospital immediately \u2014 don't wait for it to pass." },
          { sw: "Unaweza pia kumwambia ChungaMama dalili unazohisi \u2014 mfumo utakusaidia kutambua uzito wa hali na kukuelekeza hatua za haraka.", en: "You can also tell ChungaMama what you're feeling \u2014 the system will help assess how serious it is and guide you on next steps." },
        ],
      },
    ],
  },
  {
    slug: "chanjo",
    title: { sw: "Chanjo", en: "Immunization" },
    shortDesc: {
      sw: "Ratiba rasmi ya chanjo za mtoto kutoka kuzaliwa hadi miezi 18.",
      en: "The official child immunization schedule from birth to 18 months.",
    },
    icon: "syringe",
    accent: "blue",
    image: "/images/guide/chanjo.jpg",
    sections: [
      // Source: Immunization, p.33-34
      {
        heading: { sw: "Wakati wa Kuzaliwa", en: "At Birth" },
        body: [
          { sw: "BCG (kinga dhidi ya kifua kikuu).", en: "BCG (protection against tuberculosis)." },
          { sw: "Chanjo ya kwanza ya Polio (OPV).", en: "First dose of Polio vaccine (OPV)." },
        ],
      },
      {
        heading: { sw: "Wiki 6, 10, na 14", en: "Weeks 6, 10, and 14" },
        body: [
          { sw: "Polio (OPV) \u2014 dozi katika kila ziara.", en: "Polio (OPV) \u2014 a dose at each visit." },
          { sw: "Pentavalent (DPT-HepB-Hib) \u2014 kinga dhidi ya dondakoo, kifaduro, pepopunda, homa ya ini B, na Hib.", en: "Pentavalent (DPT-HepB-Hib) \u2014 protection against diphtheria, pertussis, tetanus, hepatitis B, and Hib." },
          { sw: "Chanjo ya Pneumococcal (PCV).", en: "Pneumococcal Conjugate Vaccine (PCV)." },
          { sw: "Chanjo ya Rotavirus.", en: "Rotavirus vaccine." },
          { sw: "IPV (chanjo ya polio ya sindano) hutolewa wiki ya 14.", en: "IPV (injectable polio vaccine) is given at week 14." },
        ],
      },
      {
        heading: { sw: "Miezi 6, 9, na 18", en: "Months 6, 9, and 18" },
        body: [
          { sw: "Miezi 6: MR (Surua na Rubella) \u2014 hutolewa hasa endapo kuna mlipuko wa surua au mtoto ni HIV Exposed Infant.", en: "Month 6: MR (Measles-Rubella) \u2014 given in the event of a measles outbreak or if the baby is HIV-exposed." },
          { sw: "Miezi 9: MR \u2014 dozi ya kawaida kwa watoto wote.", en: "Month 9: MR \u2014 the standard dose for all children." },
          { sw: "Miezi 9: Chanjo ya Homa ya Manjano (Yellow Fever) \u2014 katika kaunti fulani tu.", en: "Month 9: Yellow Fever vaccine \u2014 in selected counties only." },
          { sw: "Miezi 18: MR \u2014 dozi ya nyongeza.", en: "Month 18: MR \u2014 booster dose." },
        ],
      },
      {
        heading: { sw: "Muhimu Kufahamu", en: "Important to Know" },
        body: [
          { sw: "Chanjo zilizokosekana zinaweza kupatikana baadaye \u2014 usiogope kurudi kliniki hata kama umechelewa.", en: "Missed vaccines can still be given later \u2014 don't be afraid to return to clinic even if you're behind schedule." },
          { sw: "Endapo mtoto atapata madhara yoyote baada ya chanjo, ripoti mara moja kituo cha afya kilicho karibu.", en: "If your child has any adverse reaction after a vaccine, report it immediately to the nearest health facility." },
        ],
      },
    ],
  },
  {
    slug: "usaidizi-wa-baba",
    title: { sw: "Usaidizi wa Baba", en: "Father's Support" },
    shortDesc: {
      sw: "Jinsi baba anavyoweza kusaidia afya ya mama na mtoto.",
      en: "How fathers can support the health of mother and child.",
    },
    icon: "support",
    accent: "gold",
    image: "/images/guide/usaidizi-wa-baba.png",
    sections: [
      // Source: Father's Support for Mother & Child Health, p.3-4
      {
        heading: { sw: "Wakati wa Ujauzito", en: "During Pregnancy" },
        body: [
          { sw: "Msaidie mke/mpenzi wako na kazi za nyumbani.", en: "Help your wife/partner with household chores." },
          { sw: "Hakikisha anakula vizuri na kuhudhuria kliniki mara 8 wakati wa ujauzito.", en: "Ensure she eats well and attends clinic 8 times during pregnancy." },
          { sw: "Msindikize kwenye kituo cha afya inapowezekana.", en: "Accompany her to the health facility whenever possible." },
          { sw: "Pima na tibiwa magonjwa ya zinaa, ikiwemo HIV.", en: "Get tested and treated for STIs, including HIV." },
          { sw: "Panga pamoja mpango wa kuzaa.", en: "Prepare a birth plan together." },
          { sw: "Zungumzeni kuhusu njia ya uzazi wa mpango mtakayochagua.", en: "Discuss the family planning method you'll choose together." },
        ],
      },
      {
        heading: { sw: "Wakati wa Kujifungua", en: "During Childbirth" },
        body: [
          { sw: "Hakikisha usafiri wa kwenda kituo cha afya upo tayari.", en: "Make sure transport to the health facility is ready." },
          { sw: "Hakikisha watoto wengine wanaangaliwa.", en: "Ensure other children are taken care of." },
          { sw: "Kama upo wakati wa kujifungua, mpe moyo na msaada wa kimwili.", en: "If you're present during birth, offer emotional and physical support." },
          { sw: "Msaidie kutembea au kupumzika wakati wa uchungu.", en: "Help her walk or rest during contractions." },
        ],
      },
      {
        heading: { sw: "Baada ya Kujifungua", en: "After Childbirth" },
        body: [
          { sw: "Wiki sita za kwanza ni muhimu zaidi kwa mama na mtoto.", en: "The first six weeks are the most important for mother and baby." },
          { sw: "Msaidie mama kupumzika na kupata usingizi wa kutosha.", en: "Help the mother rest and get enough sleep." },
          { sw: "Shikilia na umtunze mtoto mara kwa mara ili mama apate nafasi ya kupumzika.", en: "Hold and care for the baby often so the mother gets a chance to rest." },
          { sw: "Msindikize mama kupata huduma ya baada ya kujifungua (PNC).", en: "Accompany the mother to postnatal care (PNC) visits." },
        ],
      },
    ],
  },
  {
    slug: "afya-ya-akili",
    title: { sw: "Afya ya Akili", en: "Mental Health" },
    shortDesc: {
      sw: "Hisia baada ya kujifungua ni za kawaida \u2014 hauko peke yako.",
      en: "Feelings after childbirth are normal \u2014 you're not alone.",
    },
    icon: "heart",
    accent: "gold",
    image: "/images/guide/afya-ya-akili.jpg",
    sections: [
      {
        heading: { sw: "Ni Kawaida Kuhisi Hivi", en: "It's Normal to Feel This Way" },
        body: [
          { sw: "Wanawake wengi hupitia mabadiliko ya hisia wakati wa ujauzito na baada ya kujifungua \u2014 hii si udhaifu, ni sehemu ya mchakato wa mwili na maisha mapya.", en: "Many women go through mood changes during pregnancy and after childbirth \u2014 this isn't weakness, it's part of the body's process and new life." },
          { sw: "Kliniki yako hufanya uchunguzi wa afya ya akili katika ziara za baada ya kujifungua \u2014 hii ni utaratibu wa kawaida, si kwa sababu kuna tatizo.", en: "Your clinic screens for mental health at postnatal visits \u2014 this is routine practice, not a sign something is wrong." },
        ],
      },
      {
        heading: { sw: "Dalili za Kuangalia", en: "Signs to Watch For" },
        body: [
          { sw: "Huzuni au uchovu unaoendelea kwa zaidi ya wiki mbili.", en: "Sadness or exhaustion that continues for more than two weeks." },
          { sw: "Ugumu wa kumhusiana na mtoto wako.", en: "Difficulty bonding with your baby." },
          { sw: "Kama una mawazo ya kujidhuru wewe mwenyewe, tafuta msaada mara moja kutoka kwa mfanyakazi wa afya au mtu unayemwamini.", en: "If you have thoughts of harming yourself, seek help immediately from a health worker or someone you trust." },
        ],
      },
      {
        heading: { sw: "Huna Peke Yako", en: "You're Not Alone" },
        body: [
          { sw: "ChungaMama inakupa nafasi salama ya kuzungumza kuhusu hisia zako bila hukumu.", en: "ChungaMama gives you a safe space to talk about your feelings without judgment." },
          { sw: "Kuzungumza na mkunga, CHW, au mtu wa familia unayemwamini ni hatua muhimu ya kwanza.", en: "Talking to a midwife, CHW, or a trusted family member is an important first step." },
        ],
      },
    ],
  },
];

export function getTopicBySlug(slug: string): GuideTopic | undefined {
  return guideTopics.find((t) => t.slug === slug);
}
