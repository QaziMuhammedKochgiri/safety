import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import {
  Bot, Shield, FileText, Languages, Users,
  Clock, Calendar, Package, MessageCircle, Phone,
  Sparkles, TrendingUp, CheckCircle, AlertCircle,
  Scale, Download, Eye, ArrowRight
} from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import ChatSelector from '../components/ChatSelector';

/**
 * User Dashboard - "Baş Yolla" Central Hub
 * One-click access to all AI features for mothers building custody cases
 */
const UserDashboard = () => {
  const { user } = useAuth();
  const [showChatSelector, setShowChatSelector] = useState(false);

  // AI Features - "Baş Yolla" Quick Actions
  const aiFeatures = [
    {
      id: 'chat',
      title: 'Lawyer AI',
      description: 'Get instant legal answers to your questions 24/7',
      icon: Bot,
      color: 'purple',
      action: () => setShowChatSelector(true),
      badge: '24/7',
      gradient: 'from-purple-500 to-pink-500'
    },
    {
      id: 'risk',
      title: 'Risk Analysis',
      description: 'Assess child safety risks in your case',
      icon: Shield,
      color: 'red',
      link: '/risk-analyzer',
      badge: 'Important',
      gradient: 'from-red-500 to-orange-500'
    },
    {
      id: 'petition',
      title: 'Generate Petition',
      description: 'Create court-ready documents instantly',
      icon: FileText,
      color: 'blue',
      link: '/petition-generator',
      badge: 'New',
      gradient: 'from-blue-500 to-cyan-500'
    },
    {
      id: 'translate',
      title: 'Legal Translation',
      description: 'Translate documents between TR/EN/DE',
      icon: Languages,
      color: 'green',
      link: '/translator',
      badge: 'Multi-language',
      gradient: 'from-green-500 to-teal-500'
    },
    {
      id: 'alienation',
      title: 'Alienation Detector',
      description: 'Identify parental alienation patterns',
      icon: Users,
      color: 'orange',
      link: '/alienation-detector',
      badge: 'Expert',
      gradient: 'from-orange-500 to-red-500'
    },
    {
      id: 'evidence',
      title: 'Evidence Organizer',
      description: 'Organize and analyze your evidence',
      icon: Package,
      color: 'indigo',
      link: '/evidence-analyzer',
      badge: 'Essential',
      gradient: 'from-indigo-500 to-purple-500'
    },
    {
      id: 'timeline',
      title: 'Timeline Generator',
      description: 'Create chronological case timeline',
      icon: Clock,
      color: 'pink',
      link: '/timeline-generator',
      badge: 'Visual',
      gradient: 'from-pink-500 to-rose-500'
    },
    {
      id: 'summary',
      title: 'Case Summary',
      description: 'Complete case package for court',
      icon: Scale,
      color: 'yellow',
      link: '/case-summary',
      badge: 'Complete',
      gradient: 'from-yellow-500 to-orange-500'
    }
  ];

  // Recent Activity
  const recentActivity = [
    { action: 'Risk Analysis', date: '2 hours ago', status: 'completed' },
    { action: 'Petition Generated', date: 'Yesterday', status: 'completed' },
    { action: 'Evidence Uploaded', date: '2 days ago', status: 'completed' }
  ];

  // Quick Stats
  const stats = [
    { label: 'Documents Generated', value: '12', icon: FileText, color: 'blue' },
    { label: 'Evidence Items', value: '48', icon: Package, color: 'purple' },
    { label: 'AI Analyses', value: '23', icon: TrendingUp, color: 'green' },
    { label: 'Days Active', value: '45', icon: Calendar, color: 'orange' }
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-purple-50 to-pink-50">
      {/* Chat Selector Modal */}
      {showChatSelector && (
        <ChatSelector onClose={() => setShowChatSelector(false)} />
      )}

      <div className="max-w-7xl mx-auto p-4 md:p-8">
        {/* Welcome Header */}
        <div className="bg-gradient-to-r from-purple-600 to-pink-600 rounded-3xl shadow-2xl p-8 mb-8 text-white">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-4xl font-bold mb-2">
                Welcome back, {user?.username || 'there'}! 👋
              </h1>
              <p className="text-purple-100 text-lg">
                Your AI-powered legal assistant is ready to help
              </p>
            </div>
            <Sparkles className="hidden md:block" size={64} />
          </div>
        </div>

        {/* Quick Stats */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
          {stats.map((stat, index) => (
            <div
              key={index}
              className="bg-white rounded-2xl p-6 shadow-lg hover:shadow-xl transition-shadow"
            >
              <div className={`inline-flex p-3 rounded-xl bg-${stat.color}-100 mb-3`}>
                <stat.icon className={`text-${stat.color}-600`} size={24} />
              </div>
              <div className="text-3xl font-bold text-gray-800 mb-1">
                {stat.value}
              </div>
              <div className="text-sm text-gray-600">{stat.label}</div>
            </div>
          ))}
        </div>

        {/* Main Content Grid */}
        <div className="grid lg:grid-cols-3 gap-8">
          {/* Left Column - AI Features */}
          <div className="lg:col-span-2">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-2xl font-bold text-gray-800">
                AI Tools - "Baş Yolla" 🚀
              </h2>
              <span className="text-sm text-gray-500">One-click simplicity</span>
            </div>

            <div className="grid md:grid-cols-2 gap-4">
              {aiFeatures.map((feature) => (
                <div
                  key={feature.id}
                  onClick={feature.action}
                  className="group bg-white rounded-2xl p-6 shadow-lg hover:shadow-2xl transition-all cursor-pointer transform hover:-translate-y-1"
                >
                  {/* Icon and Badge */}
                  <div className="flex items-start justify-between mb-4">
                    <div className={`inline-flex p-4 rounded-2xl bg-gradient-to-r ${feature.gradient}`}>
                      <feature.icon className="text-white" size={28} />
                    </div>
                    {feature.badge && (
                      <span className={`px-3 py-1 rounded-full text-xs font-semibold bg-${feature.color}-100 text-${feature.color}-700`}>
                        {feature.badge}
                      </span>
                    )}
                  </div>

                  {/* Content */}
                  <h3 className="text-xl font-bold text-gray-800 mb-2 group-hover:text-purple-600 transition-colors">
                    {feature.title}
                  </h3>
                  <p className="text-gray-600 text-sm mb-4">
                    {feature.description}
                  </p>

                  {/* Action Link */}
                  {feature.link ? (
                    <Link
                      to={feature.link}
                      className="inline-flex items-center text-purple-600 hover:text-purple-700 font-semibold text-sm"
                    >
                      Start Now
                      <ArrowRight className="ml-1" size={16} />
                    </Link>
                  ) : (
                    <div className="inline-flex items-center text-purple-600 font-semibold text-sm">
                      Open Chat
                      <ArrowRight className="ml-1" size={16} />
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>

          {/* Right Column - Recent Activity & Support */}
          <div className="space-y-6">
            {/* Recent Activity */}
            <div className="bg-white rounded-2xl p-6 shadow-lg">
              <h3 className="text-xl font-bold text-gray-800 mb-4 flex items-center">
                <Clock className="mr-2 text-blue-600" size={24} />
                Recent Activity
              </h3>
              <div className="space-y-3">
                {recentActivity.map((activity, index) => (
                  <div
                    key={index}
                    className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
                  >
                    <div>
                      <div className="font-semibold text-gray-800 text-sm">
                        {activity.action}
                      </div>
                      <div className="text-xs text-gray-500">{activity.date}</div>
                    </div>
                    <CheckCircle className="text-green-500" size={20} />
                  </div>
                ))}
              </div>
              <Link
                to="/history"
                className="block mt-4 text-center text-blue-600 hover:text-blue-700 font-semibold text-sm"
              >
                View All Activity →
              </Link>
            </div>

            {/* Support Options */}
            <div className="bg-gradient-to-br from-purple-100 to-pink-100 rounded-2xl p-6 shadow-lg">
              <h3 className="text-xl font-bold text-gray-800 mb-4">
                Need Help?
              </h3>
              <div className="space-y-3">
                <button
                  onClick={() => setShowChatSelector(true)}
                  className="w-full flex items-center gap-3 p-4 bg-white rounded-xl hover:shadow-md transition-shadow text-left"
                >
                  <div className="bg-purple-100 p-2 rounded-lg">
                    <Bot className="text-purple-600" size={20} />
                  </div>
                  <div className="flex-1">
                    <div className="font-semibold text-gray-800">Lawyer AI</div>
                    <div className="text-xs text-gray-500">24/7 Instant Legal Help</div>
                  </div>
                  <ArrowRight className="text-gray-400" size={20} />
                </button>

                <Link
                  to="/admin/live-chat"
                  className="w-full flex items-center gap-3 p-4 bg-white rounded-xl hover:shadow-md transition-shadow"
                >
                  <div className="bg-pink-100 p-2 rounded-lg">
                    <MessageCircle className="text-pink-600" size={20} />
                  </div>
                  <div className="flex-1">
                    <div className="font-semibold text-gray-800">Live Chat</div>
                    <div className="text-xs text-gray-500">Talk to Expert</div>
                  </div>
                  <ArrowRight className="text-gray-400" size={20} />
                </Link>

                <Link
                  to="/book-consultation"
                  className="w-full flex items-center gap-3 p-4 bg-white rounded-xl hover:shadow-md transition-shadow"
                >
                  <div className="bg-blue-100 p-2 rounded-lg">
                    <Phone className="text-blue-600" size={20} />
                  </div>
                  <div className="flex-1">
                    <div className="font-semibold text-gray-800">Book Call</div>
                    <div className="text-xs text-gray-500">Schedule Consultation</div>
                  </div>
                  <ArrowRight className="text-gray-400" size={20} />
                </Link>
              </div>
            </div>

            {/* Quick Tip */}
            <div className="bg-yellow-50 border-2 border-yellow-200 rounded-2xl p-6">
              <div className="flex items-start gap-3">
                <AlertCircle className="text-yellow-600 flex-shrink-0 mt-1" size={24} />
                <div>
                  <div className="font-bold text-yellow-900 mb-2">💡 Quick Tip</div>
                  <div className="text-sm text-yellow-800">
                    Start with <strong>Risk Analysis</strong> to understand your case better,
                    then use <strong>Evidence Organizer</strong> to collect proof. The AI will
                    guide you through each step!
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Bottom CTA */}
        <div className="mt-8 bg-gradient-to-r from-blue-600 to-purple-600 rounded-3xl p-8 text-white text-center">
          <h2 className="text-3xl font-bold mb-3">
            Ready to Build Your Case? 📋
          </h2>
          <p className="text-blue-100 mb-6 max-w-2xl mx-auto">
            Our AI tools have helped hundreds of mothers win custody cases.
            Start with one click - it's that simple!
          </p>
          <div className="flex gap-4 justify-center flex-wrap">
            <Link
              to="/risk-analyzer"
              className="bg-white text-blue-600 px-8 py-4 rounded-xl font-bold hover:shadow-xl transition-shadow"
            >
              Start Risk Analysis
            </Link>
            <button
              onClick={() => setShowChatSelector(true)}
              className="bg-blue-500 text-white px-8 py-4 rounded-xl font-bold hover:bg-blue-400 transition-colors"
            >
              Chat with AI
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default UserDashboard;
