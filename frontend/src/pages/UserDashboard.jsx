import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import {
  Bot, Shield, FileText, Languages, Users, Home,
  Clock, Package, MessageCircle, Phone,
  Sparkles, Scale, ArrowRight, User, Mail,
  Calendar, MapPin, Edit2, Save, X, LogOut
} from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { useLanguage } from '../contexts/LanguageContext';
import ChatSelector from '../components/ChatSelector';

const UserDashboard = () => {
  const { user, logout } = useAuth();
  const { language } = useLanguage();
  const navigate = useNavigate();
  const [showChatSelector, setShowChatSelector] = useState(false);
  const [isEditingProfile, setIsEditingProfile] = useState(false);
  const [profileData, setProfileData] = useState({
    username: user?.username || '',
    email: user?.email || '',
    phone: user?.phone || '',
    address: user?.address || ''
  });

  // AI Features
  const aiFeatures = [
    {
      id: 'chat',
      title: language === 'de' ? 'Anwalt AI' : 'Lawyer AI',
      description: language === 'de' ? '24/7 sofortige rechtliche Antworten' : 'Get instant legal answers 24/7',
      icon: Bot,
      action: () => setShowChatSelector(true),
      gradient: 'from-purple-500 to-pink-500'
    },
    {
      id: 'risk',
      title: language === 'de' ? 'Risikoanalyse' : 'Risk Analysis',
      description: language === 'de' ? 'Bewerten Sie Kindersicherheitsrisiken' : 'Assess child safety risks',
      icon: Shield,
      link: '/risk-analyzer',
      gradient: 'from-red-500 to-orange-500'
    },
    {
      id: 'petition',
      title: language === 'de' ? 'Petition erstellen' : 'Generate Petition',
      description: language === 'de' ? 'Gerichtsfertige Dokumente erstellen' : 'Create court-ready documents',
      icon: FileText,
      link: '/petition-generator',
      gradient: 'from-blue-500 to-cyan-500'
    },
    {
      id: 'translate',
      title: language === 'de' ? 'Übersetzung' : 'Translation',
      description: language === 'de' ? 'Dokumente übersetzen' : 'Translate documents',
      icon: Languages,
      link: '/translator',
      gradient: 'from-green-500 to-teal-500'
    },
    {
      id: 'alienation',
      title: language === 'de' ? 'Entfremdungsdetektor' : 'Alienation Detector',
      description: language === 'de' ? 'Entfremdungsmuster erkennen' : 'Identify alienation patterns',
      icon: Users,
      link: '/alienation-detector',
      gradient: 'from-orange-500 to-red-500'
    },
    {
      id: 'evidence',
      title: language === 'de' ? 'Beweisorganisator' : 'Evidence Organizer',
      description: language === 'de' ? 'Beweise organisieren' : 'Organize evidence',
      icon: Package,
      link: '/evidence-analyzer',
      gradient: 'from-indigo-500 to-purple-500'
    },
    {
      id: 'timeline',
      title: language === 'de' ? 'Zeitleiste' : 'Timeline',
      description: language === 'de' ? 'Chronologische Zeitleiste erstellen' : 'Create chronological timeline',
      icon: Clock,
      link: '/timeline-generator',
      gradient: 'from-pink-500 to-rose-500'
    },
    {
      id: 'summary',
      title: language === 'de' ? 'Fallzusammenfassung' : 'Case Summary',
      description: language === 'de' ? 'Komplettes Fallpaket' : 'Complete case package',
      icon: Scale,
      link: '/case-summary',
      gradient: 'from-yellow-500 to-orange-500'
    }
  ];

  const handleSaveProfile = () => {
    // TODO: Save to backend
    setIsEditingProfile(false);
  };

  const handleLogout = () => {
    logout();
    navigate('/');
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {showChatSelector && (
        <ChatSelector onClose={() => setShowChatSelector(false)} />
      )}

      {/* Return to Home Button */}
      <div className="bg-white border-b px-4 py-3">
        <div className="max-w-7xl mx-auto">
          <Link
            to="/"
            className="inline-flex items-center text-gray-600 hover:text-blue-600 transition-colors"
          >
            <Home className="w-4 h-4 mr-2" />
            <span className="font-medium">{language === 'de' ? 'Zurück zur Startseite' : 'Return to Home'}</span>
          </Link>
        </div>
      </div>

      <div className="max-w-7xl mx-auto p-4 md:p-8">
        <div className="grid lg:grid-cols-4 gap-6">
          {/* LEFT PANEL - User Profile */}
          <div className="lg:col-span-1">
            <div className="bg-gradient-to-br from-gray-900 to-gray-800 rounded-2xl p-6 text-white shadow-2xl sticky top-4">
              {/* Profile Header */}
              <div className="text-center mb-6">
                <div className="w-24 h-24 bg-gradient-to-br from-purple-500 to-pink-500 rounded-full mx-auto mb-4 flex items-center justify-center">
                  <User className="w-12 h-12" />
                </div>
                <h3 className="text-xl font-bold">{user?.username || 'User'}</h3>
                <p className="text-gray-400 text-sm">{user?.role === 'admin' ? 'Admin' : 'Client'}</p>
              </div>

              {/* Profile Info */}
              <div className="space-y-4 mb-6">
                {isEditingProfile ? (
                  <>
                    <div>
                      <label className="text-xs text-gray-400">{language === 'de' ? 'Name' : 'Username'}</label>
                      <input
                        type="text"
                        value={profileData.username}
                        onChange={(e) => setProfileData({...profileData, username: e.target.value})}
                        className="w-full bg-gray-700 text-white rounded-lg px-3 py-2 mt-1 text-sm"
                      />
                    </div>
                    <div>
                      <label className="text-xs text-gray-400">Email</label>
                      <input
                        type="email"
                        value={profileData.email}
                        onChange={(e) => setProfileData({...profileData, email: e.target.value})}
                        className="w-full bg-gray-700 text-white rounded-lg px-3 py-2 mt-1 text-sm"
                      />
                    </div>
                    <div>
                      <label className="text-xs text-gray-400">{language === 'de' ? 'Telefon' : 'Phone'}</label>
                      <input
                        type="tel"
                        value={profileData.phone}
                        onChange={(e) => setProfileData({...profileData, phone: e.target.value})}
                        className="w-full bg-gray-700 text-white rounded-lg px-3 py-2 mt-1 text-sm"
                      />
                    </div>
                    <div>
                      <label className="text-xs text-gray-400">{language === 'de' ? 'Adresse' : 'Address'}</label>
                      <input
                        type="text"
                        value={profileData.address}
                        onChange={(e) => setProfileData({...profileData, address: e.target.value})}
                        className="w-full bg-gray-700 text-white rounded-lg px-3 py-2 mt-1 text-sm"
                      />
                    </div>
                  </>
                ) : (
                  <>
                    <div className="flex items-center gap-3">
                      <Mail className="w-4 h-4 text-gray-400" />
                      <div>
                        <div className="text-xs text-gray-400">Email</div>
                        <div className="text-sm">{user?.email || 'Not set'}</div>
                      </div>
                    </div>
                    <div className="flex items-center gap-3">
                      <Phone className="w-4 h-4 text-gray-400" />
                      <div>
                        <div className="text-xs text-gray-400">{language === 'de' ? 'Telefon' : 'Phone'}</div>
                        <div className="text-sm">{user?.phone || 'Not set'}</div>
                      </div>
                    </div>
                    <div className="flex items-center gap-3">
                      <MapPin className="w-4 h-4 text-gray-400" />
                      <div>
                        <div className="text-xs text-gray-400">{language === 'de' ? 'Adresse' : 'Address'}</div>
                        <div className="text-sm">{user?.address || 'Not set'}</div>
                      </div>
                    </div>
                    <div className="flex items-center gap-3">
                      <Calendar className="w-4 h-4 text-gray-400" />
                      <div>
                        <div className="text-xs text-gray-400">{language === 'de' ? 'Mitglied seit' : 'Member since'}</div>
                        <div className="text-sm">{new Date(user?.createdAt || Date.now()).toLocaleDateString()}</div>
                      </div>
                    </div>
                  </>
                )}
              </div>

              {/* Action Buttons */}
              <div className="space-y-2">
                {isEditingProfile ? (
                  <>
                    <button
                      onClick={handleSaveProfile}
                      className="w-full bg-green-600 hover:bg-green-700 text-white rounded-lg px-4 py-2 flex items-center justify-center gap-2 transition-colors"
                    >
                      <Save className="w-4 h-4" />
                      {language === 'de' ? 'Speichern' : 'Save'}
                    </button>
                    <button
                      onClick={() => setIsEditingProfile(false)}
                      className="w-full bg-gray-700 hover:bg-gray-600 text-white rounded-lg px-4 py-2 flex items-center justify-center gap-2 transition-colors"
                    >
                      <X className="w-4 h-4" />
                      {language === 'de' ? 'Abbrechen' : 'Cancel'}
                    </button>
                  </>
                ) : (
                  <button
                    onClick={() => setIsEditingProfile(true)}
                    className="w-full bg-purple-600 hover:bg-purple-700 text-white rounded-lg px-4 py-2 flex items-center justify-center gap-2 transition-colors"
                  >
                    <Edit2 className="w-4 h-4" />
                    {language === 'de' ? 'Profil bearbeiten' : 'Edit Profile'}
                  </button>
                )}
                <button
                  onClick={handleLogout}
                  className="w-full bg-red-600 hover:bg-red-700 text-white rounded-lg px-4 py-2 flex items-center justify-center gap-2 transition-colors"
                >
                  <LogOut className="w-4 h-4" />
                  {language === 'de' ? 'Ausloggen' : 'Logout'}
                </button>
              </div>
            </div>
          </div>

          {/* RIGHT PANEL - AI Tools */}
          <div className="lg:col-span-3">
            {/* Welcome Header */}
            <div className="bg-gradient-to-r from-purple-600 to-pink-600 rounded-2xl shadow-xl p-6 mb-6 text-white">
              <h1 className="text-3xl font-bold mb-2">
                {language === 'de' ? 'Willkommen zurück' : 'Welcome back'}, {user?.username || 'there'}! 👋
              </h1>
              <p className="text-purple-100">
                {language === 'de'
                  ? 'Ihr KI-gestützter Rechtsassistent ist bereit zu helfen'
                  : 'Your AI-powered legal assistant is ready to help'}
              </p>
            </div>

            {/* AI Tools Grid */}
            <div>
              <h2 className="text-2xl font-bold text-gray-800 mb-4 flex items-center gap-2">
                <Sparkles className="text-purple-600" />
                {language === 'de' ? 'Alle Tools' : 'All Tools'}
              </h2>

              <div className="grid md:grid-cols-2 gap-4">
                {aiFeatures.map((feature) => (
                  <div
                    key={feature.id}
                    onClick={feature.action}
                    className="group bg-white rounded-xl p-6 shadow-md hover:shadow-xl transition-all cursor-pointer border-2 border-transparent hover:border-purple-200"
                  >
                    <div className="flex items-start justify-between mb-3">
                      <div className={`inline-flex p-3 rounded-xl bg-gradient-to-r ${feature.gradient}`}>
                        <feature.icon className="text-white" size={24} />
                      </div>
                    </div>

                    <h3 className="text-lg font-bold text-gray-800 mb-2 group-hover:text-purple-600 transition-colors">
                      {feature.title}
                    </h3>
                    <p className="text-gray-600 text-sm mb-3">
                      {feature.description}
                    </p>

                    {feature.link ? (
                      <Link
                        to={feature.link}
                        className="inline-flex items-center text-purple-600 hover:text-purple-700 font-semibold text-sm"
                      >
                        {language === 'de' ? 'Jetzt starten' : 'Start Now'}
                        <ArrowRight className="ml-1" size={16} />
                      </Link>
                    ) : (
                      <div className="inline-flex items-center text-purple-600 font-semibold text-sm">
                        {language === 'de' ? 'Chat öffnen' : 'Open Chat'}
                        <ArrowRight className="ml-1" size={16} />
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>

            {/* Need Help Section */}
            <div className="mt-6 bg-gradient-to-br from-purple-100 to-pink-100 rounded-2xl p-6">
              <h3 className="text-xl font-bold text-gray-800 mb-4">
                {language === 'de' ? 'Brauchen Sie Hilfe?' : 'Need Help?'}
              </h3>
              <div className="grid md:grid-cols-2 gap-3">
                <button
                  onClick={() => setShowChatSelector(true)}
                  className="flex items-center gap-3 p-4 bg-white rounded-xl hover:shadow-md transition-shadow"
                >
                  <div className="bg-purple-100 p-2 rounded-lg">
                    <Bot className="text-purple-600" size={20} />
                  </div>
                  <div className="text-left flex-1">
                    <div className="font-semibold text-gray-800 text-sm">{language === 'de' ? 'Anwalt AI' : 'Lawyer AI'}</div>
                    <div className="text-xs text-gray-500">24/7</div>
                  </div>
                  <ArrowRight className="text-gray-400" size={18} />
                </button>

                <Link
                  to="/admin/live-chat"
                  className="flex items-center gap-3 p-4 bg-white rounded-xl hover:shadow-md transition-shadow"
                >
                  <div className="bg-pink-100 p-2 rounded-lg">
                    <MessageCircle className="text-pink-600" size={20} />
                  </div>
                  <div className="text-left flex-1">
                    <div className="font-semibold text-gray-800 text-sm">Live Chat</div>
                    <div className="text-xs text-gray-500">{language === 'de' ? 'Experte' : 'Expert'}</div>
                  </div>
                  <ArrowRight className="text-gray-400" size={18} />
                </Link>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default UserDashboard;
