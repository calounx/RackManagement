import React from 'react';
import { motion } from 'framer-motion';
import { Search, X, Filter } from 'lucide-react';
import { Input } from '../../ui/input';
import { Button } from '../../ui/button';
import { Badge } from '../../ui/badge';
import { cn } from '../../../lib/utils';

export interface FilterConfig {
  id: string;
  label: string;
  value: string;
  options: Array<{ value: string; label: string }>;
}

export interface SearchFilterBarProps {
  searchValue: string;
  onSearchChange: (value: string) => void;
  searchPlaceholder?: string;
  filters?: FilterConfig[];
  onFilterChange?: (filterId: string, value: string) => void;
  onClearFilters?: () => void;
  className?: string;
}

/**
 * SearchFilterBar Component
 *
 * A comprehensive search and filter bar with support for multiple filter dropdowns.
 * Shows active filter count and provides a clear all button.
 *
 * @example
 * <SearchFilterBar
 *   searchValue={search}
 *   onSearchChange={setSearch}
 *   filters={[
 *     {
 *       id: 'brand',
 *       label: 'Brand',
 *       value: selectedBrand,
 *       options: brands.map(b => ({ value: b.id, label: b.name }))
 *     }
 *   ]}
 *   onFilterChange={handleFilterChange}
 *   onClearFilters={handleClearFilters}
 * />
 */
export const SearchFilterBar: React.FC<SearchFilterBarProps> = ({
  searchValue,
  onSearchChange,
  searchPlaceholder = 'Search...',
  filters = [],
  onFilterChange,
  onClearFilters,
  className,
}) => {
  // Count active filters (filters with non-empty values)
  const activeFilterCount = filters.filter((f) => f.value && f.value !== 'all').length;
  const hasSearch = searchValue.trim().length > 0;
  const hasActiveFilters = activeFilterCount > 0 || hasSearch;

  const handleClearAll = () => {
    onSearchChange('');
    onClearFilters?.();
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: -10 }}
      animate={{ opacity: 1, y: 0 }}
      className={cn('flex flex-col sm:flex-row gap-3', className)}
    >
      {/* Search Input */}
      <div className="flex-1 relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground pointer-events-none z-10" />
        <Input
          type="text"
          placeholder={searchPlaceholder}
          value={searchValue}
          onChange={(e) => onSearchChange(e.target.value)}
          className="pl-10 pr-10"
        />
        {hasSearch && (
          <button
            onClick={() => onSearchChange('')}
            className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground transition-colors"
            aria-label="Clear search"
          >
            <X className="w-4 h-4" />
          </button>
        )}
      </div>

      {/* Filter Dropdowns */}
      {filters.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {filters.map((filter) => (
            <div key={filter.id} className="relative">
              <select
                value={filter.value}
                onChange={(e) => onFilterChange?.(filter.id, e.target.value)}
                className={cn(
                  'pl-3 pr-8 py-2.5 rounded-md',
                  'bg-input border border-border',
                  'text-sm text-foreground',
                  'hover:border-electric-blue/50',
                  'focus:outline-none focus:ring-2 focus:ring-electric-blue/50 focus:border-electric',
                  'transition-all duration-200',
                  'appearance-none cursor-pointer',
                  'min-w-[140px]',
                  filter.value && filter.value !== 'all' && 'border-electric-blue/50 bg-electric-blue/5'
                )}
              >
                <option value="all">{filter.label}: All</option>
                {filter.options.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
              <Filter className="absolute right-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-muted-foreground pointer-events-none" />
            </div>
          ))}
        </div>
      )}

      {/* Clear All Button */}
      {hasActiveFilters && (
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          exit={{ opacity: 0, scale: 0.9 }}
        >
          <Button
            variant="ghost"
            onClick={handleClearAll}
            className="relative"
            leftIcon={<X className="w-4 h-4" />}
          >
            Clear
            {activeFilterCount > 0 && (
              <Badge
                variant="info"
                className="ml-2 px-1.5 min-w-[20px] h-5 flex items-center justify-center"
              >
                {activeFilterCount}
              </Badge>
            )}
          </Button>
        </motion.div>
      )}
    </motion.div>
  );
};
