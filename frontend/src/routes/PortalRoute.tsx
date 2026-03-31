import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { usePortalAuth } from '../contexts/PortalAuthContext';
import LoadingSpinner from '../components/common/LoadingSpinner';

interface PortalRouteProps {
  children: React.ReactNode;
}

const PortalRoute: React.FC<PortalRouteProps> = ({ children }) => {
  const { isAuthenticated, isLoading } = usePortalAuth();
  const location = useLocation();

  if (isLoading) {
    return (
      <div className="flex h-screen items-center justify-center">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/portal/login" state={{ from: location.pathname }} replace />;
  }

  return <>{children}</>;
};

export default PortalRoute;
