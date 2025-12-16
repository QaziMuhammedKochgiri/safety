import React, { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { useLanguage } from '../contexts/LanguageContext';
import { useAuth } from '../contexts/AuthContext';
import { t } from '../translations';
import { Button } from './ui/button';
import { Globe, Menu, X, ChevronDown, Sparkles, Brain, FileText, Languages, Shield, Package, Clock, Scale } from 'lucide-react';

const Header = () => {
  const { language, toggleLanguage } = useLanguage();
  const { user } = useAuth();
  const location = useLocation();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [aiDropdownOpen, setAiDropdownOpen] = useState(false);

  const navItems = [
    { path: '/', label: t(language, 'home') },
    { path: '/services', label: t(language, 'services') },
    { path: '/about', label: t(language, 'about') },
    { path: '/documents', label: t(language, 'documents') },
    { path: '/forensic-analysis', label: language === 'de' ? 'Forensik' : 'Forensics' },
    { path: '/faq', label: t(language, 'faq') },
  ];

  const aiFeatures = [
    { path: '/dashboard', label: language === 'de' ? '🏠 Haupt-Dashboard' : '🏠 Main Dashboard', icon: Sparkles },
    { path: '/ai-chat', label: language === 'de' ? '🤖 Lawyer AI' : '🤖 Lawyer AI', icon: Brain },
    { path: '/risk-analyzer', label: language === 'de' ? '⚠️ Risiko-Analyse' : '⚠️ Risk Analysis', icon: Shield },
    { path: '/petition-generator', label: language === 'de' ? '📄 Antrag Generator' : '📄 Petition Generator', icon: FileText },
    { path: '/translator', label: language === 'de' ? '🌍 Übersetzer' : '🌍 Translator', icon: Languages },
    { path: '/alienation-detector', label: language === 'de' ? '👥 Entfremdung' : '👥 Alienation', icon: Shield },
    { path: '/evidence-analyzer', label: language === 'de' ? '📦 Beweise' : '📦 Evidence', icon: Package },
    { path: '/timeline-generator', label: language === 'de' ? '🕐 Zeitlinie' : '🕐 Timeline', icon: Clock },
    { path: '/case-summary', label: language === 'de' ? '⚖️ Fall-Zusammenfassung' : '⚖️ Case Summary', icon: Scale },
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

          <div className="flex items-center space-x-4">
            {/* Desktop Navigation */}
            <nav className="hidden md:flex items-center space-x-6">
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

              {/* AI Features Dropdown */}
              <div
                className="relative"
                onMouseEnter={() => setAiDropdownOpen(true)}
                onMouseLeave={() => setAiDropdownOpen(false)}
              >
                <button
                  className="flex items-center space-x-1 text-sm font-medium text-gray-700 hover:text-blue-600 transition-colors"
                >
                  <Sparkles className="w-4 h-4" />
                  <span>{language === 'de' ? 'KI Features' : 'AI Features'}</span>
                  <ChevronDown className={`w-4 h-4 transition-transform ${aiDropdownOpen ? 'rotate-180' : ''}`} />
                </button>

                {aiDropdownOpen && (
                  <div className="absolute top-full left-0 mt-1 w-64 bg-white border border-gray-200 rounded-lg shadow-xl py-2 z-50">
                    {aiFeatures.map((feature) => (
                      <Link
                        key={feature.path}
                        to={feature.path}
                        onClick={() => setAiDropdownOpen(false)}
                        className="flex items-center px-4 py-2 text-sm text-gray-700 hover:bg-blue-50 hover:text-blue-600 transition-colors"
                      >
                        <span className="mr-2">{feature.label}</span>
                      </Link>
                    ))}
                  </div>
                )}
              </div>

              {/* Portal/Dashboard Link */}
              <Link
                to="/portal"
                className={`text-sm font-medium transition-colors hover:text-blue-600 ${
                  isActive('/portal') || isActive('/dashboard')
                    ? 'text-blue-600 border-b-2 border-blue-600 pb-1'
                    : 'text-gray-700'
                }`}
              >
                {user ? (language === 'de' ? 'Dashboard' : 'Dashboard') : (language === 'de' ? 'Portal' : 'Portal')}
              </Link>
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

              {/* AI Features in Mobile */}
              <>
                <div className="text-xs font-semibold text-gray-500 uppercase pt-2 border-t">
                  {language === 'de' ? 'KI Features' : 'AI Features'}
                </div>
                {aiFeatures.map((feature) => (
                  <Link
                    key={feature.path}
                    to={feature.path}
                    className="text-sm font-medium text-gray-700 hover:text-blue-600 pl-4"
                    onClick={() => setMobileMenuOpen(false)}
                  >
                    {feature.label}
                  </Link>
                ))}
              </>

              <Link
                to="/portal"
                className={`text-sm font-medium transition-colors hover:text-blue-600 ${
                  isActive('/portal') ? 'text-blue-600' : 'text-gray-700'
                }`}
                onClick={() => setMobileMenuOpen(false)}
              >
                {user ? (language === 'de' ? 'Dashboard' : 'Dashboard') : (language === 'de' ? 'Portal' : 'Portal')}
              </Link>

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
                <a href="mailto:info@safechild.mom">
                  <Button className="bg-blue-600 hover:bg-blue-700">
                    {t(language, 'contact')}
                  </Button>
                </a>
              </div>
            </nav>
          </div>
        )}
      </div>
    </header>
  );
};

export default Header;
