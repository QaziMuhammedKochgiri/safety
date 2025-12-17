import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  MapPin,
  ArrowLeft,
  Search,
  Calendar,
  FileText,
  AlertTriangle,
  RefreshCw,
  ChevronDown,
  Upload,
  Info,
  Image,
  Download
} from 'lucide-react';
import axios from 'axios';
import LocationMap from '../components/LocationMap';

const AdminLocationMap = () => {
  const navigate = useNavigate();
  const [cases, setCases] = useState([]);
  const [selectedCase, setSelectedCase] = useState(null);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [showCaseDropdown, setShowCaseDropdown] = useState(false);
  const [selectedLocation, setSelectedLocation] = useState(null);

  // Image upload
  const [uploadingImages, setUploadingImages] = useState(false);
  const [uploadResult, setUploadResult] = useState(null);
  const fileInputRef = useRef(null);

  // Fetch cases on mount
  useEffect(() => {
    fetchCases();
  }, []);

  const fetchCases = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get('/api/admin/forensics', {
        headers: { Authorization: `Bearer ${token}` }
      });
      // Response format: { cases: [...], total: N }
      const forensicCases = response.data.cases || [];
      setCases(forensicCases);

      // Auto-select first completed case (only completed cases have location data)
      if (forensicCases.length > 0) {
        const completedCase = forensicCases.find(c => c.status === 'completed') || forensicCases[0];
        setSelectedCase(completedCase);
      }
    } catch (error) {
      console.error('Error fetching cases:', error);
    } finally {
      setLoading(false);
    }
  };

  const filteredCases = cases.filter(c =>
    c.case_id?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    c.case_number?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    c.client_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    c.title?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    c.uploaded_file?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const handleLocationSelect = (location) => {
    setSelectedLocation(location);
  };

  // Handle image upload for GPS extraction
  const handleImageUpload = async (event) => {
    const files = event.target.files;
    if (!files || files.length === 0 || !selectedCase) return;

    setUploadingImages(true);
    setUploadResult(null);

    try {
      const token = localStorage.getItem('token');
      const formData = new FormData();

      for (let i = 0; i < files.length; i++) {
        formData.append('files', files[i]);
      }

      const caseId = selectedCase._id || selectedCase.case_id;
      const response = await axios.post(
        `/api/locations/${caseId}/extract-from-images`,
        formData,
        {
          headers: {
            Authorization: `Bearer ${token}`,
            'Content-Type': 'multipart/form-data'
          }
        }
      );

      setUploadResult({
        success: true,
        uploaded: response.data.uploadedFiles,
        extracted: response.data.extractedLocations
      });

      // Reset file input
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    } catch (error) {
      console.error('Error uploading images:', error);
      setUploadResult({
        success: false,
        error: error.response?.data?.detail || 'Fotoğraf yüklenirken hata oluştu'
      });
    } finally {
      setUploadingImages(false);
    }
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
                <MapPin className="w-6 h-6 text-green-500" />
                <h1 className="text-xl font-bold text-gray-800">GPS Konum Haritası</h1>
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
                    ? `${selectedCase.case_id} - ${selectedCase.uploaded_file || selectedCase.title || 'Forensic Case'}`
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
                            setUploadResult(null);
                          }}
                          className={`w-full px-4 py-3 text-left hover:bg-gray-50 border-b last:border-0 transition-colors ${
                            selectedCase?.case_id === c.case_id ? 'bg-green-50' : ''
                          }`}
                        >
                          <div className="font-medium text-sm text-gray-800">
                            {c.case_id}
                          </div>
                          <div className="text-xs text-gray-500 truncate">
                            {c.uploaded_file || c.title || 'Forensic Analysis'}
                          </div>
                          <div className="flex items-center gap-2 mt-1">
                            <span className={`text-xs px-2 py-0.5 rounded ${
                              c.status === 'completed' ? 'bg-green-100 text-green-700' :
                              c.status === 'processing' ? 'bg-yellow-100 text-yellow-700' :
                              c.status === 'failed' ? 'bg-red-100 text-red-700' :
                              'bg-gray-100 text-gray-600'
                            }`}>
                              {c.status === 'completed' ? 'Tamamlandı' :
                               c.status === 'processing' ? 'İşleniyor' :
                               c.status === 'failed' ? 'Başarısız' :
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
            <MapPin className="w-16 h-16 text-gray-300 mx-auto mb-4" />
            <h2 className="text-xl font-semibold text-gray-600 mb-2">
              Dava Seçilmedi
            </h2>
            <p className="text-gray-500">
              GPS konum haritasını görüntülemek için bir dava seçin.
            </p>
          </div>
        ) : (
          <div className="space-y-6">
            {/* Case Info Bar */}
            <div className="bg-white rounded-lg shadow-lg p-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                  <div className="p-3 bg-green-100 rounded-lg">
                    <MapPin className="w-6 h-6 text-green-600" />
                  </div>
                  <div>
                    <h2 className="font-semibold text-gray-800">
                      {selectedCase.case_id}
                    </h2>
                    <p className="text-sm text-gray-500">
                      {selectedCase.uploaded_file || selectedCase.title || 'Forensic Analysis'}
                    </p>
                  </div>
                </div>

                {/* Upload Images Button */}
                <div className="flex items-center gap-4">
                  <div className="flex items-center gap-2 text-sm text-gray-500">
                    <Calendar className="w-4 h-4" />
                    <span>
                      {selectedCase.created_at
                        ? new Date(selectedCase.created_at).toLocaleDateString('tr-TR')
                        : 'Tarih yok'}
                    </span>
                  </div>

                  <div>
                    <input
                      type="file"
                      ref={fileInputRef}
                      onChange={handleImageUpload}
                      accept="image/jpeg,image/jpg,image/tiff,image/png"
                      multiple
                      className="hidden"
                    />
                    <button
                      onClick={() => fileInputRef.current?.click()}
                      disabled={uploadingImages}
                      className="flex items-center gap-2 px-4 py-2 bg-green-500 text-white rounded-lg hover:bg-green-600 transition-colors disabled:opacity-50"
                    >
                      {uploadingImages ? (
                        <>
                          <RefreshCw className="w-4 h-4 animate-spin" />
                          Yükleniyor...
                        </>
                      ) : (
                        <>
                          <Upload className="w-4 h-4" />
                          Fotoğraf Yükle
                        </>
                      )}
                    </button>
                  </div>
                </div>
              </div>

              {/* Upload Result */}
              {uploadResult && (
                <div className={`mt-4 p-3 rounded-lg ${
                  uploadResult.success ? 'bg-green-50' : 'bg-red-50'
                }`}>
                  {uploadResult.success ? (
                    <div className="flex items-center gap-2 text-green-700">
                      <Image className="w-4 h-4" />
                      <span>
                        {uploadResult.uploaded} fotoğraf yüklendi, {uploadResult.extracted} GPS konumu çıkarıldı.
                      </span>
                    </div>
                  ) : (
                    <div className="flex items-center gap-2 text-red-700">
                      <AlertTriangle className="w-4 h-4" />
                      <span>{uploadResult.error}</span>
                    </div>
                  )}
                </div>
              )}
            </div>

            {/* Location Map */}
            <LocationMap
              caseId={selectedCase._id || selectedCase.case_id}
              onLocationSelect={handleLocationSelect}
            />

            {/* Help Section */}
            <div className="bg-green-50 rounded-lg p-4">
              <h3 className="font-semibold text-green-800 mb-2 flex items-center gap-2">
                <Info className="w-4 h-4" />
                Kullanım İpuçları
              </h3>
              <ul className="text-sm text-green-700 space-y-1">
                <li>• Harita üzerindeki noktalara tıklayarak konum detaylarını görüntüleyebilirsiniz</li>
                <li>• Mouse tekerleği ile yakınlaştırma/uzaklaştırma yapabilirsiniz</li>
                <li>• Isı haritası modu ile en sık ziyaret edilen bölgeleri görebilirsiniz</li>
                <li>• Timeline kontrolü ile kronolojik hareket takibi yapabilirsiniz</li>
                <li>• Fotoğraf yükleyerek EXIF GPS verilerini otomatik çıkarabilirsiniz</li>
                <li>• Farklı renkler farklı veri kaynaklarını gösterir (EXIF, Google Geçmişi, WhatsApp)</li>
                <li>• Kırmızı daireler sık ziyaret edilen konumları temsil eder</li>
              </ul>
            </div>

            {/* Data Sources Info */}
            <div className="bg-white rounded-lg shadow-lg p-4">
              <h3 className="font-semibold text-gray-800 mb-3 flex items-center gap-2">
                <AlertTriangle className="w-4 h-4 text-amber-500" />
                Desteklenen Veri Kaynakları
              </h3>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="p-3 bg-gray-50 rounded-lg">
                  <div className="flex items-center gap-2 mb-1">
                    <div className="w-3 h-3 rounded-full bg-green-500"></div>
                    <span className="font-medium text-sm">EXIF</span>
                  </div>
                  <p className="text-xs text-gray-500">Fotoğraf GPS verileri</p>
                </div>
                <div className="p-3 bg-gray-50 rounded-lg">
                  <div className="flex items-center gap-2 mb-1">
                    <div className="w-3 h-3 rounded-full bg-blue-500"></div>
                    <span className="font-medium text-sm">Google</span>
                  </div>
                  <p className="text-xs text-gray-500">Konum geçmişi</p>
                </div>
                <div className="p-3 bg-gray-50 rounded-lg">
                  <div className="flex items-center gap-2 mb-1">
                    <div className="w-3 h-3 rounded-full bg-purple-500"></div>
                    <span className="font-medium text-sm">iOS</span>
                  </div>
                  <p className="text-xs text-gray-500">Önemli konumlar</p>
                </div>
                <div className="p-3 bg-gray-50 rounded-lg">
                  <div className="flex items-center gap-2 mb-1">
                    <div className="w-3 h-3 rounded-full bg-emerald-500"></div>
                    <span className="font-medium text-sm">WhatsApp</span>
                  </div>
                  <p className="text-xs text-gray-500">Paylaşılan konumlar</p>
                </div>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
};

export default AdminLocationMap;
