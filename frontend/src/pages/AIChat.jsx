import React, { useState, useEffect, useRef } from 'react';
import {
  Bot, Send, Trash2, Download, Copy, Check,
  Sparkles, FileText, AlertCircle, Shield, Scale
} from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';

/**
 * AI Chat Page - Claude AI Assistant
 * 24/7 AI-powered legal assistant for mothers in custody cases
 */
const AIChat = () => {
  const { user, token } = useAuth();
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId, setSessionId] = useState(null);
  const [copiedId, setCopiedId] = useState(null);
  const messagesEndRef = useRef(null);

  // Scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Initialize chat with welcome message
  useEffect(() => {
    if (!sessionId) {
      const newSessionId = `session_${Date.now()}`;
      setSessionId(newSessionId);

      // Welcome message
      setMessages([{
        id: '1',
        role: 'assistant',
        content: `Hello ${user?.username || 'there'}! 👋\n\nI'm **Lawyer AI**, your personal legal assistant powered by Claude. I'm here to help you 24/7 with:\n\n• Understanding legal terms and processes\n• Documenting your case\n• Analyzing risks and evidence\n• Generating court documents\n• Answering your questions in simple language\n\nWhat would you like help with today?`,
        timestamp: new Date().toISOString(),
        quickActions: [
          { action: 'analyze_risk', label: 'Analyze My Case Risk' },
          { action: 'explain_custody', label: 'Explain Custody Rights' },
          { action: 'collect_evidence', label: 'How to Collect Evidence' },
          { action: 'emergency_help', label: 'Emergency Situation' }
        ]
      }]);
    }
  }, [sessionId, user]);

  // Send message to AI
  const handleSendMessage = async (message = inputMessage) => {
    if (!message.trim() || isLoading) return;

    const userMessage = {
      id: Date.now().toString(),
      role: 'user',
      content: message,
      timestamp: new Date().toISOString()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setIsLoading(true);

    try {
      const response = await fetch('/api/ai/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          message: message,
          session_id: sessionId
        })
      });

      if (!response.ok) throw new Error('Failed to get AI response');

      const data = await response.json();

      const aiMessage = {
        id: Date.now().toString() + '_ai',
        role: 'assistant',
        content: data.message,
        timestamp: data.timestamp,
        quickActions: data.quick_actions || []
      };

      setMessages(prev => [...prev, aiMessage]);
    } catch (error) {
      console.error('AI Chat error:', error);

      const errorMessage = {
        id: Date.now().toString() + '_error',
        role: 'assistant',
        content: 'I apologize, but I encountered an error. Please try again or contact our support team if the problem persists.',
        timestamp: new Date().toISOString(),
        isError: true
      };

      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  // Handle quick action click
  const handleQuickAction = (action) => {
    const actionMessages = {
      'analyze_risk': 'I need help analyzing the risk level in my custody case.',
      'explain_custody': 'Can you explain custody rights and what they mean?',
      'collect_evidence': 'What evidence should I collect for my custody case?',
      'emergency_help': 'I have an emergency situation regarding my child\'s safety.',
      'write_document': 'I need help writing a legal document.',
      'get_legal_help': 'Where can I get legal help for my case?'
    };

    const message = actionMessages[action] || action;
    handleSendMessage(message);
  };

  // Clear chat
  const handleClearChat = () => {
    if (window.confirm('Are you sure you want to clear this chat? This cannot be undone.')) {
      setMessages([]);
      setSessionId(`session_${Date.now()}`);
    }
  };

  // Download chat history
  const handleDownloadChat = () => {
    const chatText = messages.map(msg =>
      `[${new Date(msg.timestamp).toLocaleString()}] ${msg.role === 'user' ? 'You' : 'AI Assistant'}:\n${msg.content}\n`
    ).join('\n');

    const blob = new Blob([chatText], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `ai-chat-${new Date().toISOString().split('T')[0]}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  // Copy message content
  const handleCopyMessage = (content, messageId) => {
    navigator.clipboard.writeText(content);
    setCopiedId(messageId);
    setTimeout(() => setCopiedId(null), 2000);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 via-pink-50 to-blue-50">
      <div className="max-w-6xl mx-auto p-4 md:p-6">
        {/* Header */}
        <div className="bg-white rounded-2xl shadow-lg p-6 mb-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="bg-gradient-to-br from-purple-500 to-pink-500 rounded-2xl p-3">
                <Bot className="text-white" size={32} />
              </div>
              <div>
                <h1 className="text-3xl font-bold text-gray-800 flex items-center gap-2">
                  Lawyer AI
                  <Sparkles className="text-yellow-500" size={24} />
                </h1>
                <p className="text-gray-600">Your 24/7 Legal Assistant - Powered by Claude AI</p>
              </div>
            </div>

            <div className="flex gap-2">
              <button
                onClick={handleDownloadChat}
                className="flex items-center gap-2 px-4 py-2 bg-blue-100 text-blue-700 rounded-lg hover:bg-blue-200 transition-colors"
                disabled={messages.length === 0}
              >
                <Download size={18} />
                <span className="hidden md:inline">Download</span>
              </button>
              <button
                onClick={handleClearChat}
                className="flex items-center gap-2 px-4 py-2 bg-red-100 text-red-700 rounded-lg hover:bg-red-200 transition-colors"
                disabled={messages.length === 0}
              >
                <Trash2 size={18} />
                <span className="hidden md:inline">Clear</span>
              </button>
            </div>
          </div>

          {/* AI Features Info */}
          <div className="mt-4 grid grid-cols-2 md:grid-cols-4 gap-3">
            <div className="flex items-center gap-2 text-sm text-gray-600">
              <Shield className="text-green-500" size={16} />
              <span>Risk Analysis</span>
            </div>
            <div className="flex items-center gap-2 text-sm text-gray-600">
              <FileText className="text-blue-500" size={16} />
              <span>Document Help</span>
            </div>
            <div className="flex items-center gap-2 text-sm text-gray-600">
              <Scale className="text-purple-500" size={16} />
              <span>Legal Guidance</span>
            </div>
            <div className="flex items-center gap-2 text-sm text-gray-600">
              <AlertCircle className="text-orange-500" size={16} />
              <span>24/7 Support</span>
            </div>
          </div>
        </div>

        {/* Chat Container */}
        <div className="bg-white rounded-2xl shadow-lg overflow-hidden">
          {/* Messages Area */}
          <div className="h-[600px] overflow-y-auto p-6 space-y-4">
            {messages.map((message) => (
              <div
                key={message.id}
                className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div
                  className={`max-w-[80%] ${
                    message.role === 'user'
                      ? 'bg-gradient-to-r from-pink-500 to-purple-500 text-white'
                      : message.isError
                      ? 'bg-red-50 border-2 border-red-200'
                      : 'bg-gray-100'
                  } rounded-2xl p-4 shadow-md relative group`}
                >
                  {/* Message Header */}
                  <div className="flex items-center justify-between mb-2">
                    <span className={`text-xs font-semibold ${
                      message.role === 'user' ? 'text-pink-100' : 'text-gray-500'
                    }`}>
                      {message.role === 'user' ? 'You' : 'Lawyer AI'}
                    </span>
                    <button
                      onClick={() => handleCopyMessage(message.content, message.id)}
                      className="opacity-0 group-hover:opacity-100 transition-opacity"
                    >
                      {copiedId === message.id ? (
                        <Check size={16} className={message.role === 'user' ? 'text-white' : 'text-green-600'} />
                      ) : (
                        <Copy size={16} className={message.role === 'user' ? 'text-white' : 'text-gray-400'} />
                      )}
                    </button>
                  </div>

                  {/* Message Content */}
                  <div className={`whitespace-pre-wrap ${
                    message.role === 'user' ? 'text-white' : 'text-gray-800'
                  }`}>
                    {message.content}
                  </div>

                  {/* Quick Actions */}
                  {message.quickActions && message.quickActions.length > 0 && (
                    <div className="mt-4 space-y-2">
                      <div className="text-xs text-gray-500 mb-2">Quick Actions:</div>
                      {message.quickActions.map((qa, idx) => (
                        <button
                          key={idx}
                          onClick={() => handleQuickAction(qa.action)}
                          className="block w-full text-left px-4 py-2 bg-white hover:bg-gray-50 text-gray-700 rounded-lg text-sm font-medium transition-colors border border-gray-200"
                        >
                          {qa.label}
                        </button>
                      ))}
                    </div>
                  )}

                  {/* Timestamp */}
                  <div className={`text-xs mt-2 ${
                    message.role === 'user' ? 'text-pink-100' : 'text-gray-400'
                  }`}>
                    {new Date(message.timestamp).toLocaleTimeString()}
                  </div>
                </div>
              </div>
            ))}

            {/* Loading Indicator */}
            {isLoading && (
              <div className="flex justify-start">
                <div className="bg-gray-100 rounded-2xl p-4 shadow-md">
                  <div className="flex items-center gap-2">
                    <div className="flex gap-1">
                      <div className="w-2 h-2 bg-purple-500 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                      <div className="w-2 h-2 bg-purple-500 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
                      <div className="w-2 h-2 bg-purple-500 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
                    </div>
                    <span className="text-gray-500 text-sm">AI is thinking...</span>
                  </div>
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>

          {/* Input Area */}
          <div className="border-t border-gray-200 p-4 bg-gray-50">
            <form
              onSubmit={(e) => {
                e.preventDefault();
                handleSendMessage();
              }}
              className="flex gap-3"
            >
              <input
                type="text"
                value={inputMessage}
                onChange={(e) => setInputMessage(e.target.value)}
                placeholder="Type your message here..."
                className="flex-1 px-4 py-3 border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                disabled={isLoading}
              />
              <button
                type="submit"
                disabled={isLoading || !inputMessage.trim()}
                className="bg-gradient-to-r from-purple-500 to-pink-500 text-white px-6 py-3 rounded-xl hover:from-purple-600 hover:to-pink-600 transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2 font-semibold"
              >
                <Send size={20} />
                <span className="hidden md:inline">Send</span>
              </button>
            </form>

            <div className="mt-3 text-xs text-gray-500 text-center">
              💡 AI can help with legal terms, risk analysis, document generation, and more. Ask anything!
            </div>
          </div>
        </div>

        {/* Footer Note */}
        <div className="mt-6 bg-yellow-50 border border-yellow-200 rounded-lg p-4">
          <div className="flex items-start gap-3">
            <AlertCircle className="text-yellow-600 flex-shrink-0 mt-0.5" size={20} />
            <div className="text-sm text-yellow-800">
              <strong>Important:</strong> This AI assistant provides general information and guidance.
              For complex legal matters or urgent situations, please use <strong>Live Chat</strong> to speak
              with a human expert or consult with a licensed attorney.
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AIChat;
