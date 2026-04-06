export function formatLongDate(date: Date = new Date()) {
    return new Intl.DateTimeFormat("es-BO", {
        weekday: "long",
        day: "2-digit",
        month: "long",
        year: "numeric",
    }).format(date);
}