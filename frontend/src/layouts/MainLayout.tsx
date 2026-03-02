import React from 'react';
import { useUIStore } from '../store/uiStore';
import Sidebar from './Sidebar';
import Header from './Header';
import Breadcrumbs from './Breadcrumbs';
import Footer from './Footer';
import clsx from 'clsx';

interface MainLayoutProps {
  children: React.ReactNode;
}

const MainLayout: React.FC<MainLayoutProps> = ({ children }) => {
  const { sidebarOpen } = useUIStore();

  return (
    <div className="flex h-screen overflow-hidden bg-gray-50">
      {/* Sidebar */}
      <Sidebar />

      {/* Main Content Area */}
      <div className="flex flex-1 flex-col overflow-hidden">
        {/* Header */}
        <Header />

        {/* Content with Breadcrumbs and Footer */}
        <div className="flex flex-1 flex-col overflow-y-auto">
          {/* Breadcrumbs */}
          <Breadcrumbs />

          {/* Main Content */}
          <main
            className={clsx(
              'flex-1 transition-all duration-300',
              sidebarOpen ? 'lg:ml-0' : 'lg:ml-0'
            )}
          >
            <div className="mx-auto px-4 py-6 sm:px-6 lg:px-8">
              {children}
            </div>
          </main>

          {/* Footer */}
          <Footer />
        </div>
      </div>
    </div>
  );
};

export default MainLayout;
