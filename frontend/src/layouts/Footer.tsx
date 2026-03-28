import React from 'react';
import { Link } from 'react-router-dom';
import { Heart, Facebook, Instagram, Twitter, Mail, Phone, MapPin } from 'lucide-react';

const Footer: React.FC = () => {
  const currentYear = new Date().getFullYear();

  return (
    <footer className="mt-auto bg-white border-t border-gray-200">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        {/* Main Footer */}
        <div className="grid grid-cols-1 gap-8 py-8 md:grid-cols-3">
          {/* About Section */}
          <div>
            <div className="flex items-center gap-2 mb-4">
              <img 
                src="/assets/images/logo_tita.png" 
                alt="Cantina Tita" 
                className="h-10 w-10 object-contain"
                onError={(e) => {
                  e.currentTarget.style.display = 'none';
                }}
              />
              <h3 className="text-lg font-bold text-amber-600">Cantina Tita</h3>
            </div>
            <p className="text-sm text-gray-600 leading-relaxed">
              Sistema de gestión integral para cantinas escolares. Administra recargas, ventas, inventario y más de manera eficiente y profesional.
            </p>
            <div className="mt-4 flex gap-3">
              <button
                type="button"
                className="rounded-full bg-gray-100 p-2 text-gray-600 transition-colors hover:bg-amber-100 hover:text-amber-600"
                aria-label="Facebook"
              >
                <Facebook className="h-4 w-4" />
              </button>
              <button
                type="button"
                className="rounded-full bg-gray-100 p-2 text-gray-600 transition-colors hover:bg-amber-100 hover:text-amber-600"
                aria-label="Instagram"
              >
                <Instagram className="h-4 w-4" />
              </button>
              <button
                type="button"
                className="rounded-full bg-gray-100 p-2 text-gray-600 transition-colors hover:bg-amber-100 hover:text-amber-600"
                aria-label="Twitter"
              >
                <Twitter className="h-4 w-4" />
              </button>
            </div>
          </div>

          {/* Quick Links */}
          <div>
            <h3 className="mb-4 text-sm font-semibold text-gray-900 uppercase tracking-wider">
              Accesos Rápidos
            </h3>
            <ul className="space-y-2">
              {[
                { name: 'Dashboard', path: '/dashboard' },
                { name: 'Recargas', path: '/recargas' },
                { name: 'Punto de Venta', path: '/ventas' },
                { name: 'Reportes', path: '/reportes' },
                { name: 'Configuración', path: '/configuracion' },
              ].map((link) => (
                <li key={link.path}>
                  <Link
                    to={link.path}
                    className="text-sm text-gray-600 transition-colors hover:text-amber-600"
                  >
                    {link.name}
                  </Link>
                </li>
              ))}
            </ul>
          </div>

          {/* Contact Info */}
          <div>
            <h3 className="mb-4 text-sm font-semibold text-gray-900 uppercase tracking-wider">
              Contacto
            </h3>
            <ul className="space-y-3">
              <li className="flex items-start gap-3 text-sm text-gray-600">
                <MapPin className="h-5 w-5 flex-shrink-0 text-gray-400" />
                <span>Asunción, Paraguay</span>
              </li>
              <li className="flex items-center gap-3 text-sm text-gray-600">
                <Phone className="h-5 w-5 flex-shrink-0 text-gray-400" />
                <a href="tel:+595123456789" className="hover:text-amber-600">
                  +595 123 456 789
                </a>
              </li>
              <li className="flex items-center gap-3 text-sm text-gray-600">
                <Mail className="h-5 w-5 flex-shrink-0 text-gray-400" />
                <a href="mailto:info@cantinatita.com" className="hover:text-amber-600">
                  info@cantinatita.com
                </a>
              </li>
            </ul>
          </div>
        </div>

        {/* Bottom Footer */}
        <div className="border-t border-gray-200 py-4">
          <div className="flex flex-col items-center justify-between gap-4 sm:flex-row">
            <p className="text-sm text-gray-600">
              © {currentYear} Cantina Tita. Todos los derechos reservados.
            </p>
            <p className="flex items-center gap-1 text-sm text-gray-600">
              Hecho con <Heart className="h-4 w-4 text-red-500 fill-current" /> en Paraguay
            </p>
          </div>
        </div>
      </div>
    </footer>
  );
};

export default Footer;
