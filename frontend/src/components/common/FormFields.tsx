import React from 'react';
import Input, { InputProps } from './Input';
import Select, { SelectProps } from './Select';
import Checkbox, { CheckboxProps } from './Checkbox';
import Textarea, { TextareaProps } from './Textarea';

/**
 * FormField - Wrapper componente que agrega funcionalidad de formulario
 * Compatible con react-hook-form
 */

type BaseFieldProps = {
  name: string;
  label?: string;
  error?: string;
  helperText?: string;
  required?: boolean;
};

// Input Field
export interface FormInputProps extends Omit<InputProps, 'name'>, BaseFieldProps {}

export const FormInput: React.FC<FormInputProps> = (props) => {
  return <Input {...props} />;
};

// Select Field
export interface FormSelectProps extends Omit<SelectProps, 'name'>, BaseFieldProps {}

export const FormSelect: React.FC<FormSelectProps> = (props) => {
  return <Select {...props} />;
};

// Checkbox Field
export interface FormCheckboxProps extends Omit<CheckboxProps, 'name'>, BaseFieldProps {}

export const FormCheckbox: React.FC<FormCheckboxProps> = (props) => {
  return <Checkbox {...props} />;
};

// Textarea Field
export interface FormTextareaProps extends Omit<TextareaProps, 'name'>, BaseFieldProps {}

export const FormTextarea: React.FC<FormTextareaProps> = (props) => {
  return <Textarea {...props} />;
};

// FormGroup - Agrupa múltiples campos con label común
export interface FormGroupProps {
  children: React.ReactNode;
  label?: string;
  helperText?: string;
  error?: string;
  required?: boolean;
  className?: string;
}

export const FormGroup: React.FC<FormGroupProps> = ({
  children,
  label,
  helperText,
  error,
  required,
  className = '',
}) => {
  return (
    <div className={`space-y-2 ${className}`}>
      {label && (
        <label className="block text-sm font-medium text-gray-700">
          {label}
          {required && <span className="text-red-500 ml-1">*</span>}
        </label>
      )}
      {children}
      {error && (
        <p className="text-sm text-red-600 flex items-center gap-1">
          <svg className="h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
          </svg>
          {error}
        </p>
      )}
      {helperText && !error && (
        <p className="text-sm text-gray-500">{helperText}</p>
      )}
    </div>
  );
};
