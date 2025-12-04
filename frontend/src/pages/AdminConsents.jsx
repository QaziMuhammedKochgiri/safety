import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { useLanguage } from '../contexts/LanguageContext';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Input } from '../components/ui/input';
import { Badge } from '../components/ui/badge';
import { toast } from 'sonner';
import {
  ArrowLeft,
  Search,
  Shield,
  CheckCircle,
  XCircle,
  Clock,
  Loader2,
  User,
  Calendar,
  Globe,
  Monitor,
  FileCheck
} from 'lucide-react';
import axios from 'axios';

const API_URL = '/api';

const AdminConsents = () => {
  const { language } = useLanguage();
  const { token } = useAuth();
  const navigate = useNavigate();
  const [consents, setConsents] = useState([]);
  const [filteredConsents, setFilteredConsents] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState({ total: 0, accepted: 0, rejected: 0 });

  useEffect(() => {
    fetchConsents();
  }, []);

  useEffect(() => {
    if (searchTerm) {
      const filtered = consents.filter(c =>
        c.clientNumber?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        c.type?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        c.ipAddress?.includes(searchTerm)
      );
      setFilteredConsents(filtered);
    } else {
      setFilteredConsents(consents);
    }
  }, [searchTerm, consents]);

  const fetchConsents = async () => {
    try {
      const response = await axios.get(`${API_URL}/consent/logs`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      const logs = response.data.logs || [];
      setConsents(logs);
      setFilteredConsents(logs);

      // Calculate stats
      const accepted = logs.filter(c => c.accepted).length;
      setStats({
        total: logs.length,
        accepted,
        rejected: logs.length - accepted
      });
    } catch (error) {
      console.error('Error:', error);
      toast.error('Failed to load consent logs');
    } finally {
      setLoading(false);
    }
  };

  const getConsentTypeLabel = (type) => {
    const types = {
      'privacy': 'Privacy Policy',
      'terms': 'Terms of Service',
      'cookies': 'Cookie Consent',
      'marketing': 'Marketing',
      'data_processing': 'Data Processing',
      'chat': 'Chat Consent'
    };
    return types[type] || type;
  };

  const getConsentTypeBadge = (type) => {
    const colors = {
      'privacy': 'bg-blue-100 text-blue-800',
      'terms': 'bg-purple-100 text-purple-800',
      'cookies': 'bg-yellow-100 text-yellow-800',
      'marketing': 'bg-green-100 text-green-800',
      'data_processing': 'bg-red-100 text-red-800',
      'chat': 'bg-pink-100 text-pink-800'
    };
    return colors[type] || 'bg-gray-100 text-gray-800';
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="bg-white border-b">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center space-x-4">
            <Button variant="ghost" onClick={() => navigate('/admin')}>
              <ArrowLeft className="w-4 h-4 mr-2" />
              {language === 'de' ? 'Zuruck' : 'Back'}
            </Button>
            <div>
              <h1 className="text-2xl font-bold">
                {language === 'de' ? 'Einwilligungen' : 'Consent Logs'}
              </h1>
              <p className="text-gray-500">
                {language === 'de' ? 'DSGVO Einwilligungsprotokolle' : 'GDPR Consent Records'}
              </p>
            </div>
          </div>
        </div>
      </div>

      <div className="container mx-auto px-4 py-8">
        {/* Stats */}
        <div className="grid grid-cols-3 gap-4 mb-6">
          <Card>
            <CardContent className="p-4 text-center">
              <Shield className="w-8 h-8 mx-auto mb-2 text-blue-600" />
              <p className="text-2xl font-bold">{stats.total}</p>
              <p className="text-xs text-gray-500">
                {language === 'de' ? 'Gesamt' : 'Total'}
              </p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4 text-center">
              <CheckCircle className="w-8 h-8 mx-auto mb-2 text-green-600" />
              <p className="text-2xl font-bold">{stats.accepted}</p>
              <p className="text-xs text-gray-500">
                {language === 'de' ? 'Akzeptiert' : 'Accepted'}
              </p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4 text-center">
              <XCircle className="w-8 h-8 mx-auto mb-2 text-red-600" />
              <p className="text-2xl font-bold">{stats.rejected}</p>
              <p className="text-xs text-gray-500">
                {language === 'de' ? 'Abgelehnt' : 'Rejected'}
              </p>
            </CardContent>
          </Card>
        </div>

        {/* Search */}
        <Card className="mb-6">
          <CardContent className="p-4">
            <div className="relative">
              <Search className="absolute left-3 top-3 w-4 h-4 text-gray-400" />
              <Input
                placeholder={language === 'de' ? 'Nach Client oder IP suchen...' : 'Search by client or IP...'}
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10"
              />
            </div>
          </CardContent>
        </Card>

        {/* Consent Logs */}
        {loading ? (
          <div className="flex justify-center py-12">
            <Loader2 className="h-8 w-8 animate-spin text-gray-400" />
          </div>
        ) : filteredConsents.length === 0 ? (
          <Card>
            <CardContent className="p-12 text-center">
              <Shield className="w-12 h-12 mx-auto mb-4 text-gray-300" />
              <p className="text-gray-500">
                {language === 'de' ? 'Keine Einwilligungen gefunden' : 'No consent logs found'}
              </p>
            </CardContent>
          </Card>
        ) : (
          <div className="space-y-3">
            {filteredConsents.map((consent, index) => (
              <Card key={consent._id || index} className="hover:shadow-md transition-shadow">
                <CardContent className="p-4">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-4">
                      {consent.accepted ? (
                        <CheckCircle className="w-6 h-6 text-green-600" />
                      ) : (
                        <XCircle className="w-6 h-6 text-red-600" />
                      )}
                      <div>
                        <div className="flex items-center space-x-2 mb-1">
                          <span className={`px-2 py-1 rounded text-xs font-medium ${getConsentTypeBadge(consent.type)}`}>
                            {getConsentTypeLabel(consent.type)}
                          </span>
                          <Badge variant={consent.accepted ? 'default' : 'destructive'}>
                            {consent.accepted ? 'Accepted' : 'Rejected'}
                          </Badge>
                        </div>
                        <div className="flex flex-wrap items-center gap-3 text-sm text-gray-500">
                          {consent.clientNumber && (
                            <span className="flex items-center">
                              <User className="w-3 h-3 mr-1" />
                              {consent.clientNumber}
                            </span>
                          )}
                          <span className="flex items-center">
                            <Calendar className="w-3 h-3 mr-1" />
                            {new Date(consent.timestamp).toLocaleString('de-DE')}
                          </span>
                          {consent.ipAddress && (
                            <span className="flex items-center">
                              <Globe className="w-3 h-3 mr-1" />
                              {consent.ipAddress}
                            </span>
                          )}
                        </div>
                      </div>
                    </div>
                    <div className="text-right text-xs text-gray-400">
                      {consent.userAgent && (
                        <div className="flex items-center justify-end">
                          <Monitor className="w-3 h-3 mr-1" />
                          <span className="max-w-[200px] truncate">{consent.userAgent}</span>
                        </div>
                      )}
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default AdminConsents;
