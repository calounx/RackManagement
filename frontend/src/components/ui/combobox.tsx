import React, { useState, useRef, useEffect } from 'react';
import { cn } from '../../lib/utils';
import { Check, ChevronDown } from 'lucide-react';

export interface ComboboxOption {
  value: string;
  label: string;
}

export interface ComboboxProps {
  label?: string;
  value: string;
  onChange: (value: string) => void;
  options: ComboboxOption[];
  placeholder?: string;
  error?: string;
  disabled?: boolean;
  allowCustom?: boolean;
  className?: string;
}

export const Combobox: React.FC<ComboboxProps> = ({
  label,
  value,
  onChange,
  options,
  placeholder = 'Search or select...',
  error,
  disabled = false,
  allowCustom = true,
  className,
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [inputValue, setInputValue] = useState(value);
  const [filteredOptions, setFilteredOptions] = useState<ComboboxOption[]>(options);
  const containerRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Update input value when value prop changes
  useEffect(() => {
    setInputValue(value);
  }, [value]);

  // Filter options based on input
  useEffect(() => {
    if (!inputValue) {
      setFilteredOptions(options);
    } else {
      const filtered = options.filter((option) =>
        option.label.toLowerCase().includes(inputValue.toLowerCase()) ||
        option.value.toLowerCase().includes(inputValue.toLowerCase())
      );
      setFilteredOptions(filtered);
    }
  }, [inputValue, options]);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setIsOpen(false);
        // If not allowing custom input and input doesn't match an option, reset
        if (!allowCustom && !options.find(opt => opt.value === inputValue)) {
          setInputValue(value);
        }
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [allowCustom, inputValue, options, value]);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newValue = e.target.value;
    setInputValue(newValue);
    setIsOpen(true);

    // If allowing custom input, update parent immediately
    if (allowCustom) {
      onChange(newValue);
    }
  };

  const handleOptionSelect = (option: ComboboxOption) => {
    setInputValue(option.value);
    onChange(option.value);
    setIsOpen(false);
    inputRef.current?.blur();
  };

  const handleInputFocus = () => {
    setIsOpen(true);
  };

  const handleInputBlur = () => {
    // Delay to allow option click to register
    setTimeout(() => {
      if (allowCustom) {
        onChange(inputValue);
      } else {
        // If not allowing custom and no match, reset to original value
        const matchingOption = options.find(opt => opt.value === inputValue);
        if (!matchingOption) {
          setInputValue(value);
        }
      }
    }, 200);
  };

  const showDropdownIcon = !disabled && options.length > 0;

  return (
    <div className={cn('w-full', className)} ref={containerRef}>
      {label && (
        <label className="block text-sm font-medium text-foreground mb-2">
          {label}
        </label>
      )}
      <div className="relative">
        <input
          ref={inputRef}
          type="text"
          value={inputValue}
          onChange={handleInputChange}
          onFocus={handleInputFocus}
          onBlur={handleInputBlur}
          placeholder={placeholder}
          disabled={disabled}
          className={cn(
            'w-full rounded-md border bg-input px-4 py-2.5',
            'text-foreground placeholder:text-muted-foreground',
            'transition-all duration-200',
            'focus:outline-none focus:ring-2 focus:ring-electric-blue/50 focus:border-electric',
            'disabled:opacity-50 disabled:cursor-not-allowed',
            error && 'border-red-500 focus:ring-red-500/50 focus:border-red-500',
            !error && 'border-border',
            showDropdownIcon && 'pr-10'
          )}
        />
        {showDropdownIcon && (
          <button
            type="button"
            onClick={() => !disabled && setIsOpen(!isOpen)}
            className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground transition-colors"
            tabIndex={-1}
          >
            <ChevronDown
              className={cn(
                'w-4 h-4 transition-transform duration-200',
                isOpen && 'rotate-180'
              )}
            />
          </button>
        )}
      </div>

      {/* Dropdown */}
      {isOpen && filteredOptions.length > 0 && (
        <div className="absolute z-50 w-full mt-1 bg-secondary border border-border rounded-lg shadow-lg max-h-60 overflow-y-auto">
          {filteredOptions.map((option) => {
            const isSelected = value === option.value;
            return (
              <button
                key={option.value}
                type="button"
                onClick={() => handleOptionSelect(option)}
                className={cn(
                  'w-full px-4 py-2.5 text-left text-sm transition-colors',
                  'hover:bg-electric/10 hover:text-electric',
                  'flex items-center justify-between gap-2',
                  isSelected && 'bg-electric/5 text-electric font-medium'
                )}
              >
                <span>{option.label}</span>
                {isSelected && <Check className="w-4 h-4 flex-shrink-0" />}
              </button>
            );
          })}
        </div>
      )}

      {/* No results message */}
      {isOpen && filteredOptions.length === 0 && inputValue && (
        <div className="absolute z-50 w-full mt-1 bg-secondary border border-border rounded-lg shadow-lg p-4 text-center">
          <p className="text-sm text-muted-foreground">
            {allowCustom ? (
              <>Press Enter to use "<span className="text-foreground font-medium">{inputValue}</span>"</>
            ) : (
              'No matching options found'
            )}
          </p>
        </div>
      )}

      {error && (
        <p className="mt-1.5 text-sm text-red-500">{error}</p>
      )}
    </div>
  );
};
