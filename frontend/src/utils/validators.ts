export const validateEmail = (email: string): boolean => {
  const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return re.test(email);
};

export const validateRUC = (ruc: string): boolean => {
  const re = /^\d{6,8}-\d{1}$/;
  return re.test(ruc);
};

export const validateCI = (ci: string): boolean => {
  const cleaned = ci.replace(/\./g, '');
  return /^\d{6,8}$/.test(cleaned);
};

export const validatePhone = (phone: string): boolean => {
  const cleaned = phone.replace(/[\s-]/g, '');
  return /^09\d{8}$/.test(cleaned);
};

export const isRequired = (value: string | null | undefined): boolean => {
  return value !== null && value !== undefined && value !== '';
};

export interface ValidationRule {
  validate: (value: any) => boolean;
  message: string;
}

export const createValidator = (rules: ValidationRule[]) => {
  return (value: any): string | undefined => {
    for (const rule of rules) {
      if (!rule.validate(value)) {
        return rule.message;
      }
    }
    return undefined;
  };
};
