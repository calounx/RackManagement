/**
 * Catalog Shared Components
 *
 * Reusable components for the catalog UI system (DeviceTypes, Brands, Models).
 * These components provide consistent styling, behavior, and user experience
 * across all catalog management pages.
 */

// Form Components
export { FormSection, FormGrid } from './FormSection';
export type { FormSectionProps, FormGridProps } from './FormSection';

// Dialog Components
export { ConfirmDialog } from './ConfirmDialog';
export type { ConfirmDialogProps } from './ConfirmDialog';

// Search & Filter Components
export { SearchFilterBar } from './SearchFilterBar';
export type {
  SearchFilterBarProps,
  FilterConfig,
} from './SearchFilterBar';

// Pagination Components
export { PaginationControls } from './PaginationControls';
export type { PaginationControlsProps } from './PaginationControls';

// Empty State Components
export { EmptyState, EmptySearchResults } from './EmptyState';
export type {
  EmptyStateProps,
  EmptySearchResultsProps,
} from './EmptyState';

// Stats Components
export { StatsDashboard, MiniStat } from './StatsDashboard';
export type {
  StatsDashboardProps,
  StatItem,
  MiniStatProps,
} from './StatsDashboard';
