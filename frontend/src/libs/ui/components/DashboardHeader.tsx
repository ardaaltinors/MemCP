import React, { useState, useEffect } from 'react';
import { getCurrentUser } from '@libs/api';
import type { User } from '@libs/types';
import { authUtils } from '@libs/utils/auth';
import { Logo } from '@static/images';

interface DashboardHeaderProps {
  title?: string;
  showNavigation?: boolean;
  currentPage?: 'dashboard' | 'credentials';
}

export const DashboardHeader: React.FC<DashboardHeaderProps> = ({ 
  title, 
  showNavigation = true,
  currentPage = 'dashboard'
}) => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [showLogoutPopup, setShowLogoutPopup] = useState(false);

  const fetchUser = async () => {
    try {
      const token = authUtils.getToken();
      if (!token) return;

      const userData = await getCurrentUser(token);
      setUser(userData);
    } catch (error) {
      console.error('Failed to fetch user:', error);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchUser();
  }, []);

  const handleLogout = () => {
    authUtils.clearAuth();
    window.location.href = '/';
  };

  const getFirstName = (username: string): string => {
    return username.charAt(0).toUpperCase() + username.slice(1);
  };

  const getInitials = (username: string): string => {
    return username.charAt(0).toUpperCase();
  };

  const getPageTitle = (): string => {
    if (title) return title;
    
    if (currentPage === 'credentials') {
      return 'API Keys & Connection Management';
    }
    
    if (user && currentPage === 'dashboard') {
      return `${getFirstName(user.username)}'s Memory Space`;
    }
    
    return 'Dashboard';
  };

  return (
    <>
      {/* Custom Dashboard Header */}
      <div className="fixed top-0 left-0 right-0 z-20 bg-[#0D0D1A]/95 backdrop-blur-xl border-b border-gray-800/50 header-glow">
        <div className="h-16 md:h-20 lg:h-24 px-4 md:px-6 flex items-center justify-between">
          {/* Left: Logo */}
          <a href="/" className="flex items-center space-x-2 md:space-x-3 flex-shrink-0">
            <img 
              src={Logo.src} 
              alt="MemCP" 
              className="w-8 h-8 md:w-10 md:h-10 rounded-lg md:rounded-xl"
            />
            <span className="text-white font-semibold text-base md:text-lg">MemCP</span>
          </a>

          {/* Center: Page Title - Hidden on small screens */}
          <h1 className="hidden md:block absolute left-1/2 transform -translate-x-1/2 text-lg lg:text-2xl font-medium text-white text-center max-w-xs lg:max-w-md truncate">
            {getPageTitle()}
          </h1>

          {/* Mobile Page Title - Only visible on small screens */}
          <h1 className="md:hidden flex-1 text-center text-sm font-medium text-white truncate px-4">
            {getPageTitle().replace("'s Memory Space", "").replace(" & Connection Management", "")}
          </h1>

          {/* Right: Actions */}
          <div className="flex items-center space-x-2 md:space-x-4 lg:space-x-6 flex-shrink-0">
            {showNavigation && (
              <>
                {currentPage === 'dashboard' ? (
                  // API Key Button (when on dashboard)
                  <a 
                    href="/credentials" 
                    className="flex items-center space-x-1 md:space-x-2 px-2 md:px-4 py-2 rounded-lg bg-gray-800/50 hover:bg-gray-800 transition-colors group"
                  >
                    <svg className="w-4 h-4 md:w-5 md:h-5 text-gray-400 group-hover:text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 7a2 2 0 012 2m4 0a6 6 0 01-7.743 5.743L11 17H9v2H7v2H4a1 1 0 01-1-1v-2.586a1 1 0 01.293-.707l5.964-5.964A6 6 0 1721 9z" />
                    </svg>
                    <span className="hidden sm:inline text-gray-300 text-xs md:text-sm font-medium">API Key</span>
                  </a>
                ) : (
                  // Dashboard Button (when on credentials)
                  <a 
                    href="/dashboard" 
                    className="flex items-center space-x-1 md:space-x-2 px-2 md:px-4 py-2 rounded-lg bg-gray-800/50 hover:bg-gray-800 transition-colors group"
                  >
                    <svg className="w-4 h-4 md:w-5 md:h-5 text-gray-400 group-hover:text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 5a1 1 0 011-1h14a1 1 0 011 1v2a1 1 0 01-1 1H5a1 1 0 01-1-1V5zM4 13a1 1 0 011-1h6a1 1 0 011 1v6a1 1 0 01-1 1H5a1 1 0 01-1-1v-6zM16 13a1 1 0 011-1h2a1 1 0 011 1v6a1 1 0 01-1 1h-2a1 1 0 01-1-1v-6z" />
                    </svg>
                    <span className="hidden sm:inline text-gray-300 text-xs md:text-sm font-medium">Dashboard</span>
                  </a>
                )}
              </>
            )}

            {/* Profile/Avatar with User Initial */}
            <div className="relative">
              <button 
                onClick={() => setShowLogoutPopup(!showLogoutPopup)}
                className="w-8 h-8 md:w-10 md:h-10 rounded-full bg-gradient-to-br from-purple-500 to-blue-600 flex items-center justify-center hover:scale-105 transition-transform"
                title={user ? `${getFirstName(user.username)} - Click for options` : 'Profile'}
              >
                <span className="text-white font-semibold text-sm md:text-base">
                  {isLoading ? '•' : user ? getInitials(user.username) : 'U'}
                </span>
              </button>

              {/* Logout Popup */}
              {showLogoutPopup && (
                <div className="absolute right-0 top-10 md:top-12 w-44 md:w-48 bg-gray-900 border border-gray-700 rounded-lg shadow-xl overflow-hidden z-30">
                  {user && (
                    <div className="p-3 md:p-4 border-b border-gray-700">
                      <p className="text-white font-medium text-sm md:text-base truncate">{getFirstName(user.username)}</p>
                      <p className="text-gray-400 text-xs md:text-sm truncate">{user.email}</p>
                    </div>
                  )}
                  <button
                    onClick={handleLogout}
                    className="w-full px-3 md:px-4 py-2 md:py-3 text-left text-red-400 hover:bg-gray-800 transition-colors flex items-center space-x-2"
                  >
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
                    </svg>
                    <span className="text-sm md:text-base">Logout</span>
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Click outside to close popup */}
      {showLogoutPopup && (
        <div 
          className="fixed inset-0 z-10"
          onClick={() => setShowLogoutPopup(false)}
        />
      )}

    </>
  );
};