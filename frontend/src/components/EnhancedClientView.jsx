import React, { useState, useEffect } from 'react';
import {
  X, User, FolderOpen, Link2, Brain, Calendar,
  Mail, Phone, MapPin, CreditCard, Clock, Shield
} from 'lucide-react';
import { Button } from './ui/button';
import { Card, CardContent } from './ui/card';
import { Badge } from './ui/badge';
import ClientDataArchive from './ClientDataArchive';
import UnifiedLinkGenerator from './UnifiedLinkGenerator';

/**
 * EnhancedClientView Component
 * Comprehensive tabbed interface for viewing all client data
 * Tabs: Overview, Files & Evidence, Data Collection, AI Analysis
 */
const EnhancedClientView = ({ clientData, onClose, token }) => {
  const [activeTab, setActiveTab] = useState('overview');

  if (!clientData || !clientData.client) return null;

  const client = clientData.client;
  const documents = clientData.documents || [];

  const tabs = [
    { id: 'overview', label: 'Overview', icon: User },
    { id: 'files', label: 'Files & Evidence', icon: FolderOpen, badge: documents.length },
    { id: 'collection', label: 'Data Collection', icon: Link2 },
    { id: 'ai', label: 'AI Analysis', icon: Brain }
  ];

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-7xl max-h-[90vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="bg-gradient-to-r from-blue-600 to-purple-600 text-white px-6 py-4 flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold">
              {client.firstName} {client.lastName}
            </h2>
            <p className="text-sm text-blue-100 flex items-center gap-2 mt-1">
              <CreditCard className="w-4 h-4" />
              {client.clientNumber}
            </p>
          </div>
          <div className="flex items-center gap-3">
            <Badge variant="secondary" className="bg-white text-blue-600">
              {client.status || 'active'}
            </Badge>
            <Button variant="ghost" size="sm" onClick={onClose} className="text-white hover:bg-white/20">
              <X className="w-5 h-5" />
            </Button>
          </div>
        </div>

        {/* Tab Navigation */}
        <div className="border-b bg-gray-50">
          <div className="flex gap-1 px-6">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                className={`px-4 py-3 font-medium transition-all flex items-center gap-2 ${
                  activeTab === tab.id
                    ? 'text-blue-600 border-b-2 border-blue-600 bg-white'
                    : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
                }`}
                onClick={() => setActiveTab(tab.id)}
              >
                <tab.icon className="w-4 h-4" />
                {tab.label}
                {tab.badge !== undefined && (
                  <Badge variant="secondary" className="ml-1 text-xs">
                    {tab.badge}
                  </Badge>
                )}
              </button>
            ))}
          </div>
        </div>

        {/* Tab Content */}
        <div className="flex-1 overflow-y-auto p-6">
          {activeTab === 'overview' && (
            <div className="space-y-6">
              {/* Client Information */}
              <Card>
                <CardContent className="p-6">
                  <h3 className="text-lg font-bold text-gray-900 mb-4 flex items-center gap-2">
                    <User className="w-5 h-5 text-blue-600" />
                    Client Information
                  </h3>
                  <div className="grid md:grid-cols-2 gap-6">
                    <div>
                      <label className="text-sm font-medium text-gray-500">Full Name</label>
                      <p className="text-lg font-semibold text-gray-900">
                        {client.firstName} {client.lastName}
                      </p>
                    </div>
                    <div>
                      <label className="text-sm font-medium text-gray-500">Client Number</label>
                      <p className="font-mono text-sm text-gray-900">{client.clientNumber}</p>
                    </div>
                    <div>
                      <label className="text-sm font-medium text-gray-500 flex items-center gap-1">
                        <Mail className="w-4 h-4" />
                        Email
                      </label>
                      <p className="text-gray-900">{client.email || '-'}</p>
                    </div>
                    <div>
                      <label className="text-sm font-medium text-gray-500 flex items-center gap-1">
                        <Phone className="w-4 h-4" />
                        Phone
                      </label>
                      <p className="text-gray-900">{client.phone || '-'}</p>
                    </div>
                    <div>
                      <label className="text-sm font-medium text-gray-500 flex items-center gap-1">
                        <MapPin className="w-4 h-4" />
                        Country
                      </label>
                      <p className="text-gray-900">{client.country || '-'}</p>
                    </div>
                    <div>
                      <label className="text-sm font-medium text-gray-500 flex items-center gap-1">
                        <Shield className="w-4 h-4" />
                        Case Type
                      </label>
                      <p className="text-gray-900">{client.caseType || '-'}</p>
                    </div>
                    <div>
                      <label className="text-sm font-medium text-gray-500">Status</label>
                      <Badge className={
                        client.status === 'active' ? 'bg-green-100 text-green-700' :
                        client.status === 'pending' ? 'bg-yellow-100 text-yellow-700' :
                        'bg-gray-100 text-gray-700'
                      }>
                        {client.status || 'active'}
                      </Badge>
                    </div>
                    <div>
                      <label className="text-sm font-medium text-gray-500 flex items-center gap-1">
                        <Clock className="w-4 h-4" />
                        Registration Date
                      </label>
                      <p className="text-gray-900">
                        {client.createdAt
                          ? new Date(client.createdAt).toLocaleDateString()
                          : '-'}
                      </p>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Quick Stats */}
              <div className="grid grid-cols-3 gap-4">
                <Card>
                  <CardContent className="p-4 text-center">
                    <div className="text-3xl font-bold text-blue-600">{documents.length}</div>
                    <div className="text-sm text-gray-600 mt-1">Documents</div>
                  </CardContent>
                </Card>
                <Card>
                  <CardContent className="p-4 text-center">
                    <div className="text-3xl font-bold text-green-600">
                      {documents.filter(d => d.fileType?.includes('image')).length}
                    </div>
                    <div className="text-sm text-gray-600 mt-1">Images</div>
                  </CardContent>
                </Card>
                <Card>
                  <CardContent className="p-4 text-center">
                    <div className="text-3xl font-bold text-purple-600">
                      {documents.filter(d => d.fileType?.includes('video')).length}
                    </div>
                    <div className="text-sm text-gray-600 mt-1">Videos</div>
                  </CardContent>
                </Card>
              </div>

              {/* Recent Activity */}
              <Card>
                <CardContent className="p-6">
                  <h3 className="text-lg font-bold text-gray-900 mb-4 flex items-center gap-2">
                    <Calendar className="w-5 h-5 text-purple-600" />
                    Recent Activity
                  </h3>
                  {documents.length > 0 ? (
                    <div className="space-y-3">
                      {documents.slice(0, 5).map((doc, idx) => (
                        <div
                          key={idx}
                          className="flex items-center justify-between py-2 border-b last:border-b-0"
                        >
                          <div>
                            <p className="font-medium text-gray-900">{doc.fileName}</p>
                            <p className="text-xs text-gray-500">
                              {doc.uploadedAt
                                ? new Date(doc.uploadedAt).toLocaleString()
                                : 'Unknown date'}
                            </p>
                          </div>
                          <Badge variant="outline">{doc.fileType?.split('/')[0] || 'file'}</Badge>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-gray-500 text-center py-4">No activity yet</p>
                  )}
                </CardContent>
              </Card>
            </div>
          )}

          {activeTab === 'files' && (
            <ClientDataArchive clientNumber={client.clientNumber} token={token} />
          )}

          {activeTab === 'collection' && (
            <UnifiedLinkGenerator
              clientNumber={client.clientNumber}
              clientInfo={client}
              token={token}
            />
          )}

          {activeTab === 'ai' && (
            <div className="space-y-6">
              <Card>
                <CardContent className="p-6">
                  <h3 className="text-lg font-bold text-gray-900 mb-4 flex items-center gap-2">
                    <Brain className="w-5 h-5 text-purple-600" />
                    AI-Powered Analysis Tools
                  </h3>
                  <p className="text-gray-600 mb-6">
                    Use our AI tools to analyze case data, generate documents, and detect patterns.
                  </p>

                  <div className="grid md:grid-cols-2 gap-4">
                    {/* AI Features */}
                    <Card className="border-2 border-purple-100 hover:border-purple-300 transition-all cursor-pointer">
                      <CardContent className="p-4">
                        <h4 className="font-semibold text-gray-900 mb-2">Risk Analysis</h4>
                        <p className="text-sm text-gray-600 mb-3">
                          Assess child safety risks with 0-10 scoring
                        </p>
                        <Button className="w-full" size="sm">
                          Run Analysis
                        </Button>
                      </CardContent>
                    </Card>

                    <Card className="border-2 border-blue-100 hover:border-blue-300 transition-all cursor-pointer">
                      <CardContent className="p-4">
                        <h4 className="font-semibold text-gray-900 mb-2">Document Generation</h4>
                        <p className="text-sm text-gray-600 mb-3">
                          Generate court-ready petitions and documents
                        </p>
                        <Button className="w-full" size="sm">
                          Generate Document
                        </Button>
                      </CardContent>
                    </Card>

                    <Card className="border-2 border-green-100 hover:border-green-300 transition-all cursor-pointer">
                      <CardContent className="p-4">
                        <h4 className="font-semibold text-gray-900 mb-2">Evidence Analysis</h4>
                        <p className="text-sm text-gray-600 mb-3">
                          Organize and analyze evidence with AI assistance
                        </p>
                        <Button className="w-full" size="sm">
                          Analyze Evidence
                        </Button>
                      </CardContent>
                    </Card>

                    <Card className="border-2 border-orange-100 hover:border-orange-300 transition-all cursor-pointer">
                      <CardContent className="p-4">
                        <h4 className="font-semibold text-gray-900 mb-2">Alienation Detection</h4>
                        <p className="text-sm text-gray-600 mb-3">
                          Detect parental alienation patterns in case data
                        </p>
                        <Button className="w-full" size="sm">
                          Detect Patterns
                        </Button>
                      </CardContent>
                    </Card>

                    <Card className="border-2 border-indigo-100 hover:border-indigo-300 transition-all cursor-pointer">
                      <CardContent className="p-4">
                        <h4 className="font-semibold text-gray-900 mb-2">Timeline Generator</h4>
                        <p className="text-sm text-gray-600 mb-3">
                          Create chronological timeline of case events
                        </p>
                        <Button className="w-full" size="sm">
                          Generate Timeline
                        </Button>
                      </CardContent>
                    </Card>

                    <Card className="border-2 border-pink-100 hover:border-pink-300 transition-all cursor-pointer">
                      <CardContent className="p-4">
                        <h4 className="font-semibold text-gray-900 mb-2">Case Summary</h4>
                        <p className="text-sm text-gray-600 mb-3">
                          Generate comprehensive case summary for court
                        </p>
                        <Button className="w-full" size="sm">
                          Create Summary
                        </Button>
                      </CardContent>
                    </Card>
                  </div>

                  <div className="mt-6 bg-purple-50 border border-purple-200 rounded-lg p-4">
                    <p className="text-sm text-purple-800">
                      <strong>Note:</strong> AI analysis features use Claude AI to provide
                      intelligent insights. All data is processed securely and confidentially.
                    </p>
                  </div>
                </CardContent>
              </Card>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default EnhancedClientView;
