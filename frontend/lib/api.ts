const RAW_API_URL =
  process.env.NEXT_PUBLIC_API_URL || "backend-pio-ai.vercel.app";

function normalizeApiUrl(url: string) {
  const cleanUrl = url.trim().replace(/\/$/, "");

  if (cleanUrl.startsWith("http://") || cleanUrl.startsWith("https://")) {
    return cleanUrl;
  }

  return `https://${cleanUrl}`;
}

export const API_URL = normalizeApiUrl(RAW_API_URL);

export type IAFeedbackPayload = {
  conteo_corregido: number;
  tipo_feedback: "correccion" | "fallida";
  motivo?: string;
};

export async function loginReal(correo: string, password: string) {
  const formData = new URLSearchParams();

  formData.append("username", correo);
  formData.append("password", password);

  const res = await fetch(`${API_URL}/auth/login`, {
    method: "POST",
    headers: {
      "Content-Type": "application/x-www-form-urlencoded",
    },
    body: formData.toString(),
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Credenciales incorrectas");
  }

  const data = await res.json();

  return {
    token: data.access_token,
    user: {
      nombre: correo.split("@")[0],
      rol: "operador",
      correo,
    },
  };
}

export async function fetchWithAuth(endpoint: string, options: RequestInit = {}) {
  const token = localStorage.getItem("pioai_token");

  const headers = new Headers(options.headers || {});

  if (!(options.body instanceof FormData) && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  return fetch(`${API_URL}${endpoint}`, {
    ...options,
    headers,
  });
}

export async function listarAves() {
  return fetchWithAuth("/aves").then((r) => r.json());
}

export async function registrarAve(
  tipo: "pollito" | "gallina",
  cantidad: number,
  notas?: string,
) {
  return fetchWithAuth("/aves", {
    method: "POST",
    body: JSON.stringify({
      tipo,
      cantidad,
      notas,
    }),
  });
}

export async function listarHuevos() {
  return fetchWithAuth("/produccion-huevos").then((r) => r.json());
}

export async function registrarHuevos(
  ave_id: number,
  cantidad_huevos: number,
  notas?: string,
) {
  return fetchWithAuth("/produccion-huevos", {
    method: "POST",
    body: JSON.stringify({
      ave_id,
      cantidad_huevos,
      notas,
    }),
  });
}

export async function listarAlertas(estado?: string) {
  const url = estado ? `/alertas?estado=${estado}&limit=50` : "/alertas?limit=50";

  return fetchWithAuth(url).then((r) => r.json());
}

export async function marcarAlertaLeida(id: number) {
  return fetchWithAuth(`/alertas/${id}/leida`, {
    method: "PATCH",
  }).then((r) => r.json());
}

export async function subirImagen(file: File) {
  const token = localStorage.getItem("pioai_token");
  const formData = new FormData();

  formData.append("file", file);

  const res = await fetch(`${API_URL}/imagenes/upload`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
    },
    body: formData,
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "No se pudo subir la imagen.");
  }

  return res.json();
}

export async function enviarFeedbackIA(
  imagenId: number,
  payload: IAFeedbackPayload,
) {
  const res = await fetchWithAuth(`/imagenes/${imagenId}/feedback`, {
    method: "POST",
    body: JSON.stringify(payload),
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "No se pudo enviar el feedback de IA.");
  }

  return res.json();
}

export async function obtenerUltimaMetricaIA() {
  const res = await fetchWithAuth("/imagenes/ia/metricas/ultima");

  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "No hay métricas de IA disponibles.");
  }

  return res.json();
}