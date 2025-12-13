import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Network,
  Users,
  ArrowLeft,
  Search,
  Calendar,
  FileText,
  AlertTriangle,
  RefreshCw,
  ChevronDown
} from 'lucide-react';
import axios from 'axios';
import ContactNetworkGraph from '../components/ContactNetworkGraph';

const AdminContactNetwork = () => {
  const navigate = useNavigate();
  const [cases, setCases] = useState([]);
  const [selectedCase, setSelectedCase] = useState(null);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [showCaseDropdown, setShowCaseDropdown] = useState(false);
  const [selectedNodeDetails, setSelectedNodeDetails] = useState(null);

  // Fetch cases on mount
  useEffect(() => {
    fetchCases();
  }, []);

  const fetchCases = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get('/api/cases', {
        headers: { Authorization: `Bearer ${token}` }
      });
      setCases(response.data || []);

      // Auto-select first case with forensic data
      if (response.data?.length > 0) {
        const caseWithForensics = response.data.find(c =>
          c.has_forensics || c.forensic_status === 'completed'
        ) || response.data[0];
        setSelectedCase(caseWithForensics);
      }
    } catch (error) {
      console.error('Error fetching cases:', error);
    } finally {
      setLoading(false);
    }
  };

  const filteredCases = cases.filter(c =>
    c.case_number?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    c.client_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    c.title?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const handleNodeSelect = (node) => {
    setSelectedNodeDetails(node);
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <RefreshCw className="w-10 h-10 animate-spin text-blue-500 mx-auto mb-4" />
          <p className="text-gray-600">Davalar yükleniyor...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <button
                onClick={() => navigate('/admin/forensics')}
                className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
              >
                <ArrowLeft className="w-5 h-5" />
              </button>
              <div className="flex items-center gap-2">
                <Network className="w-6 h-6 text-blue-500" />
                <h1 className="text-xl font-bold text-gray-800">İletişim Ağı Analizi</h1>
              </div>
            </div>

            {/* Case Selector */}
            <div className="relative">
              <button
                onClick={() => setShowCaseDropdown(!showCaseDropdown)}
                className="flex items-center gap-2 px-4 py-2 bg-white border rounded-lg hover:bg-gray-50 transition-colors min-w-[250px]"
              >
                <FileText className="w-4 h-4 text-gray-400" />
                <span className="flex-1 text-left truncate">
                  {selectedCase
                    ? `${selectedCase.case_number} - ${selectedCase.client_name || selectedCase.title}`
                    : 'Dava Seçin'}
                </span>
                <ChevronDown className={`w-4 h-4 transition-transform ${showCaseDropdown ? 'rotate-180' : ''}`} />
              </button>

              {showCaseDropdown && (
                <div className="absolute right-0 mt-2 w-80 bg-white rounded-lg shadow-lg border z-50">
                  <div className="p-2 border-b">
                    <div className="relative">
                      <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                      <input
                        type="text"
                        placeholder="Dava ara..."
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                        className="w-full pl-10 pr-4 py-2 border rounded-lg text-sm"
                      />
                    </div>
                  </div>
                  <div className="max-h-64 overflow-y-auto">
                    {filteredCases.length === 0 ? (
                      <div className="p-4 text-center text-gray-500 text-sm">
                        Dava bulunamadı
                      </div>
                    ) : (
                      filteredCases.map(c => (
                        <button
                          key={c._id || c.case_id}
                          onClick={() => {
                            setSelectedCase(c);
                            setShowCaseDropdown(false);
                            setSearchTerm('');
                          }}
                          className={`w-full px-4 py-3 text-left hover:bg-gray-50 border-b last:border-0 transition-colors ${
                            selectedCase?._id === c._id ? 'bg-blue-50' : ''
                          }`}
                        >
                          <div className="font-medium text-sm text-gray-800">
                            {c.case_number}
                          </div>
                          <div className="text-xs text-gray-500 truncate">
                            {c.client_name || c.title}
                          </div>
                          <div className="flex items-center gap-2 mt-1">
                            <span className={`text-xs px-2 py-0.5 rounded ${
                              c.forensic_status === 'completed' ? 'bg-green-100 text-green-700' :
                              c.forensic_status === 'in_progress' ? 'bg-yellow-100 text-yellow-700' :
                              'bg-gray-100 text-gray-600'
                            }`}>
                              {c.forensic_status === 'completed' ? 'Tamamlandı' :
                               c.forensic_status === 'in_progress' ? 'Devam Ediyor' :
                               'Bekliyor'}
                            </span>
                          </div>
                        </button>
                      ))
                    )}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 py-6">
        {!selectedCase ? (
          <div className="bg-white rounded-lg shadow-lg p-12 text-center">
            <Network className="w-16 h-16 text-gray-300 mx-auto mb-4" />
            <h2 className="text-xl font-semibold text-gray-600 mb-2">
              Dava Seçilmedi
            </h2>
            <p className="text-gray-500">
              İletişim ağı grafiğini görüntülemek için bir dava seçin.
            </p>
          </div>
        ) : (
          <div className="space-y-6">
            {/* Case Info Bar */}
            <div className="bg-white rounded-lg shadow-lg p-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                  <div className="p-3 bg-blue-100 rounded-lg">
                    <Users className="w-6 h-6 text-blue-600" />
                  </div>
                  <div>
                    <h2 className="font-semibold text-gray-800">
                      {selectedCase.case_number}
                    </h2>
                    <p className="text-sm text-gray-500">
                      {selectedCase.client_name || selectedCase.title}
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-4 text-sm">
                  <div className="flex items-center gap-2 text-gray-500">
                    <Calendar className="w-4 h-4" />
                    <span>
                      {selectedCase.created_at
                        ? new Date(selectedCase.created_at).toLocaleDateString('tr-TR')
                        : 'Tarih yok'}
                    </span>
                  </div>
                </div>
              </div>
            </div>

            {/* Network Graph */}
            <ContactNetworkGraph
              caseId={selectedCase._id || selectedCase.case_id}
              onNodeSelect={handleNodeSelect}
            />

            {/* Help Section */}
            <div className="bg-blue-50 rounded-lg p-4">
              <h3 className="font-semibold text-blue-800 mb-2 flex items-center gap-2">
                <AlertTriangle className="w-4 h-4" />
                Kullanım İpuçları
              </h3>
              <ul className="text-sm text-blue-700 space-y-1">
                <li>• Düğümlere tıklayarak kişi detaylarını görüntüleyebilirsiniz</li>
                <li>• Mouse tekerleği ile yakınlaştırma/uzaklaştırma yapabilirsiniz</li>
                <li>• Sürükleyerek graf üzerinde gezinebilirsiniz</li>
                <li>• Büyük düğümler daha fazla mesajlaşma hacmini gösterir</li>
                <li>• Kalın kenarlar daha yoğun iletişimi temsil eder</li>
                <li>• Farklı renkler farklı platformları gösterir (WhatsApp: yeşil, SMS: mavi)</li>
              </ul>
            </div>
          </div>
        )}
      </main>
    </div>
  );
};

export default AdminContactNetwork;
