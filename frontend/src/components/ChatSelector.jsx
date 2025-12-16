import React, { useState } from 'react';
import { MessageCircle, Bot, Users, X } from 'lucide-react';

/**
 * Chat Selector Component
 * Allows users to choose between Live Chat (human) or AI Chat (Claude)
 */
const ChatSelector = ({ onClose }) => {
  const [selectedChat, setSelectedChat] = useState(null);

  const handleSelectChat = (chatType) => {
    setSelectedChat(chatType);
    // Redirect to appropriate chat
    if (chatType === 'live') {
      window.location.href = '/admin/live-chat';
    } else if (chatType === 'ai') {
      window.location.href = '/ai-chat';
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-2xl max-w-2xl w-full p-8 relative">
        {/* Close Button */}
        <button
          onClick={onClose}
          className="absolute top-4 right-4 text-gray-400 hover:text-gray-600 transition-colors"
        >
          <X size={24} />
        </button>

        {/* Header */}
        <div className="text-center mb-8">
          <MessageCircle className="mx-auto mb-4 text-pink-600" size={48} />
          <h2 className="text-3xl font-bold text-gray-800 mb-2">
            Choose Your Chat Support
          </h2>
          <p className="text-gray-600">
            Select the type of support you need
          </p>
        </div>

        {/* Chat Options */}
        <div className="grid md:grid-cols-2 gap-6">
          {/* Live Chat Option */}
          <div
            onClick={() => handleSelectChat('live')}
            className="border-2 border-gray-200 rounded-xl p-6 hover:border-pink-500 hover:shadow-lg transition-all cursor-pointer group"
          >
            <div className="flex flex-col items-center text-center">
              <div className="bg-pink-100 group-hover:bg-pink-200 rounded-full p-4 mb-4 transition-colors">
                <Users className="text-pink-600" size={32} />
              </div>
              <h3 className="text-xl font-bold text-gray-800 mb-2">
                Live Chat
              </h3>
              <p className="text-gray-600 mb-4">
                Talk to a real person from our support team
              </p>

              <div className="space-y-2 text-sm text-left w-full">
                <div className="flex items-center text-green-600">
                  <span className="mr-2">✓</span>
                  <span>Human empathy & understanding</span>
                </div>
                <div className="flex items-center text-green-600">
                  <span className="mr-2">✓</span>
                  <span>Complex case discussions</span>
                </div>
                <div className="flex items-center text-green-600">
                  <span className="mr-2">✓</span>
                  <span>Personalized advice</span>
                </div>
                <div className="flex items-center text-gray-500">
                  <span className="mr-2">⏰</span>
                  <span>Available during office hours</span>
                </div>
              </div>

              <button className="mt-6 w-full bg-pink-600 hover:bg-pink-700 text-white font-semibold py-3 px-6 rounded-lg transition-colors">
                Start Live Chat
              </button>
            </div>
          </div>

          {/* AI Chat Option */}
          <div
            onClick={() => handleSelectChat('ai')}
            className="border-2 border-gray-200 rounded-xl p-6 hover:border-purple-500 hover:shadow-lg transition-all cursor-pointer group"
          >
            <div className="flex flex-col items-center text-center">
              <div className="bg-purple-100 group-hover:bg-purple-200 rounded-full p-4 mb-4 transition-colors">
                <Bot className="text-purple-600" size={32} />
              </div>
              <h3 className="text-xl font-bold text-gray-800 mb-2">
                Lawyer AI
              </h3>
              <p className="text-gray-600 mb-4">
                Get instant legal help from Lawyer AI powered by Claude
              </p>

              <div className="space-y-2 text-sm text-left w-full">
                <div className="flex items-center text-green-600">
                  <span className="mr-2">✓</span>
                  <span>24/7 instant responses</span>
                </div>
                <div className="flex items-center text-green-600">
                  <span className="mr-2">✓</span>
                  <span>Quick legal term explanations</span>
                </div>
                <div className="flex items-center text-green-600">
                  <span className="mr-2">✓</span>
                  <span>Document generation help</span>
                </div>
                <div className="flex items-center text-green-600">
                  <span className="mr-2">✓</span>
                  <span>Risk analysis guidance</span>
                </div>
              </div>

              <button className="mt-6 w-full bg-purple-600 hover:bg-purple-700 text-white font-semibold py-3 px-6 rounded-lg transition-colors">
                Start AI Chat
              </button>
            </div>
          </div>
        </div>

        {/* Footer Note */}
        <div className="mt-8 text-center text-sm text-gray-500">
          <p>
            💡 <strong>Tip:</strong> Try AI Chat first for quick answers. You can always switch to Live Chat for complex discussions.
          </p>
        </div>
      </div>
    </div>
  );
};

export default ChatSelector;
