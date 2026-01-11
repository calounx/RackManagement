import React from 'react';
import { motion } from 'framer-motion';
import { cn } from '../../../lib/utils';

export interface FormSectionProps {
  title: string;
  description?: string;
  children: React.ReactNode;
  accentColor?: string;
  className?: string;
}

/**
 * FormSection Component
 *
 * A wrapper for form sections with consistent styling across catalog dialogs.
 * Features an electric blue indicator bar, section header, and grid layout support.
 *
 * @example
 * <FormSection title="Basic Information" description="Enter the core details">
 *   <Input label="Name" />
 *   <Input label="Slug" />
 * </FormSection>
 */
export const FormSection: React.FC<FormSectionProps> = ({
  title,
  description,
  children,
  accentColor = 'rgb(0, 234, 255)',
  className,
}) => {
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.2 }}
      className={cn('space-y-4', className)}
    >
      {/* Section Header */}
      <div className="flex items-center gap-2 pb-2 border-b border-border/50">
        <div
          className="w-1 h-5 rounded-full"
          style={{ backgroundColor: accentColor }}
        />
        <div className="flex-1">
          <h3 className="text-sm font-semibold text-foreground uppercase tracking-wide">
            {title}
          </h3>
          {description && (
            <p className="text-xs text-muted-foreground mt-0.5">
              {description}
            </p>
          )}
        </div>
      </div>

      {/* Section Content */}
      <div className="space-y-4">
        {children}
      </div>
    </motion.div>
  );
};

export interface FormGridProps {
  columns?: 1 | 2 | 3;
  children: React.ReactNode;
  className?: string;
}

/**
 * FormGrid Component
 *
 * Helper component for creating responsive grid layouts within form sections.
 *
 * @example
 * <FormGrid columns={2}>
 *   <Input label="First Name" />
 *   <Input label="Last Name" />
 * </FormGrid>
 */
export const FormGrid: React.FC<FormGridProps> = ({
  columns = 2,
  children,
  className,
}) => {
  const gridClasses = {
    1: 'grid-cols-1',
    2: 'grid-cols-1 md:grid-cols-2',
    3: 'grid-cols-1 md:grid-cols-2 lg:grid-cols-3',
  };

  return (
    <div className={cn('grid gap-4', gridClasses[columns], className)}>
      {children}
    </div>
  );
};
