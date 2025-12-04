import React, { useState, useEffect, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";
import { toast } from "sonner";
import {
  FileText,
  Plus,
  Search,
  Filter,
  Eye,
  Edit2,
  Trash2,
  Download,
  Copy,
  RefreshCw,
  ChevronRight,
  Scale,
  Globe,
  Shield,
  FileCheck,
  Mail,
  Gavel,
  Users,
  Bell,
  Sparkles,
  X,
  Check,
  Printer
} from "lucide-react";

const API_URL = process.env.REACT_APP_API_URL || "http://localhost:8000";

// Category icons
const categoryIcons = {
  custody: Scale,
  hague: Globe,
  forensic: Shield,
  consent: FileCheck,
  correspondence: Mail,
  court: Gavel,
  agreement: Users,
  notification: Bell
};

export default function AdminTemplates() {
  const { token } = useAuth();
  const navigate = useNavigate();

  // State
  const [loading, setLoading] = useState(true);
  const [templates, setTemplates] = useState([]);
  const [categories, setCategories] = useState([]);
  const [selectedCategory, setSelectedCategory] = useState("");
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedTemplate, setSelectedTemplate] = useState(null);
  const [showGenerateModal, setShowGenerateModal] = useState(false);
  const [showPreviewModal, setShowPreviewModal] = useState(false);
  const [generatedContent, setGeneratedContent] = useState("");
  const [formData, setFormData] = useState({});
  const [clients, setClients] = useState([]);
  const [cases, setCases] = useState([]);
  const [generatedDocs, setGeneratedDocs] = useState([]);

  // Fetch templates
  const fetchTemplates = useCallback(async () => {
    try {
      const params = new URLSearchParams();
      if (selectedCategory) params.append("category", selectedCategory);
      if (searchQuery) params.append("search", searchQuery);

      const res = await fetch(`${API_URL}/api/templates?${params}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setTemplates(data.templates || []);
      }
    } catch (error) {
      console.error("Templates fetch error:", error);
    }
  }, [token, selectedCategory, searchQuery]);

  // Fetch categories
  const fetchCategories = useCallback(async () => {
    try {
      const res = await fetch(`${API_URL}/api/templates/categories`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setCategories(data.categories || []);
      }
    } catch (error) {
      console.error("Categories fetch error:", error);
    }
  }, [token]);

  // Fetch clients for autofill
  const fetchClients = useCallback(async () => {
    try {
      const res = await fetch(`${API_URL}/api/clients?limit=100`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setClients(data.clients || []);
      }
    } catch (error) {
      console.error("Clients fetch error:", error);
    }
  }, [token]);

  // Fetch cases
  const fetchCases = useCallback(async () => {
    try {
      const res = await fetch(`${API_URL}/api/cases?limit=100`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setCases(data.cases || []);
      }
    } catch (error) {
      console.error("Cases fetch error:", error);
    }
  }, [token]);

  // Fetch generated documents
  const fetchGeneratedDocs = useCallback(async () => {
    try {
      const res = await fetch(`${API_URL}/api/templates/generated/list?limit=20`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setGeneratedDocs(data.documents || []);
      }
    } catch (error) {
      console.error("Generated docs fetch error:", error);
    }
  }, [token]);

  // Initial load
  useEffect(() => {
    const loadData = async () => {
      setLoading(true);
      await Promise.all([
        fetchTemplates(),
        fetchCategories(),
        fetchClients(),
        fetchCases(),
        fetchGeneratedDocs()
      ]);
      setLoading(false);
    };
    loadData();
  }, [fetchTemplates, fetchCategories, fetchClients, fetchCases, fetchGeneratedDocs]);

  // Reload when filter changes
  useEffect(() => {
    fetchTemplates();
  }, [fetchTemplates]);

  // Open generate modal
  const openGenerateModal = async (template) => {
    setSelectedTemplate(template);
    setFormData({});

    // Get full template details
    try {
      const res = await fetch(`${API_URL}/api/templates/${template.template_id}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        const fullTemplate = await res.json();
        setSelectedTemplate(fullTemplate);
      }
    } catch (error) {
      console.error("Template detail error:", error);
    }

    setShowGenerateModal(true);
  };

  // Auto-fill from client/case
  const handleAutofill = async (type, id) => {
    try {
      const params = new URLSearchParams();
      if (type === "client") params.append("client_number", id);
      if (type === "case") params.append("case_id", id);

      const res = await fetch(
        `${API_URL}/api/templates/${selectedTemplate.template_id}/autofill?${params}`,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      if (res.ok) {
        const data = await res.json();
        setFormData((prev) => ({ ...prev, ...data.autofill }));
        toast.success("Veriler otomatik dolduruldu");
      }
    } catch (error) {
      toast.error("Oto-doldurma hatası");
    }
  };

  // Preview document
  const handlePreview = async () => {
    try {
      const res = await fetch(`${API_URL}/api/templates/${selectedTemplate.template_id}/preview`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({ variables: formData })
      });
      if (res.ok) {
        const data = await res.json();
        setGeneratedContent(data.preview);
        setShowPreviewModal(true);
      }
    } catch (error) {
      toast.error("Önizleme hatası");
    }
  };

  // Generate document
  const handleGenerate = async () => {
    try {
      const res = await fetch(`${API_URL}/api/templates/${selectedTemplate.template_id}/generate`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({ variables: formData })
      });
      if (res.ok) {
        const data = await res.json();
        setGeneratedContent(data.content);
        setShowGenerateModal(false);
        setShowPreviewModal(true);
        fetchGeneratedDocs();
        toast.success("Belge oluşturuldu");
      } else {
        const err = await res.json();
        toast.error(err.detail || "Belge oluşturma hatası");
      }
    } catch (error) {
      toast.error("Belge oluşturma hatası");
    }
  };

  // Copy to clipboard
  const copyToClipboard = () => {
    navigator.clipboard.writeText(generatedContent);
    toast.success("Panoya kopyalandı");
  };

  // Print document
  const printDocument = () => {
    const printWindow = window.open("", "_blank");
    printWindow.document.write(`
      <html>
        <head>
          <title>${selectedTemplate?.name || "Belge"}</title>
          <style>
            body { font-family: 'Times New Roman', serif; padding: 40px; line-height: 1.6; }
            pre { white-space: pre-wrap; font-family: inherit; }
          </style>
        </head>
        <body>
          <pre>${generatedContent}</pre>
        </body>
      </html>
    `);
    printWindow.document.close();
    printWindow.print();
  };

  // Template Card Component
  const TemplateCard = ({ template }) => {
    const IconComponent = categoryIcons[template.category] || FileText;

    return (
      <div className="bg-white rounded-xl p-5 shadow-sm border border-gray-100 hover:shadow-md transition-all hover:border-indigo-200">
        <div className="flex items-start gap-4">
          <div className={`p-3 rounded-xl ${
            template.is_builtin ? "bg-gradient-to-br from-indigo-100 to-purple-100" : "bg-gray-100"
          }`}>
            <IconComponent className={`w-6 h-6 ${template.is_builtin ? "text-indigo-600" : "text-gray-600"}`} />
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2">
              <h3 className="font-semibold text-gray-900 truncate">{template.name}</h3>
              {template.is_builtin && (
                <span className="px-2 py-0.5 bg-indigo-100 text-indigo-700 text-xs font-medium rounded-full">
                  Yerleşik
                </span>
              )}
            </div>
            <p className="text-sm text-gray-500 mt-1 line-clamp-2">{template.description}</p>
            <div className="flex items-center gap-3 mt-3">
              <span className="text-xs text-gray-400">
                {categories.find((c) => c.id === template.category)?.name || template.category}
              </span>
              <span className="text-xs text-gray-400">
                {template.language === "en" ? "English" : "Türkçe"}
              </span>
              <span className="text-xs text-gray-400">
                {template.variables?.length || 0} değişken
              </span>
            </div>
          </div>
          <button
            onClick={() => openGenerateModal(template)}
            className="flex items-center gap-1 px-3 py-2 bg-indigo-600 text-white rounded-lg text-sm font-medium hover:bg-indigo-700"
          >
            <Sparkles className="w-4 h-4" />
            Oluştur
          </button>
        </div>
      </div>
    );
  };

  // Generate Modal
  const GenerateModal = () => {
    if (!selectedTemplate) return null;

    return (
      <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
        <div className="bg-white rounded-xl shadow-xl max-w-2xl w-full max-h-[90vh] overflow-hidden">
          <div className="p-6 border-b flex items-center justify-between">
            <div>
              <h3 className="text-lg font-semibold text-gray-900">{selectedTemplate.name}</h3>
              <p className="text-sm text-gray-500">Belge oluşturmak için alanları doldurun</p>
            </div>
            <button onClick={() => setShowGenerateModal(false)} className="p-2 hover:bg-gray-100 rounded-lg">
              <X className="w-5 h-5 text-gray-500" />
            </button>
          </div>

          <div className="p-6 overflow-y-auto max-h-[60vh]">
            {/* Auto-fill options */}
            <div className="mb-6 p-4 bg-gray-50 rounded-lg">
              <p className="text-sm font-medium text-gray-700 mb-3">Otomatik Doldur:</p>
              <div className="flex flex-wrap gap-3">
                <select
                  onChange={(e) => e.target.value && handleAutofill("client", e.target.value)}
                  className="px-3 py-2 border rounded-lg text-sm"
                  defaultValue=""
                >
                  <option value="">Müvekkil seç...</option>
                  {clients.map((c) => (
                    <option key={c.clientNumber} value={c.clientNumber}>
                      {c.name} ({c.clientNumber})
                    </option>
                  ))}
                </select>
                <select
                  onChange={(e) => e.target.value && handleAutofill("case", e.target.value)}
                  className="px-3 py-2 border rounded-lg text-sm"
                  defaultValue=""
                >
                  <option value="">Dava seç...</option>
                  {cases.map((c) => (
                    <option key={c.case_id} value={c.case_id}>
                      {c.case_id} - {c.client_name || ""}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            {/* Form fields */}
            <div className="space-y-4">
              {selectedTemplate.variables?.map((variable) => (
                <div key={variable.key}>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    {variable.label}
                    {variable.required && <span className="text-red-500 ml-1">*</span>}
                  </label>
                  {variable.type === "textarea" ? (
                    <textarea
                      value={formData[variable.key] || ""}
                      onChange={(e) => setFormData({ ...formData, [variable.key]: e.target.value })}
                      className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500"
                      rows={4}
                      placeholder={variable.placeholder || ""}
                    />
                  ) : variable.type === "select" ? (
                    <select
                      value={formData[variable.key] || ""}
                      onChange={(e) => setFormData({ ...formData, [variable.key]: e.target.value })}
                      className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500"
                    >
                      <option value="">Seçin...</option>
                      {variable.options?.map((opt) => (
                        <option key={opt} value={opt}>{opt}</option>
                      ))}
                    </select>
                  ) : variable.type === "date" ? (
                    <input
                      type="date"
                      value={formData[variable.key] || ""}
                      onChange={(e) => setFormData({ ...formData, [variable.key]: e.target.value })}
                      className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500"
                    />
                  ) : (
                    <input
                      type="text"
                      value={formData[variable.key] || ""}
                      onChange={(e) => setFormData({ ...formData, [variable.key]: e.target.value })}
                      className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500"
                      placeholder={variable.placeholder || ""}
                    />
                  )}
                </div>
              ))}
            </div>
          </div>

          <div className="p-4 border-t flex justify-end gap-3">
            <button
              onClick={() => setShowGenerateModal(false)}
              className="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-lg"
            >
              İptal
            </button>
            <button
              onClick={handlePreview}
              className="flex items-center gap-2 px-4 py-2 bg-gray-200 text-gray-800 rounded-lg hover:bg-gray-300"
            >
              <Eye className="w-4 h-4" />
              Önizle
            </button>
            <button
              onClick={handleGenerate}
              className="flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700"
            >
              <Check className="w-4 h-4" />
              Oluştur ve Kaydet
            </button>
          </div>
        </div>
      </div>
    );
  };

  // Preview Modal
  const PreviewModal = () => (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl shadow-xl max-w-4xl w-full max-h-[90vh] overflow-hidden">
        <div className="p-6 border-b flex items-center justify-between">
          <div>
            <h3 className="text-lg font-semibold text-gray-900">Belge Önizleme</h3>
            <p className="text-sm text-gray-500">{selectedTemplate?.name}</p>
          </div>
          <button onClick={() => setShowPreviewModal(false)} className="p-2 hover:bg-gray-100 rounded-lg">
            <X className="w-5 h-5 text-gray-500" />
          </button>
        </div>

        <div className="p-6 overflow-y-auto max-h-[60vh] bg-gray-50">
          <div className="bg-white p-8 shadow-sm rounded-lg border max-w-3xl mx-auto">
            <pre className="whitespace-pre-wrap font-serif text-gray-800 leading-relaxed">
              {generatedContent}
            </pre>
          </div>
        </div>

        <div className="p-4 border-t flex justify-end gap-3">
          <button
            onClick={() => setShowPreviewModal(false)}
            className="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-lg"
          >
            Kapat
          </button>
          <button
            onClick={copyToClipboard}
            className="flex items-center gap-2 px-4 py-2 bg-gray-200 text-gray-800 rounded-lg hover:bg-gray-300"
          >
            <Copy className="w-4 h-4" />
            Kopyala
          </button>
          <button
            onClick={printDocument}
            className="flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700"
          >
            <Printer className="w-4 h-4" />
            Yazdır
          </button>
        </div>
      </div>
    </div>
  );

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <RefreshCw className="w-8 h-8 text-indigo-600 animate-spin mx-auto mb-4" />
          <p className="text-gray-600">Şablonlar yükleniyor...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <button
                onClick={() => navigate("/admin")}
                className="text-gray-500 hover:text-gray-700"
              >
                ← Admin
              </button>
              <div>
                <h1 className="text-xl font-bold text-gray-900">Belge Şablonları</h1>
                <p className="text-sm text-gray-500">Hukuki belge oluşturma ve yönetimi</p>
              </div>
            </div>
            <button
              onClick={fetchTemplates}
              className="p-2 hover:bg-gray-100 rounded-lg"
            >
              <RefreshCw className="w-5 h-5 text-gray-600" />
            </button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 py-6">
        {/* Filters */}
        <div className="flex flex-wrap items-center gap-4 mb-6">
          <div className="relative flex-1 max-w-md">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
            <input
              type="text"
              placeholder="Şablon ara..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500"
            />
          </div>

          <select
            value={selectedCategory}
            onChange={(e) => setSelectedCategory(e.target.value)}
            className="px-4 py-2 border rounded-lg"
          >
            <option value="">Tüm Kategoriler</option>
            {categories.map((cat) => (
              <option key={cat.id} value={cat.id}>{cat.name}</option>
            ))}
          </select>

          <div className="ml-auto text-sm text-gray-500">
            {templates.length} şablon bulundu
          </div>
        </div>

        {/* Category Quick Filters */}
        <div className="flex flex-wrap gap-2 mb-6">
          {categories.map((cat) => {
            const IconComponent = categoryIcons[cat.id] || FileText;
            const isSelected = selectedCategory === cat.id;
            return (
              <button
                key={cat.id}
                onClick={() => setSelectedCategory(isSelected ? "" : cat.id)}
                className={`flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                  isSelected
                    ? "bg-indigo-600 text-white"
                    : "bg-white text-gray-700 border hover:bg-gray-50"
                }`}
              >
                <IconComponent className="w-4 h-4" />
                {cat.name}
              </button>
            );
          })}
        </div>

        {/* Templates Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 mb-8">
          {templates.map((template) => (
            <TemplateCard key={template.template_id} template={template} />
          ))}
        </div>

        {templates.length === 0 && (
          <div className="text-center py-12 text-gray-500">
            <FileText className="w-12 h-12 mx-auto mb-3 opacity-50" />
            <p>Şablon bulunamadı</p>
          </div>
        )}

        {/* Recent Generated Documents */}
        {generatedDocs.length > 0 && (
          <div className="mt-8">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Son Oluşturulan Belgeler</h2>
            <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Şablon</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Müvekkil</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Tarih</th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">İşlem</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200">
                  {generatedDocs.map((doc) => (
                    <tr key={doc.document_id} className="hover:bg-gray-50">
                      <td className="px-6 py-4 text-sm text-gray-900">{doc.template_name}</td>
                      <td className="px-6 py-4 text-sm text-gray-600">{doc.client_number || "-"}</td>
                      <td className="px-6 py-4 text-sm text-gray-500">
                        {new Date(doc.generated_at).toLocaleDateString("tr-TR", {
                          day: "numeric",
                          month: "short",
                          year: "numeric",
                          hour: "2-digit",
                          minute: "2-digit"
                        })}
                      </td>
                      <td className="px-6 py-4 text-right">
                        <button className="text-indigo-600 hover:text-indigo-800 text-sm font-medium">
                          Görüntüle
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </main>

      {/* Modals */}
      {showGenerateModal && <GenerateModal />}
      {showPreviewModal && <PreviewModal />}
    </div>
  );
}
