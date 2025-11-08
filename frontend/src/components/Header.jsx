import React, { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { useLanguage } from '../contexts/LanguageContext';
import { t } from '../translations';
import { Button } from './ui/button';
import { Globe, Menu, X } from 'lucide-react';

const Header = () => {
  const { language, toggleLanguage } = useLanguage();
  const location = useLocation();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const navItems = [
    { path: '/', label: t(language, 'home') },
    { path: '/services', label: t(language, 'services') },
    { path: '/about', label: t(language, 'about') },
    { path: '/documents', label: t(language, 'documents') },
    { path: '/forensic-analysis', label: language === 'de' ? 'Forensik' : 'Forensics' },
    { path: '/faq', label: t(language, 'faq') },
    { path: '/portal', label: language === 'de' ? 'Portal' : 'Portal' },
  ];

  const isActive = (path) => location.pathname === path;

  return (
    <header className="sticky top-0 z-50 w-full border-b bg-white/95 backdrop-blur supports-[backdrop-filter]:bg-white/80">
      <div className="container mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex h-16 items-center justify-between">
          {/* Logo */}
          <Link to="/" className="flex items-center space-x-2">
            <div className="flex items-center space-x-2">
              <div className="w-10 h-10 bg-gradient-to-br from-blue-600 to-blue-800 rounded-lg flex items-center justify-center">
                <span className="text-white font-bold text-xl">SC</span>
              </div>
              <div className="flex flex-col">
                <span className="font-bold text-lg leading-tight text-gray-900">SafeChild</span>
                <span className="text-xs text-gray-600">
                  {language === 'de' ? 'Rechtsanwaltskanzlei' : 'Law Firm'}
                </span>
              </div>
            </div>
          </Link>

          {/* Desktop Navigation */}
          <nav className="hidden md:flex items-center space-x-8">
            {navItems.map((item) => (
              <Link
                key={item.path}
                to={item.path}
                className={`text-sm font-medium transition-colors hover:text-blue-600 ${
                  isActive(item.path)
                    ? 'text-blue-600 border-b-2 border-blue-600 pb-1'
                    : 'text-gray-700'
                }`}
              >
                {item.label}
              </Link>
            ))}
          </nav>

          {/* Language Toggle & CTA */}
          <div className="hidden md:flex items-center space-x-4">
            <Button
              variant="ghost"
              size="sm"
              onClick={toggleLanguage}
              className="flex items-center space-x-2"
            >
              <Globe className="w-4 h-4" />
              <span className="font-semibold">{language.toUpperCase()}</span>
            </Button>
            <a href="mailto:info@safechild.mom">
              <Button className="bg-blue-600 hover:bg-blue-700">
                {t(language, 'contact')}
              </Button>
            </a>
          </div>

          {/* Mobile Menu Button */}
          <button
            className="md:hidden p-2"
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
          >
            {mobileMenuOpen ? (
              <X className="w-6 h-6" />
            ) : (
              <Menu className="w-6 h-6" />
            )}
          </button>
        </div>

        {/* Mobile Menu */}
        {mobileMenuOpen && (
          <div className="md:hidden py-4 border-t">
            <nav className="flex flex-col space-y-4">
              {navItems.map((item) => (
                <Link
                  key={item.path}
                  to={item.path}
                  className={`text-sm font-medium transition-colors hover:text-blue-600 ${
                    isActive(item.path) ? 'text-blue-600' : 'text-gray-700'
                  }`}
                  onClick={() => setMobileMenuOpen(false)}
                >
                  {item.label}
                </Link>
              ))}
              <div className="flex items-center space-x-4 pt-4 border-t">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={toggleLanguage}
                  className="flex items-center space-x-2"
                >
                  <Globe className="w-4 h-4" />
                  <span className="font-semibold">{language.toUpperCase()}</span>
                </Button>
                <Button className="bg-blue-600 hover:bg-blue-700">
                  {t(language, 'contact')}
                </Button>
              </div>
            </nav>
          </div>
        )}
      </div>
    </header>
  );
};

export default Header;
