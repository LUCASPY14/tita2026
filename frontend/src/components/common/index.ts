/**
 * Common Components - Sistema de Componentes UI
 * Exportaciones centralizadas de todos los componentes comunes
 */

// Atoms
export { default as Button } from './Button';
export type { ButtonProps } from './Button';

export { default as Input } from './Input';
export type { InputProps } from './Input';

export { default as Select } from './Select';
export type { SelectProps, SelectOption } from './Select';

export { default as Checkbox } from './Checkbox';
export type { CheckboxProps } from './Checkbox';

export { default as Badge } from './Badge';
export type { BadgeProps } from './Badge';

export { default as Avatar } from './Avatar';
export type { AvatarProps } from './Avatar';

export { default as LoadingSpinner, Spinner } from './LoadingSpinner';
export type { SpinnerProps } from './LoadingSpinner';

export { default as Textarea } from './Textarea';
export type { TextareaProps } from './Textarea';

// Molecules
export { default as Card } from './Card';
export type { CardProps } from './Card';

export { default as Modal, ModalFooter } from './Modal';
export type { ModalProps } from './Modal';

export { default as ConfirmDialog } from './ConfirmDialog';

export { default as Skeleton, SkeletonLine, SkeletonKPI } from './Skeleton';

export { default as SearchBar } from './SearchBar';
export type { SearchBarProps } from './SearchBar';

export {
  FormInput,
  FormSelect,
  FormCheckbox,
  FormTextarea,
  FormGroup,
} from './FormFields';
export type {
  FormInputProps,
  FormSelectProps,
  FormCheckboxProps,
  FormTextareaProps,
  FormGroupProps,
} from './FormFields';
