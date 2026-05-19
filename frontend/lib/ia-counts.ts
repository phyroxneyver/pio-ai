import type { IAVisualDetection } from "@/types/media";

export type IACategoryKey = "pollitos" | "gallinas" | "huevos";

export type IACounts = Record<IACategoryKey, number>;

export const EMPTY_IA_COUNTS: IACounts = {
  pollitos: 0,
  gallinas: 0,
  huevos: 0,
};

export const IA_CATEGORIES: Array<{
  key: IACategoryKey;
  title: string;
  singular: string;
  plural: string;
  description: string;
}> = [
  {
    key: "pollitos",
    title: "Pollos / pollitos",
    singular: "pollo/pollito",
    plural: "pollos/pollitos",
    description: "Crías o pollos detectados en la imagen",
  },
  {
    key: "gallinas",
    title: "Gallinas",
    singular: "gallina",
    plural: "gallinas",
    description: "Gallinas adultas detectadas",
  },
  {
    key: "huevos",
    title: "Huevos",
    singular: "huevo",
    plural: "huevos",
    description: "Huevos sin cocinar detectados",
  },
];

const CATEGORY_ALIASES: Record<IACategoryKey, string[]> = {
  pollitos: [
    "conteo_pollitos",
    "conteo_pollito",
    "conteo_pollos",
    "conteo_pollo",
    "pollitos",
    "pollito",
    "pollos",
    "pollo",
    "chicks",
    "chick",
  ],
  gallinas: [
    "conteo_gallinas",
    "conteo_gallina",
    "gallinas",
    "gallina",
    "hens",
    "hen",
  ],
  huevos: [
    "conteo_huevos",
    "conteo_huevo",
    "huevos",
    "huevo",
    "eggs",
    "egg",
  ],
};

function normalizeText(value: unknown) {
  return String(value ?? "")
    .trim()
    .toLowerCase()
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/[\s_-]+/g, " ");
}

function toCount(value: unknown): number | undefined {
  if (value === null || value === undefined || value === "") return undefined;

  const parsed = Number(value);
  if (!Number.isFinite(parsed)) return undefined;

  return Math.max(0, Math.trunc(parsed));
}

function parseObject(value: unknown): Record<string, unknown> {
  if (!value) return {};
  if (typeof value === "object" && !Array.isArray(value)) {
    return value as Record<string, unknown>;
  }

  if (typeof value !== "string") return {};

  try {
    const parsed = JSON.parse(value);
    return parsed && typeof parsed === "object" && !Array.isArray(parsed)
      ? (parsed as Record<string, unknown>)
      : {};
  } catch {
    return {};
  }
}

function readCountFromSources(key: IACategoryKey, sources: Array<Record<string, unknown>>) {
  for (const source of sources) {
    for (const alias of CATEGORY_ALIASES[key]) {
      const value = toCount(source[alias]);
      if (value !== undefined) return value;
    }
  }

  return undefined;
}

export function normalizeDetectionLabel(label: unknown): IACategoryKey | null {
  const normalized = normalizeText(label);

  if (["pollito", "pollitos", "pollo", "pollos", "chick", "chicks", "chicken"].includes(normalized)) {
    return "pollitos";
  }

  if (["gallina", "gallinas", "hen", "hens"].includes(normalized)) {
    return "gallinas";
  }

  if (["huevo", "huevos", "egg", "eggs"].includes(normalized)) {
    return "huevos";
  }

  return null;
}

export function countDetectionsByCategory(detections: IAVisualDetection[] = []): IACounts {
  const counts = { ...EMPTY_IA_COUNTS };

  detections.forEach((detection) => {
    const key = normalizeDetectionLabel(detection.label);
    if (key) counts[key] += 1;
  });

  return counts;
}

export function normalizeIACounts(raw: unknown): IACounts {
  const data = parseObject(raw);
  const notes = parseObject(data.notas_ia);
  const nestedCounts = parseObject(data.conteos) || parseObject(data.conteos_ia);
  const noteCounts = parseObject(notes.conteos) || parseObject(notes.conteos_ia);
  const detections = Array.isArray(data.detecciones)
    ? (data.detecciones as IAVisualDetection[])
    : [];
  const detectionCounts = countDetectionsByCategory(detections);

  const sources = [data, notes, nestedCounts, noteCounts];

  return IA_CATEGORIES.reduce<IACounts>((acc, category) => {
    acc[category.key] = readCountFromSources(category.key, sources) ?? detectionCounts[category.key];
    return acc;
  }, { ...EMPTY_IA_COUNTS });
}

export function totalIACounts(counts: IACounts) {
  return IA_CATEGORIES.reduce((total, category) => total + counts[category.key], 0);
}

export function formatIACounts(counts: IACounts) {
  const parts = IA_CATEGORIES
    .map((category) => {
      const value = counts[category.key];
      if (value <= 0) return null;
      return `${value} ${value === 1 ? category.singular : category.plural}`;
    })
    .filter(Boolean);

  return parts.length > 0 ? parts.join(" · ") : "0 detectados";
}

export function hasIACountDifference(a: IACounts, b: IACounts) {
  return IA_CATEGORIES.some((category) => a[category.key] !== b[category.key]);
}

export function getIACountDifference(a: IACounts, b: IACounts): IACounts {
  return IA_CATEGORIES.reduce<IACounts>((acc, category) => {
    acc[category.key] = a[category.key] - b[category.key];
    return acc;
  }, { ...EMPTY_IA_COUNTS });
}

export function buildCountsNote(prefix: string, counts: IACounts) {
  return `${prefix}: ${IA_CATEGORIES.map((category) => `${category.title}=${counts[category.key]}`).join(", ")}`;
}
