import React, { useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { AlertTriangle, Info, AlertCircle } from 'lucide-react';
import { Button } from '../../ui/button';
import { cn } from '../../../lib/utils';

export interface ConfirmDialogProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: () => void | Promise<void>;
  title: string;
  message: string;
  confirmText?: string;
  cancelText?: string;
  isLoading?: boolean;
  variant?: 'danger' | 'warning' | 'info';
}

/**
 * ConfirmDialog Component
 *
 * A reusable confirmation dialog for destructive actions and important decisions.
 * Supports keyboard shortcuts (Enter = confirm, Esc = cancel) and loading states.
 *
 * @example
 * <ConfirmDialog
 *   isOpen={showConfirm}
 *   onClose={() => setShowConfirm(false)}
 *   onConfirm={handleDelete}
 *   title="Delete Device Type?"
 *   message="This action cannot be undone. All associated models will also be removed."
 *   confirmText="Delete"
 *   variant="danger"
 * />
 */
export const ConfirmDialog: React.FC<ConfirmDialogProps> = ({
  isOpen,
  onClose,
  onConfirm,
  title,
  message,
  confirmText = 'Confirm',
  cancelText = 'Cancel',
  isLoading = false,
  variant = 'danger',
}) => {
  // Handle keyboard shortcuts
  useEffect(() => {
    if (!isOpen || isLoading) return;

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onClose();
      } else if (e.key === 'Enter' && !e.shiftKey && !e.ctrlKey && !e.metaKey) {
        e.preventDefault();
        onConfirm();
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, isLoading, onClose, onConfirm]);

  // Prevent body scroll when dialog is open
  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = 'unset';
    }
    return () => {
      document.body.style.overflow = 'unset';
    };
  }, [isOpen]);

  const variantConfig = {
    danger: {
      icon: AlertCircle,
      iconColor: 'text-red-500',
      bgColor: 'bg-red-500/10',
      borderColor: 'border-red-500/30',
      accentColor: 'border-red-500',
      buttonVariant: 'danger' as const,
    },
    warning: {
      icon: AlertTriangle,
      iconColor: 'text-amber',
      bgColor: 'bg-amber/10',
      borderColor: 'border-amber/30',
      accentColor: 'border-amber',
      buttonVariant: 'primary' as const,
    },
    info: {
      icon: Info,
      iconColor: 'text-electric',
      bgColor: 'bg-electric-blue/10',
      borderColor: 'border-electric-blue/30',
      accentColor: 'border-electric',
      buttonVariant: 'primary' as const,
    },
  };

  const config = variantConfig[variant];
  const Icon = config.icon;

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Backdrop */}
          <motion.div
            className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={isLoading ? undefined : onClose}
          />

          {/* Dialog Container */}
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
            <motion.div
              className={cn(
                'glass rounded-lg shadow-2xl w-full max-w-md',
                'border-2',
                config.borderColor
              )}
              initial={{ opacity: 0, scale: 0.95, y: 20 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95, y: 20 }}
              transition={{ type: 'spring', duration: 0.3 }}
              onClick={(e) => e.stopPropagation()}
            >
              {/* Header with Icon */}
              <div className={cn('p-6 border-l-4', config.accentColor)}>
                <div className="flex items-start gap-4">
                  {/* Icon */}
                  <div
                    className={cn(
                      'flex-shrink-0 w-12 h-12 rounded-full flex items-center justify-center',
                      config.bgColor,
                      'border',
                      config.borderColor
                    )}
                  >
                    <Icon className={cn('w-6 h-6', config.iconColor)} />
                  </div>

                  {/* Content */}
                  <div className="flex-1 min-w-0">
                    <h3 className="text-lg font-semibold text-foreground mb-2">
                      {title}
                    </h3>
                    <p className="text-sm text-muted-foreground leading-relaxed">
                      {message}
                    </p>
                  </div>
                </div>
              </div>

              {/* Footer with Actions */}
              <div className="px-6 pb-6 flex items-center justify-end gap-3">
                <Button
                  variant="ghost"
                  onClick={onClose}
                  disabled={isLoading}
                  className="min-w-[100px]"
                >
                  {cancelText}
                </Button>
                <Button
                  variant={config.buttonVariant}
                  onClick={onConfirm}
                  loading={isLoading}
                  disabled={isLoading}
                  className="min-w-[100px]"
                >
                  {confirmText}
                </Button>
              </div>

              {/* Keyboard Hint */}
              {!isLoading && (
                <div className="px-6 pb-4 flex items-center justify-center gap-4 text-xs text-muted-foreground">
                  <div className="flex items-center gap-1.5">
                    <kbd className="px-2 py-1 bg-secondary rounded border border-border font-mono">
                      Enter
                    </kbd>
                    <span>to confirm</span>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <kbd className="px-2 py-1 bg-secondary rounded border border-border font-mono">
                      Esc
                    </kbd>
                    <span>to cancel</span>
                  </div>
                </div>
              )}
            </motion.div>
          </div>
        </>
      )}
    </AnimatePresence>
  );
};
