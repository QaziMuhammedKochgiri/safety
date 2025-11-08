import React from 'react';
import { Link } from 'react-router-dom';
import { useLanguage } from '../contexts/LanguageContext';
import { t } from '../translations';
import { MapPin, Phone, Mail } from 'lucide-react';

const Footer = () => {
  const { language } = useLanguage();

  return (
    <footer className="bg-gray-900 text-gray-300">
      <div className="container mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
          {/* Brand */}
          <div className="space-y-4">
            <div className="flex items-center space-x-2">
              <div className="w-10 h-10 bg-gradient-to-br from-blue-600 to-blue-800 rounded-lg flex items-center justify-center">
                <span className="text-white font-bold text-xl">SC</span>
              </div>
              <div className="flex flex-col">
                <span className="font-bold text-lg leading-tight text-white">SafeChild</span>
                <span className="text-xs text-gray-400">
                  {language === 'de' ? 'Rechtsanwaltskanzlei' : 'Law Firm'}
                </span>
              </div>
            </div>
            <p className="text-sm">{t(language, 'footerTagline')}</p>
          </div>

          {/* Location */}
          <div>
            <h3 className="font-semibold text-white mb-4">{t(language, 'footerLocation')}</h3>
            <div className="space-y-3">
              <div className="flex items-start space-x-2">
                <MapPin className="w-5 h-5 text-blue-500 mt-0.5 flex-shrink-0" />
                <span className="text-sm">{t(language, 'footerAddress')}</span>
              </div>
              <div className="flex items-center space-x-2">
                <Phone className="w-5 h-5 text-blue-500 flex-shrink-0" />
                <span className="text-sm">+31 20 123 4567</span>
              </div>
              <div className="flex items-center space-x-2">
                <Mail className="w-5 h-5 text-blue-500 flex-shrink-0" />
                <span className="text-sm">info@safechild.mom</span>
              </div>
            </div>
          </div>

          {/* Quick Links */}
          <div>
            <h3 className="font-semibold text-white mb-4">{t(language, 'footerQuickLinks')}</h3>
            <ul className="space-y-2">
              <li>
                <Link to="/" className="text-sm hover:text-blue-400 transition-colors">
                  {t(language, 'home')}
                </Link>
              </li>
              <li>
                <Link to="/services" className="text-sm hover:text-blue-400 transition-colors">
                  {t(language, 'services')}
                </Link>
              </li>
              <li>
                <Link to="/about" className="text-sm hover:text-blue-400 transition-colors">
                  {t(language, 'about')}
                </Link>
              </li>
              <li>
                <Link to="/faq" className="text-sm hover:text-blue-400 transition-colors">
                  {t(language, 'faq')}
                </Link>
              </li>
            </ul>
          </div>

          {/* Legal */}
          <div>
            <h3 className="font-semibold text-white mb-4">{t(language, 'footerLegal')}</h3>
            <ul className="space-y-2">
              <li>
                <Link to="/privacy" className="text-sm hover:text-blue-400 transition-colors">
                  {t(language, 'privacy')}
                </Link>
              </li>
              <li>
                <Link to="/terms" className="text-sm hover:text-blue-400 transition-colors">
                  {t(language, 'terms')}
                </Link>
              </li>
              <li>
                <Link to="/imprint" className="text-sm hover:text-blue-400 transition-colors">
                  {t(language, 'imprint')}
                </Link>
              </li>
            </ul>
          </div>
        </div>

        {/* Bottom Bar */}
        <div className="mt-12 pt-8 border-t border-gray-800 text-center">
          <p className="text-sm">{t(language, 'footerRights')}</p>
        </div>
      </div>
    </footer>
  );
};

export default Footer;
