import React, { useState, useEffect, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";
import { toast } from "sonner";
import {
  TrendingUp,
  TrendingDown,
  Users,
  Briefcase,
  FileText,
  Calendar,
  Shield,
  Activity,
  Globe,
  AlertTriangle,
  RefreshCw,
  Download,
  ChevronDown,
  BarChart3,
  PieChart,
  LineChart,
  MapPin,
  Clock,
  Target,
  Zap,
  ArrowUpRight,
  ArrowDownRight,
  Eye,
  Scale,
  MessageSquare,
  Layers
} from "lucide-react";

const API_URL = process.env.REACT_APP_API_URL || "http://localhost:8000";

// Color palette
const COLORS = {
  primary: "#4F46E5",
  success: "#10B981",
  warning: "#F59E0B",
  danger: "#EF4444",
  info: "#3B82F6",
  purple: "#8B5CF6",
  pink: "#EC4899",
  cyan: "#06B6D4"
};

export default function AdminAnalytics() {
  const { token } = useAuth();
  const navigate = useNavigate();

  // State
  const [loading, setLoading] = useState(true);
  const [period, setPeriod] = useState("30d");
  const [overview, setOverview] = useState(null);
  const [trends, setTrends] = useState([]);
  const [performance, setPerformance] = useState(null);
  const [geographic, setGeographic] = useState(null);
  const [riskData, setRiskData] = useState(null);
  const [activityFeed, setActivityFeed] = useState([]);
  const [activeChart, setActiveChart] = useState("clients");

  // Fetch analytics data
  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const headers = { Authorization: `Bearer ${token}` };

      const [overviewRes, performanceRes, geoRes, riskRes, activityRes] = await Promise.all([
        fetch(`${API_URL}/api/analytics/overview?period=${period}`, { headers }),
        fetch(`${API_URL}/api/analytics/performance`, { headers }),
        fetch(`${API_URL}/api/analytics/geographic`, { headers }),
        fetch(`${API_URL}/api/analytics/risk-distribution`, { headers }),
        fetch(`${API_URL}/api/analytics/activity-feed?limit=20`, { headers })
      ]);

      if (overviewRes.ok) setOverview(await overviewRes.json());
      if (performanceRes.ok) setPerformance(await performanceRes.json());
      if (geoRes.ok) setGeographic(await geoRes.json());
      if (riskRes.ok) setRiskData(await riskRes.json());
      if (activityRes.ok) {
        const actData = await activityRes.json();
        setActivityFeed(actData.activities || []);
      }

      // Fetch trends for selected metric
      const trendsRes = await fetch(
        `${API_URL}/api/analytics/trends?metric=${activeChart}&period=${period}&granularity=day`,
        { headers }
      );
      if (trendsRes.ok) {
        const trendData = await trendsRes.json();
        setTrends(trendData.data || []);
      }
    } catch (error) {
      console.error("Analytics fetch error:", error);
      toast.error("Veriler yüklenirken hata oluştu");
    }
    setLoading(false);
  }, [token, period, activeChart]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  // Export data
  const handleExport = async () => {
    try {
      const res = await fetch(`${API_URL}/api/analytics/export?period=${period}&format=json`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `analytics-${period}-${new Date().toISOString().split("T")[0]}.json`;
        a.click();
        toast.success("Rapor indirildi");
      }
    } catch (error) {
      toast.error("Dışa aktarma hatası");
    }
  };

  // Stat Card Component
  const StatCard = ({ title, value, change, icon: Icon, color, subtitle }) => (
    <div className="bg-white rounded-xl p-5 shadow-sm border border-gray-100 hover:shadow-md transition-shadow">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm text-gray-500 mb-1">{title}</p>
          <p className="text-2xl font-bold text-gray-900">{value}</p>
          {subtitle && <p className="text-xs text-gray-400 mt-1">{subtitle}</p>}
        </div>
        <div className={`p-3 rounded-xl ${color}`}>
          <Icon className="w-5 h-5 text-white" />
        </div>
      </div>
      {change !== undefined && (
        <div className="flex items-center gap-1 mt-3">
          {change >= 0 ? (
            <ArrowUpRight className="w-4 h-4 text-green-500" />
          ) : (
            <ArrowDownRight className="w-4 h-4 text-red-500" />
          )}
          <span className={`text-sm font-medium ${change >= 0 ? "text-green-600" : "text-red-600"}`}>
            {Math.abs(change)}%
          </span>
          <span className="text-xs text-gray-500">önceki döneme göre</span>
        </div>
      )}
    </div>
  );

  // Simple Bar Chart Component
  const SimpleBarChart = ({ data, label }) => {
    if (!data || data.length === 0) return null;
    const maxValue = Math.max(...data.map(d => d.count));

    return (
      <div className="space-y-2">
        {data.slice(-14).map((item, idx) => (
          <div key={idx} className="flex items-center gap-2">
            <span className="text-xs text-gray-500 w-16 truncate">{item.date?.slice(-5) || idx}</span>
            <div className="flex-1 bg-gray-100 rounded-full h-4 overflow-hidden">
              <div
                className="h-full bg-gradient-to-r from-indigo-500 to-purple-500 rounded-full transition-all"
                style={{ width: `${maxValue > 0 ? (item.count / maxValue) * 100 : 0}%` }}
              />
            </div>
            <span className="text-xs font-medium text-gray-700 w-8">{item.count}</span>
          </div>
        ))}
      </div>
    );
  };

  // Risk Distribution Component
  const RiskDistribution = () => {
    if (!riskData) return null;

    const levels = [
      { key: "critical", label: "Kritik", color: "bg-red-500" },
      { key: "high", label: "Yüksek", color: "bg-orange-500" },
      { key: "medium", label: "Orta", color: "bg-yellow-500" },
      { key: "low", label: "Düşük", color: "bg-green-500" }
    ];

    const total = Object.values(riskData.by_level || {}).reduce((a, b) => a + b, 0) || 1;

    return (
      <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
        <h3 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
          <Shield className="w-5 h-5 text-indigo-600" />
          Risk Dağılımı
        </h3>

        {/* Stacked Bar */}
        <div className="h-8 flex rounded-lg overflow-hidden mb-4">
          {levels.map((level) => {
            const count = riskData.by_level?.[level.key] || 0;
            const percentage = (count / total) * 100;
            return percentage > 0 ? (
              <div
                key={level.key}
                className={`${level.color} flex items-center justify-center`}
                style={{ width: `${percentage}%` }}
              >
                {percentage > 10 && (
                  <span className="text-xs text-white font-medium">{count}</span>
                )}
              </div>
            ) : null;
          })}
        </div>

        {/* Legend */}
        <div className="grid grid-cols-2 gap-2">
          {levels.map((level) => (
            <div key={level.key} className="flex items-center gap-2">
              <div className={`w-3 h-3 rounded-full ${level.color}`} />
              <span className="text-sm text-gray-600">{level.label}</span>
              <span className="text-sm font-medium text-gray-900 ml-auto">
                {riskData.by_level?.[level.key] || 0}
              </span>
            </div>
          ))}
        </div>

        {/* Urgent Alert */}
        {riskData.urgent_cases > 0 && (
          <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg flex items-center gap-2">
            <AlertTriangle className="w-5 h-5 text-red-500" />
            <span className="text-sm text-red-700">
              <strong>{riskData.urgent_cases}</strong> acil müdahale gerektiren dava
            </span>
          </div>
        )}
      </div>
    );
  };

  // Geographic Distribution Component
  const GeographicDistribution = () => {
    if (!geographic) return null;

    return (
      <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
        <h3 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
          <Globe className="w-5 h-5 text-indigo-600" />
          Coğrafi Dağılım
        </h3>

        <div className="space-y-4">
          {/* Countries */}
          <div>
            <p className="text-sm text-gray-500 mb-2">Ülkelere Göre Müvekkiller</p>
            <div className="space-y-2">
              {geographic.clients_by_country?.slice(0, 5).map((item, idx) => (
                <div key={idx} className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <MapPin className="w-4 h-4 text-gray-400" />
                    <span className="text-sm text-gray-700">{item.country || "Belirtilmemiş"}</span>
                  </div>
                  <span className="text-sm font-medium text-gray-900">{item.count}</span>
                </div>
              ))}
            </div>
          </div>

          {/* International Cases */}
          <div className="pt-4 border-t">
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">Uluslararası Davalar</span>
              <span className="text-lg font-bold text-indigo-600">{geographic.international_cases || 0}</span>
            </div>
          </div>
        </div>
      </div>
    );
  };

  // Performance Metrics Component
  const PerformanceMetrics = () => {
    if (!performance) return null;

    return (
      <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
        <h3 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
          <Zap className="w-5 h-5 text-indigo-600" />
          Performans Metrikleri
        </h3>

        <div className="grid grid-cols-2 gap-4">
          {/* Case Resolution */}
          <div className="p-4 bg-gradient-to-br from-blue-50 to-indigo-50 rounded-lg">
            <div className="flex items-center gap-2 mb-2">
              <Clock className="w-4 h-4 text-blue-600" />
              <span className="text-xs text-blue-600 font-medium">Dava Çözüm Süresi</span>
            </div>
            <p className="text-2xl font-bold text-gray-900">
              {performance.case_resolution?.avg_days || "—"}
            </p>
            <p className="text-xs text-gray-500">ortalama gün</p>
          </div>

          {/* Task Completion */}
          <div className="p-4 bg-gradient-to-br from-green-50 to-emerald-50 rounded-lg">
            <div className="flex items-center gap-2 mb-2">
              <Target className="w-4 h-4 text-green-600" />
              <span className="text-xs text-green-600 font-medium">Görev Tamamlama</span>
            </div>
            <p className="text-2xl font-bold text-gray-900">
              {performance.tasks?.completion_rate || 0}%
            </p>
            <p className="text-xs text-gray-500">{performance.tasks?.completed || 0}/{performance.tasks?.total || 0}</p>
          </div>

          {/* Document Rate */}
          <div className="p-4 bg-gradient-to-br from-purple-50 to-pink-50 rounded-lg">
            <div className="flex items-center gap-2 mb-2">
              <FileText className="w-4 h-4 text-purple-600" />
              <span className="text-xs text-purple-600 font-medium">Belge Yüklemesi</span>
            </div>
            <p className="text-2xl font-bold text-gray-900">
              {performance.documents?.avg_per_day || 0}
            </p>
            <p className="text-xs text-gray-500">günlük ortalama</p>
          </div>

          {/* Evidence Collection */}
          <div className="p-4 bg-gradient-to-br from-orange-50 to-yellow-50 rounded-lg">
            <div className="flex items-center gap-2 mb-2">
              <Layers className="w-4 h-4 text-orange-600" />
              <span className="text-xs text-orange-600 font-medium">Delil Toplama</span>
            </div>
            <p className="text-2xl font-bold text-gray-900">
              {performance.evidence_collection?.avg_items_per_session || "—"}
            </p>
            <p className="text-xs text-gray-500">oturum başına</p>
          </div>
        </div>
      </div>
    );
  };

  // Activity Feed Component
  const ActivityFeedComponent = () => (
    <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
      <h3 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
        <Activity className="w-5 h-5 text-indigo-600" />
        Son Aktiviteler
      </h3>

      <div className="space-y-3 max-h-[400px] overflow-y-auto">
        {activityFeed.map((activity, idx) => {
          const icons = {
            client_registered: Users,
            case_created: Scale,
            document_uploaded: FileText,
            meeting_scheduled: Calendar,
            forensic_analysis: Shield
          };
          const Icon = icons[activity.type] || Activity;

          return (
            <div key={idx} className="flex items-start gap-3 p-2 hover:bg-gray-50 rounded-lg">
              <div className="p-2 bg-indigo-100 rounded-lg">
                <Icon className="w-4 h-4 text-indigo-600" />
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-gray-900">{activity.title}</p>
                <p className="text-xs text-gray-500 truncate">{activity.description}</p>
              </div>
              <span className="text-xs text-gray-400 whitespace-nowrap">
                {activity.timestamp
                  ? new Date(activity.timestamp).toLocaleDateString("tr-TR", {
                      day: "numeric",
                      month: "short",
                      hour: "2-digit",
                      minute: "2-digit"
                    })
                  : ""}
              </span>
            </div>
          );
        })}

        {activityFeed.length === 0 && (
          <p className="text-center text-gray-500 py-8">Henüz aktivite yok</p>
        )}
      </div>
    </div>
  );

  if (loading && !overview) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <RefreshCw className="w-8 h-8 text-indigo-600 animate-spin mx-auto mb-4" />
          <p className="text-gray-600">Analitik verileri yükleniyor...</p>
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
                <h1 className="text-xl font-bold text-gray-900">Analitik Dashboard</h1>
                <p className="text-sm text-gray-500">Gerçek zamanlı iş zekası ve raporlama</p>
              </div>
            </div>

            <div className="flex items-center gap-3">
              {/* Period Selector */}
              <div className="relative">
                <select
                  value={period}
                  onChange={(e) => setPeriod(e.target.value)}
                  className="appearance-none bg-white border rounded-lg px-4 py-2 pr-8 text-sm font-medium text-gray-700 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                >
                  <option value="7d">Son 7 Gün</option>
                  <option value="30d">Son 30 Gün</option>
                  <option value="90d">Son 90 Gün</option>
                  <option value="1y">Son 1 Yıl</option>
                  <option value="all">Tüm Zamanlar</option>
                </select>
                <ChevronDown className="absolute right-2 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500 pointer-events-none" />
              </div>

              <button
                onClick={handleExport}
                className="flex items-center gap-2 px-4 py-2 bg-white border rounded-lg text-sm font-medium text-gray-700 hover:bg-gray-50"
              >
                <Download className="w-4 h-4" />
                Dışa Aktar
              </button>

              <button
                onClick={fetchData}
                className="p-2 hover:bg-gray-100 rounded-lg"
                disabled={loading}
              >
                <RefreshCw className={`w-5 h-5 text-gray-600 ${loading ? "animate-spin" : ""}`} />
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 py-6">
        {/* Key Metrics */}
        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4 mb-6">
          <StatCard
            title="Toplam Müvekkil"
            value={overview?.clients?.total || 0}
            change={overview?.clients?.change_percent}
            icon={Users}
            color="bg-blue-500"
            subtitle={`${overview?.clients?.active || 0} aktif`}
          />
          <StatCard
            title="Aktif Dava"
            value={overview?.cases?.active || 0}
            change={overview?.cases?.change_percent}
            icon={Briefcase}
            color="bg-indigo-500"
            subtitle={`${overview?.cases?.total || 0} toplam`}
          />
          <StatCard
            title="Belgeler"
            value={overview?.documents?.total || 0}
            change={overview?.documents?.change_percent}
            icon={FileText}
            color="bg-purple-500"
            subtitle={`${overview?.documents?.total_size_mb || 0} MB`}
          />
          <StatCard
            title="Toplantılar"
            value={overview?.meetings?.total || 0}
            change={overview?.meetings?.change_percent}
            icon={Calendar}
            color="bg-green-500"
            subtitle={`${overview?.meetings?.upcoming || 0} planlanmış`}
          />
          <StatCard
            title="Delil Öğeleri"
            value={overview?.evidence?.total_items || 0}
            change={overview?.evidence?.change_percent}
            icon={Layers}
            color="bg-orange-500"
            subtitle={`${overview?.evidence?.active_sessions || 0} aktif oturum`}
          />
          <StatCard
            title="Adli Analizler"
            value={overview?.forensics?.total || 0}
            change={overview?.forensics?.change_percent}
            icon={Shield}
            color="bg-red-500"
            subtitle={`${overview?.forensics?.high_risk_cases || 0} yüksek risk`}
          />
        </div>

        {/* Charts Row */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
          {/* Trend Chart */}
          <div className="lg:col-span-2 bg-white rounded-xl p-6 shadow-sm border border-gray-100">
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-semibold text-gray-900 flex items-center gap-2">
                <LineChart className="w-5 h-5 text-indigo-600" />
                Trend Analizi
              </h3>
              <div className="flex gap-2">
                {["clients", "cases", "documents", "meetings", "evidence"].map((metric) => (
                  <button
                    key={metric}
                    onClick={() => setActiveChart(metric)}
                    className={`px-3 py-1 rounded-lg text-xs font-medium transition-colors ${
                      activeChart === metric
                        ? "bg-indigo-100 text-indigo-700"
                        : "bg-gray-100 text-gray-600 hover:bg-gray-200"
                    }`}
                  >
                    {metric === "clients" ? "Müvekkiller" :
                     metric === "cases" ? "Davalar" :
                     metric === "documents" ? "Belgeler" :
                     metric === "meetings" ? "Toplantılar" : "Deliller"}
                  </button>
                ))}
              </div>
            </div>
            <SimpleBarChart data={trends} label={activeChart} />
            {trends.length === 0 && (
              <p className="text-center text-gray-500 py-8">Bu dönem için veri yok</p>
            )}
          </div>

          {/* Risk Distribution */}
          <RiskDistribution />
        </div>

        {/* Second Row */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
          {/* Performance */}
          <PerformanceMetrics />

          {/* Geographic */}
          <GeographicDistribution />

          {/* Activity Feed */}
          <ActivityFeedComponent />
        </div>

        {/* Status Breakdowns */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {/* Client Status */}
          <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
            <h4 className="font-medium text-gray-900 mb-4">Müvekkil Durumları</h4>
            <div className="space-y-2">
              {Object.entries(overview?.clients?.by_status || {}).map(([status, count]) => (
                <div key={status} className="flex items-center justify-between">
                  <span className="text-sm text-gray-600 capitalize">{status}</span>
                  <span className="text-sm font-medium text-gray-900">{count}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Case Types */}
          <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
            <h4 className="font-medium text-gray-900 mb-4">Dava Türleri</h4>
            <div className="space-y-2">
              {Object.entries(overview?.cases?.by_type || {}).map(([type, count]) => (
                <div key={type} className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">{type?.replace(/_/g, " ") || "Belirtilmemiş"}</span>
                  <span className="text-sm font-medium text-gray-900">{count}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Document Types */}
          <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
            <h4 className="font-medium text-gray-900 mb-4">Belge Türleri</h4>
            <div className="space-y-2">
              {Object.entries(overview?.documents?.by_type || {}).slice(0, 6).map(([type, count]) => (
                <div key={type} className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">{type || "Diğer"}</span>
                  <span className="text-sm font-medium text-gray-900">{count}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Evidence Platforms */}
          <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
            <h4 className="font-medium text-gray-900 mb-4">Delil Platformları</h4>
            <div className="space-y-2">
              {Object.entries(overview?.evidence?.by_platform || {}).map(([platform, count]) => (
                <div key={platform} className="flex items-center justify-between">
                  <span className="text-sm text-gray-600 capitalize">{platform}</span>
                  <span className="text-sm font-medium text-gray-900">{count}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
