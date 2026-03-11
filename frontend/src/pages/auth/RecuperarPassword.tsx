import React, { useState, FormEvent, ChangeEvent, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { authService } from '../../services/auth.service';
import Button from '../../components/common/Button';
import Input from '../../components/common/Input';

type Step = 'solicitar' | 'enviado' | 'restablecer' | 'exito';

const RecuperarPassword: React.FC = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const tokenParam = searchParams.get('token');

  const [step, setStep] = useState<Step>(tokenParam ? 'restablecer' : 'solicitar');
  const [email, setEmail] = useState('');
  const [token] = useState(tokenParam || '');
  const [nuevaPassword, setNuevaPassword] = useState('');
  const [confirmarPassword, setConfirmarPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  // Validar token si viene en la URL
  useEffect(() => {
    if (tokenParam) {
      authService.validarTokenRecuperacion(tokenParam).then((valido) => {
        if (!valido) {
          setError('El enlace de recuperación es inválido o ha expirado.');
          setStep('solicitar');
        }
      });
    }
  }, [tokenParam]);

  const handleSolicitar = async (e: FormEvent) => {
    e.preventDefault();
    if (!email) { setError('Ingresá tu email'); return; }
    setError('');
    setLoading(true);
    try {
      await authService.solicitarRecuperacion(email);
      setStep('enviado');
    } catch (err: any) {
      setError(err.response?.data?.mensaje || err.message || 'Error al enviar el email');
    } finally {
      setLoading(false);
    }
  };

  const handleRestablecer = async (e: FormEvent) => {
    e.preventDefault();
    if (!nuevaPassword || !confirmarPassword) {
      setError('Completá ambos campos'); return;
    }
    if (nuevaPassword !== confirmarPassword) {
      setError('Las contraseñas no coinciden'); return;
    }
    if (nuevaPassword.length < 8) {
      setError('La contraseña debe tener al menos 8 caracteres'); return;
    }
    setError('');
    setLoading(true);
    try {
      await authService.restablecerPassword(token, nuevaPassword);
      setStep('exito');
    } catch (err: any) {
      setError(err.response?.data?.mensaje || err.message || 'Error al restablecer la contraseña');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-primary-50 to-primary-100 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        <div className="bg-white rounded-2xl shadow-2xl p-8">

          {/* PASO 1 — Pedir email */}
          {step === 'solicitar' && (
            <>
              <div className="text-center mb-8">
                <h1 className="text-2xl font-bold text-gray-900">Recuperar contraseña</h1>
                <p className="mt-2 text-sm text-gray-600">
                  Ingresá tu email y te enviaremos un enlace para restablecer tu contraseña.
                </p>
              </div>

              {error && (
                <div className="mb-6 bg-red-50 border-l-4 border-red-500 p-4 rounded">
                  <p className="text-red-700 text-sm">{error}</p>
                </div>
              )}

              <form onSubmit={handleSolicitar} className="space-y-6">
                <Input
                  label="Email"
                  type="email"
                  value={email}
                  onChange={(e: ChangeEvent<HTMLInputElement>) => setEmail(e.target.value)}
                  required
                  placeholder="tu@email.com"
                />
                <Button type="submit" variant="primary" fullWidth isLoading={loading}>
                  Enviar enlace
                </Button>
              </form>
            </>
          )}

          {/* PASO 2 — Email enviado */}
          {step === 'enviado' && (
            <div className="text-center space-y-4">
              <div className="mx-auto w-16 h-16 bg-green-100 rounded-full flex items-center justify-center">
                <svg className="w-8 h-8 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                </svg>
              </div>
              <h2 className="text-xl font-bold text-gray-900">Revisá tu email</h2>
              <p className="text-sm text-gray-600">
                Si el email <strong>{email}</strong> está registrado en el sistema, recibirás un enlace para restablecer tu contraseña en los próximos minutos.
              </p>
              <p className="text-xs text-gray-400">
                El enlace vence en 2 horas.
              </p>
            </div>
          )}

          {/* PASO 3 — Nueva contraseña */}
          {step === 'restablecer' && (
            <>
              <div className="text-center mb-8">
                <h1 className="text-2xl font-bold text-gray-900">Nueva contraseña</h1>
                <p className="mt-2 text-sm text-gray-600">
                  Elegí una contraseña segura de al menos 8 caracteres.
                </p>
              </div>

              {error && (
                <div className="mb-6 bg-red-50 border-l-4 border-red-500 p-4 rounded">
                  <p className="text-red-700 text-sm">{error}</p>
                </div>
              )}

              <form onSubmit={handleRestablecer} className="space-y-6">
                <Input
                  label="Nueva contraseña"
                  type="password"
                  value={nuevaPassword}
                  onChange={(e: ChangeEvent<HTMLInputElement>) => setNuevaPassword(e.target.value)}
                  required
                  placeholder="Mínimo 8 caracteres"
                />
                <Input
                  label="Confirmar contraseña"
                  type="password"
                  value={confirmarPassword}
                  onChange={(e: ChangeEvent<HTMLInputElement>) => setConfirmarPassword(e.target.value)}
                  required
                  placeholder="Repetí la contraseña"
                />
                <Button type="submit" variant="primary" fullWidth isLoading={loading}>
                  Restablecer contraseña
                </Button>
              </form>
            </>
          )}

          {/* PASO 4 — Éxito */}
          {step === 'exito' && (
            <div className="text-center space-y-4">
              <div className="mx-auto w-16 h-16 bg-green-100 rounded-full flex items-center justify-center">
                <svg className="w-8 h-8 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
              </div>
              <h2 className="text-xl font-bold text-gray-900">¡Contraseña restablecida!</h2>
              <p className="text-sm text-gray-600">
                Tu contraseña fue actualizada exitosamente. Ya podés iniciar sesión.
              </p>
              <Button variant="primary" fullWidth onClick={() => navigate('/login')}>
                Ir al inicio de sesión
              </Button>
            </div>
          )}

          {/* Back link (en pasos 1 y 3) */}
          {(step === 'solicitar' || step === 'enviado') && (
            <div className="mt-6 text-center">
              <button
                type="button"
                onClick={() => navigate('/login')}
                className="text-sm text-gray-500 hover:text-gray-700 hover:underline"
              >
                ← Volver al inicio de sesión
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default RecuperarPassword;
