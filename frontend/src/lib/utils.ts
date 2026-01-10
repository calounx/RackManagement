import { type ClassValue, clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

/**
 * Utility function for merging Tailwind CSS classes
 * Combines clsx for conditional classes and tailwind-merge to handle conflicts
 */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

/**
 * Format bytes to human-readable size
 */
export function formatBytes(bytes: number, decimals = 2): string {
  if (bytes === 0) return '0 Bytes';

  const k = 1024;
  const dm = decimals < 0 ? 0 : decimals;
  const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];

  const i = Math.floor(Math.log(bytes) / Math.log(k));

  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(dm))} ${sizes[i]}`;
}

/**
 * Format power consumption to human-readable string
 */
export function formatPower(watts: number): string {
  if (watts >= 1000) {
    return `${(watts / 1000).toFixed(2)} kW`;
  }
  return `${watts.toFixed(0)} W`;
}

/**
 * Format temperature with unit
 */
export function formatTemperature(celsius: number): string {
  return `${celsius.toFixed(1)}°C`;
}

/**
 * Get thermal status based on temperature
 */
export function getThermalStatus(temp: number): {
  status: 'cold' | 'cool' | 'warm' | 'hot' | 'critical';
  color: string;
  label: string;
} {
  if (temp < 20) {
    return { status: 'cold', color: 'text-blue-400', label: 'Cold' };
  } else if (temp < 30) {
    return { status: 'cool', color: 'text-green-400', label: 'Cool' };
  } else if (temp < 40) {
    return { status: 'warm', color: 'text-amber', label: 'Warm' };
  } else if (temp < 50) {
    return { status: 'hot', color: 'text-orange-500', label: 'Hot' };
  } else {
    return { status: 'critical', color: 'text-red-500', label: 'Critical' };
  }
}

/**
 * Get cable type color
 */
export function getCableColor(cableType: string): string {
  const colors: Record<string, string> = {
    ethernet: 'rgb(var(--electric-blue))',
    fiber: 'rgb(var(--lime))',
    power: 'rgb(var(--amber))',
    console: 'rgb(148, 163, 184)',
  };
  return colors[cableType.toLowerCase()] || colors.console;
}

/**
 * Calculate rack space usage percentage
 */
export function calculateRackUsage(totalUnits: number, usedUnits: number): number {
  return (usedUnits / totalUnits) * 100;
}

/**
 * Validate rack unit position
 */
export function isValidRackPosition(
  startUnit: number,
  height: number,
  maxUnits: number = 42
): boolean {
  return startUnit >= 1 && startUnit + height - 1 <= maxUnits;
}

/**
 * Check if rack units overlap
 */
export function doUnitsOverlap(
  start1: number,
  height1: number,
  start2: number,
  height2: number
): boolean {
  const end1 = start1 + height1 - 1;
  const end2 = start2 + height2 - 1;
  return start1 <= end2 && end1 >= start2;
}

/**
 * Format date to relative time
 */
export function formatRelativeTime(date: string | Date): string {
  const now = new Date();
  const then = new Date(date);
  const diffMs = now.getTime() - then.getTime();
  const diffSecs = Math.floor(diffMs / 1000);
  const diffMins = Math.floor(diffSecs / 60);
  const diffHours = Math.floor(diffMins / 60);
  const diffDays = Math.floor(diffHours / 24);

  if (diffSecs < 60) return 'just now';
  if (diffMins < 60) return `${diffMins}m ago`;
  if (diffHours < 24) return `${diffHours}h ago`;
  if (diffDays < 7) return `${diffDays}d ago`;

  return then.toLocaleDateString();
}

/**
 * Generate unique ID
 */
export function generateId(): string {
  return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
}

/**
 * Debounce function
 */
export function debounce<T extends (...args: any[]) => any>(
  func: T,
  wait: number
): (...args: Parameters<T>) => void {
  let timeout: ReturnType<typeof setTimeout> | null = null;

  return function executedFunction(...args: Parameters<T>) {
    const later = () => {
      timeout = null;
      func(...args);
    };

    if (timeout) clearTimeout(timeout);
    timeout = setTimeout(later, wait);
  };
}

/**
 * Deep clone object
 */
export function deepClone<T>(obj: T): T {
  return JSON.parse(JSON.stringify(obj));
}

/**
 * Sort array by key
 */
export function sortBy<T>(array: T[], key: keyof T, direction: 'asc' | 'desc' = 'asc'): T[] {
  return [...array].sort((a, b) => {
    const aVal = a[key];
    const bVal = b[key];

    if (aVal < bVal) return direction === 'asc' ? -1 : 1;
    if (aVal > bVal) return direction === 'asc' ? 1 : -1;
    return 0;
  });
}

/**
 * Group array by key
 */
export function groupBy<T>(array: T[], key: keyof T): Record<string, T[]> {
  return array.reduce((result, item) => {
    const groupKey = String(item[key]);
    if (!result[groupKey]) {
      result[groupKey] = [];
    }
    result[groupKey].push(item);
    return result;
  }, {} as Record<string, T[]>);
}

/**
 * Truncate text with ellipsis
 */
export function truncate(text: string, maxLength: number): string {
  if (text.length <= maxLength) return text;
  return `${text.slice(0, maxLength)}...`;
}

/**
 * Check if value is empty
 */
export function isEmpty(value: any): boolean {
  if (value == null) return true;
  if (typeof value === 'string') return value.trim().length === 0;
  if (Array.isArray(value)) return value.length === 0;
  if (typeof value === 'object') return Object.keys(value).length === 0;
  return false;
}
