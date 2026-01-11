import React from 'react';
import { motion } from 'framer-motion';
import type { LucideIcon } from 'lucide-react';
import { Button } from '../../ui/button';
import { cn } from '../../../lib/utils';

export interface EmptyStateProps {
  icon: LucideIcon;
  title: string;
  description: string;
  actionButton?: {
    label: string;
    onClick: () => void;
    icon?: LucideIcon;
  };
  variant?: 'no-data' | 'no-results' | 'error';
  className?: string;
}

/**
 * EmptyState Component
 *
 * A friendly empty state component for displaying when there's no data or no search results.
 * Supports different variants with appropriate styling and optional action buttons.
 *
 * @example
 * // No data yet
 * <EmptyState
 *   icon={Database}
 *   title="No device types yet"
 *   description="Get started by creating your first device type category"
 *   variant="no-data"
 *   actionButton={{
 *     label: "Add Device Type",
 *     onClick: handleCreate,
 *     icon: Plus
 *   }}
 * />
 *
 * @example
 * // No search results
 * <EmptyState
 *   icon={Search}
 *   title="No results found"
 *   description="Try adjusting your search criteria or filters"
 *   variant="no-results"
 * />
 */
export const EmptyState: React.FC<EmptyStateProps> = ({
  icon: Icon,
  title,
  description,
  actionButton,
  variant = 'no-data',
  className,
}) => {
  const variantConfig = {
    'no-data': {
      iconColor: 'text-electric',
      iconBgColor: 'bg-electric-blue/10',
      iconBorderColor: 'border-electric-blue/30',
    },
    'no-results': {
      iconColor: 'text-muted-foreground',
      iconBgColor: 'bg-secondary/50',
      iconBorderColor: 'border-border',
    },
    error: {
      iconColor: 'text-red-500',
      iconBgColor: 'bg-red-500/10',
      iconBorderColor: 'border-red-500/30',
    },
  };

  const config = variantConfig[variant];
  const ActionIcon = actionButton?.icon;

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.3 }}
      className={cn('flex flex-col items-center justify-center py-12 px-4', className)}
    >
      {/* Icon */}
      <motion.div
        initial={{ scale: 0 }}
        animate={{ scale: 1 }}
        transition={{ delay: 0.1, type: 'spring', stiffness: 200 }}
        className={cn(
          'w-20 h-20 rounded-2xl flex items-center justify-center mb-6',
          'border-2',
          config.iconBgColor,
          config.iconBorderColor
        )}
      >
        <Icon className={cn('w-10 h-10', config.iconColor)} />
      </motion.div>

      {/* Content */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
        className="text-center max-w-md"
      >
        <h3 className="text-lg font-semibold text-foreground mb-2">{title}</h3>
        <p className="text-sm text-muted-foreground leading-relaxed mb-6">
          {description}
        </p>

        {/* Action Button */}
        {actionButton && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
          >
            <Button
              variant="primary"
              onClick={actionButton.onClick}
              leftIcon={ActionIcon ? <ActionIcon className="w-4 h-4" /> : undefined}
            >
              {actionButton.label}
            </Button>
          </motion.div>
        )}
      </motion.div>

      {/* Decorative Elements */}
      <div className="absolute inset-0 pointer-events-none overflow-hidden -z-10">
        <motion.div
          className={cn(
            'absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2',
            'w-[400px] h-[400px] rounded-full blur-3xl opacity-10',
            config.iconBgColor
          )}
          initial={{ scale: 0.8, opacity: 0 }}
          animate={{ scale: 1, opacity: 0.1 }}
          transition={{ duration: 1, delay: 0.2 }}
        />
      </div>
    </motion.div>
  );
};

export interface EmptySearchResultsProps {
  searchQuery: string;
  onClearSearch: () => void;
  className?: string;
}

/**
 * EmptySearchResults Component
 *
 * A specialized empty state component specifically for search results.
 * Displays the search query and provides a button to clear the search.
 *
 * @example
 * <EmptySearchResults
 *   searchQuery={searchQuery}
 *   onClearSearch={() => setSearchQuery('')}
 * />
 */
export const EmptySearchResults: React.FC<EmptySearchResultsProps> = ({
  searchQuery,
  onClearSearch,
  className,
}) => {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className={cn('text-center py-12', className)}
    >
      <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-secondary/50 border border-border mb-4">
        <svg
          className="w-8 h-8 text-muted-foreground"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
          />
        </svg>
      </div>

      <h3 className="text-lg font-medium text-foreground mb-2">No results found</h3>
      <p className="text-sm text-muted-foreground mb-4">
        No results found for{' '}
        <span className="font-medium text-foreground">"{searchQuery}"</span>
      </p>

      <Button variant="ghost" onClick={onClearSearch} size="sm">
        Clear search
      </Button>
    </motion.div>
  );
};
