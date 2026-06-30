const STORAGE_KEY = "dynamic-fas-schemes-v1";

const LEGACY_QUESTION_TRANSLATIONS = {
  "Vui lòng mô tả hoàn cảnh tài chính hiện tại của gia đình.":
    "Please describe your family's current financial situation.",
  "Thu nhập của gia đình đã thay đổi như thế nào trong 6 tháng gần đây?":
    "How has your family's income changed over the past six months?",
  "Bạn có thông tin bổ sung nào muốn cung cấp không?":
    "Is there any additional information you would like to provide?",
};

const DEFAULT_SCHEMES = [
  {
    id: 10,
    name: "Financial Assistance Scheme 2026",
    questions: [
      {
        question_id: 101,
        question_text: "Please describe your family's current financial situation.",
        is_required: true,
      },
      {
        question_id: 102,
        question_text:
          "How has your family's income changed over the past six months?",
        is_required: true,
      },
      {
        question_id: 103,
        question_text: "Is there any additional information you would like to provide?",
        is_required: false,
      },
    ],
  },
];

function clone(value) {
  return JSON.parse(JSON.stringify(value));
}

function migrateLegacyQuestions(schemes) {
  return schemes.map((scheme) => ({
    ...scheme,
    questions: scheme.questions.map((question) => ({
      ...question,
      question_text:
        LEGACY_QUESTION_TRANSLATIONS[question.question_text] ??
        question.question_text,
    })),
  }));
}

export function loadSchemes() {
  try {
    const saved = localStorage.getItem(STORAGE_KEY);
    if (saved) {
      const parsed = JSON.parse(saved);
      if (Array.isArray(parsed)) {
        const migrated = migrateLegacyQuestions(parsed);
        localStorage.setItem(STORAGE_KEY, JSON.stringify(migrated));
        return migrated;
      }
    }
  } catch {
    // Fall through to the safe demo configuration.
  }

  const defaults = clone(DEFAULT_SCHEMES);
  localStorage.setItem(STORAGE_KEY, JSON.stringify(defaults));
  return defaults;
}

export function saveSchemes(schemes) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(schemes));
}

export function getNextSchemeId(schemes) {
  return Math.max(0, ...schemes.map((scheme) => Number(scheme.id) || 0)) + 1;
}

export function getNextQuestionId(schemes) {
  const questionIds = schemes.flatMap((scheme) =>
    scheme.questions.map((question) => Number(question.question_id) || 0),
  );
  return Math.max(100, ...questionIds) + 1;
}
