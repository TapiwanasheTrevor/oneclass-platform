import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function formatDate(
  value: string | number | Date | null | undefined,
  locale = "en-ZW",
  options: Intl.DateTimeFormatOptions = {
    year: "numeric",
    month: "short",
    day: "numeric",
  }
) {
  if (!value) {
    return "--"
  }

  const date = value instanceof Date ? value : new Date(value)
  if (Number.isNaN(date.getTime())) {
    return "--"
  }

  return new Intl.DateTimeFormat(locale, options).format(date)
}

export function formatNumber(
  value: number | null | undefined,
  locale = "en-ZW",
  options?: Intl.NumberFormatOptions
) {
  const safeValue = value ?? 0
  return new Intl.NumberFormat(locale, options).format(safeValue)
}

export function formatPercentage(
  value: number | null | undefined,
  decimals = 1,
  locale = "en-ZW"
) {
  const safeValue = value ?? 0
  return new Intl.NumberFormat(locale, {
    style: "percent",
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  }).format(safeValue / 100)
}
