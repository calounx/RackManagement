import React from 'react';
import { motion } from 'framer-motion';
import { ChevronLeft, ChevronRight, ChevronsLeft, ChevronsRight } from 'lucide-react';
import { Button } from '../../ui/button';
import { cn } from '../../../lib/utils';

export interface PaginationControlsProps {
  currentPage: number;
  totalPages: number;
  totalItems: number;
  pageSize: number;
  onPageChange: (page: number) => void;
  className?: string;
  showPageNumbers?: boolean;
  maxPageButtons?: number;
}

/**
 * PaginationControls Component
 *
 * Standardized pagination with page numbers, navigation buttons, and result counter.
 * Supports ellipsis for large page sets and boundary navigation.
 *
 * @example
 * <PaginationControls
 *   currentPage={page}
 *   totalPages={20}
 *   totalItems={500}
 *   pageSize={25}
 *   onPageChange={setPage}
 * />
 */
export const PaginationControls: React.FC<PaginationControlsProps> = ({
  currentPage,
  totalPages,
  totalItems,
  pageSize,
  onPageChange,
  className,
  showPageNumbers = true,
  maxPageButtons = 7,
}) => {
  const startItem = (currentPage - 1) * pageSize + 1;
  const endItem = Math.min(currentPage * pageSize, totalItems);

  // Generate page number buttons with ellipsis
  const getPageNumbers = (): (number | 'ellipsis')[] => {
    if (totalPages <= maxPageButtons) {
      return Array.from({ length: totalPages }, (_, i) => i + 1);
    }

    const pages: (number | 'ellipsis')[] = [];
    const halfMax = Math.floor(maxPageButtons / 2);

    // Always show first page
    pages.push(1);

    let startPage = Math.max(2, currentPage - halfMax);
    let endPage = Math.min(totalPages - 1, currentPage + halfMax);

    // Adjust if we're near the start or end
    if (currentPage <= halfMax + 1) {
      endPage = Math.min(totalPages - 1, maxPageButtons - 1);
    }
    if (currentPage >= totalPages - halfMax) {
      startPage = Math.max(2, totalPages - maxPageButtons + 2);
    }

    // Add ellipsis after first page if needed
    if (startPage > 2) {
      pages.push('ellipsis');
    }

    // Add page numbers
    for (let i = startPage; i <= endPage; i++) {
      pages.push(i);
    }

    // Add ellipsis before last page if needed
    if (endPage < totalPages - 1) {
      pages.push('ellipsis');
    }

    // Always show last page
    if (totalPages > 1) {
      pages.push(totalPages);
    }

    return pages;
  };

  const pageNumbers = getPageNumbers();

  if (totalPages <= 1) {
    return (
      <div className={cn('flex items-center justify-center text-sm text-muted-foreground', className)}>
        Showing {totalItems} {totalItems === 1 ? 'result' : 'results'}
      </div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className={cn('flex flex-col sm:flex-row items-center justify-between gap-4', className)}
    >
      {/* Results Counter */}
      <div className="text-sm text-muted-foreground font-medium">
        Showing{' '}
        <span className="text-foreground font-mono">
          {startItem}-{endItem}
        </span>{' '}
        of{' '}
        <span className="text-foreground font-mono">{totalItems}</span>{' '}
        results
      </div>

      {/* Pagination Controls */}
      <div className="flex items-center gap-2">
        {/* First Page */}
        <Button
          variant="ghost"
          size="sm"
          onClick={() => onPageChange(1)}
          disabled={currentPage === 1}
          className="hidden sm:flex"
          aria-label="First page"
        >
          <ChevronsLeft className="w-4 h-4" />
        </Button>

        {/* Previous Page */}
        <Button
          variant="ghost"
          size="sm"
          onClick={() => onPageChange(currentPage - 1)}
          disabled={currentPage === 1}
          leftIcon={<ChevronLeft className="w-4 h-4" />}
          aria-label="Previous page"
        >
          <span className="hidden sm:inline">Previous</span>
        </Button>

        {/* Page Numbers */}
        {showPageNumbers && (
          <div className="flex items-center gap-1">
            {pageNumbers.map((page, index) =>
              page === 'ellipsis' ? (
                <div
                  key={`ellipsis-${index}`}
                  className="px-2 text-muted-foreground"
                >
                  ...
                </div>
              ) : (
                <button
                  key={page}
                  onClick={() => onPageChange(page)}
                  disabled={page === currentPage}
                  className={cn(
                    'min-w-[36px] h-9 px-3 rounded-md font-medium text-sm',
                    'transition-all duration-200',
                    'focus:outline-none focus:ring-2 focus:ring-electric-blue/50',
                    page === currentPage
                      ? 'bg-electric text-slate-dark shadow-lg shadow-electric-blue/20'
                      : 'bg-secondary/50 text-foreground hover:bg-secondary hover:text-foreground'
                  )}
                  aria-label={`Page ${page}`}
                  aria-current={page === currentPage ? 'page' : undefined}
                >
                  {page}
                </button>
              )
            )}
          </div>
        )}

        {/* Next Page */}
        <Button
          variant="ghost"
          size="sm"
          onClick={() => onPageChange(currentPage + 1)}
          disabled={currentPage === totalPages}
          rightIcon={<ChevronRight className="w-4 h-4" />}
          aria-label="Next page"
        >
          <span className="hidden sm:inline">Next</span>
        </Button>

        {/* Last Page */}
        <Button
          variant="ghost"
          size="sm"
          onClick={() => onPageChange(totalPages)}
          disabled={currentPage === totalPages}
          className="hidden sm:flex"
          aria-label="Last page"
        >
          <ChevronsRight className="w-4 h-4" />
        </Button>
      </div>
    </motion.div>
  );
};
