import React, { useState, FormEvent, ChangeEvent, useRef, KeyboardEvent } from 'react';
import { useNavigate } from 'react-router-dom';
import { authService } from '../../services/auth.service';
import { useAuth } from '../../hooks/useAuth';
import Button from '../../components/common/Button';

const Verify2FA: React.FC = () => {
  const navigate = useNavigate();
  const { completeLogin } = useAuth();
  const [codigo, setCodigo] = useState<string[]>(Array(6).fill(''));
  const [error, setError] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(false);
  const inputRefs = useRef<(HTMLInputElement | null)[]>([]);

  const handleDigitChange = (index: number, e: ChangeEvent<HTMLInputElement>): void => {
    const val = e.target.value.replace(/\D/g, '').slice(-1);
    const next = [...codigo];
    next[index] = val;
    setCodigo(next);
    if (val && index < 5) {
      inputRefs.current[index + 1]?.focus();
    }
  };

  const handleKeyDown = (index: number, e: KeyboardEvent<HTMLInputElement>): void => {
    if (e.key === 'Backspace' && !codigo[index] && index > 0) {
      inputRefs.current[index - 1]?.focus();
    }
  };

  const handlePaste = (e: React.ClipboardEvent<HTMLInputElement>): void => {
    const pasted = e.clipboardData.getData('text').replace(/\D/g, '').slice(0, 6);
    if (pasted.length > 0) {
      const next = Array(6).fill('');
      pasted.split('').forEach((ch, i) => { next[i] = ch; });
      setCodigo(next);
      const focusIdx = Math.min(pasted.length, 5);
      inputRefs.current[focusIdx]?.focus();
    }
    e.preventDefault();
  };

  const handleSubmit = async (e: FormEvent<HTMLFormElement>): Promise<void> => {
    e.preventDefault();
    const codigoCompleto = codigo.join('');
    if (codigoCompleto.length < 6) {
      setError('Ingresa los 6 dígitos del código');
      return;
    }

    setError('');
    setLoading(true);

    try {
      const result = await authService.verify2FA(codigoCompleto);
      completeLogin(result.user);
      navigate('/dashboard');
    } catch (err: any) {
      setError(
        err.response?.data?.mensaje ||
        err.message ||
        'Código inválido. Verificá tu app autenticadora.'
      );
      setCodigo(Array(6).fill(''));
      inputRefs.current[0]?.focus();
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-primary-50 to-primary-100 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        <div className="bg-white rounded-2xl shadow-2xl p-8">
          {/* Header */}
          <div className="text-center mb-8">
            <div className="mx-auto w-16 h-16 bg-primary-100 rounded-full flex items-center justify-center mb-4">
              <svg className="w-8 h-8 text-primary-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                  d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
              </svg>
            </div>
            <h1 className="text-2xl font-bold text-gray-900">Verificación en dos pasos</h1>
            <p className="mt-2 text-sm text-gray-600">
              Ingresá el código de 6 dígitos de tu app autenticadora (Google/Microsoft Authenticator).
            </p>
          </div>

          {/* Error */}
          {error && (
            <div className="mb-6 bg-red-50 border-l-4 border-red-500 p-4 rounded">
              <p className="text-red-700 text-sm">{error}</p>
            </div>
          )}

          {/* Form */}
          <form onSubmit={handleSubmit} className="space-y-6">
            <div className="flex justify-center gap-2">
              {codigo.map((digit, idx) => (
                <input
                  key={idx}
                  ref={(el) => { inputRefs.current[idx] = el; }}
                  type="text"
                  inputMode="numeric"
                  maxLength={1}
                  value={digit}
                  onChange={(e) => handleDigitChange(idx, e)}
                  onKeyDown={(e) => handleKeyDown(idx, e)}
                  onPaste={idx === 0 ? handlePaste : undefined}
                  className="w-12 h-14 text-center text-xl font-bold border-2 border-gray-300 rounded-lg
                    focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500
                    transition-colors"
                  autoFocus={idx === 0}
                />
              ))}
            </div>

            <Button
              type="submit"
              variant="primary"
              fullWidth
              isLoading={loading}
              disabled={codigo.join('').length < 6}
            >
              Verificar código
            </Button>
          </form>

          {/* Back link */}
          <div className="mt-6 text-center">
            <button
              type="button"
              onClick={() => navigate('/login')}
              className="text-sm text-gray-500 hover:text-gray-700 hover:underline"
            >
              ← Volver al inicio de sesión
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Verify2FA;
