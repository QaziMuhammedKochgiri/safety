import React, { useState, useEffect, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";
import { useLanguage } from "../contexts/LanguageContext";
import { toast } from "sonner";
import {
  Calendar,
  Clock,
  CheckCircle2,
  AlertCircle,
  Plus,
  Filter,
  ChevronDown,
  ChevronRight,
  Flag,
  Target,
  ListTodo,
  Users,
  FileText,
  MessageSquare,
  Scale,
  Milestone,
  TrendingUp,
  RefreshCw,
  Search,
  MoreVertical,
  Edit2,
  Trash2,
  Eye,
  PlayCircle,
  PauseCircle,
  CheckSquare,
  Square,
  CalendarDays,
  Timer,
  AlertTriangle,
  Sparkles,
  LayoutGrid,
  List,
  Layers,
  Download,
  FileSpreadsheet,
  Image
} from "lucide-react";

const API_URL = process.env.REACT_APP_API_URL || "http://localhost:8000";

// Priority colors
const priorityColors = {
  critical: { bg: "bg-red-100", text: "text-red-700", border: "border-red-300" },
  high: { bg: "bg-orange-100", text: "text-orange-700", border: "border-orange-300" },
  medium: { bg: "bg-yellow-100", text: "text-yellow-700", border: "border-yellow-300" },
  low: { bg: "bg-green-100", text: "text-green-700", border: "border-green-300" }
};

// Status colors
const statusColors = {
  pending: { bg: "bg-gray-100", text: "text-gray-700", icon: Clock },
  in_progress: { bg: "bg-blue-100", text: "text-blue-700", icon: PlayCircle },
  completed: { bg: "bg-green-100", text: "text-green-700", icon: CheckCircle2 },
  cancelled: { bg: "bg-red-100", text: "text-red-700", icon: PauseCircle },
  overdue: { bg: "bg-red-100", text: "text-red-700", icon: AlertTriangle }
};

// Event type icons
const eventTypeIcons = {
  case_created: Scale,
  document_uploaded: FileText,
  meeting_scheduled: Calendar,
  task_completed: CheckCircle2,
  milestone_reached: Target,
  note_added: MessageSquare,
  status_change: RefreshCw,
  evidence_collected: Layers,
  court_date: Scale,
  deadline: AlertCircle,
  custom: Flag
};

export default function AdminCaseTimeline() {
  const { user, token } = useAuth();
  const { t } = useLanguage();
  const navigate = useNavigate();

  // State
  const [activeTab, setActiveTab] = useState("timeline");
  const [loading, setLoading] = useState(true);
  const [dashboard, setDashboard] = useState(null);
  const [events, setEvents] = useState([]);
  const [tasks, setTasks] = useState([]);
  const [milestones, setMilestones] = useState([]);
  const [cases, setCases] = useState([]);
  const [selectedCase, setSelectedCase] = useState(null);
  const [viewMode, setViewMode] = useState("list"); // list, board, calendar

  // Filters
  const [taskFilter, setTaskFilter] = useState({
    status: "",
    priority: "",
    assigned_to: ""
  });

  // Modals
  const [showNewEventModal, setShowNewEventModal] = useState(false);
  const [showNewTaskModal, setShowNewTaskModal] = useState(false);
  const [showNewMilestoneModal, setShowNewMilestoneModal] = useState(false);
  const [showTemplateModal, setShowTemplateModal] = useState(false);
  const [showExportModal, setShowExportModal] = useState(false);
  const [exportLoading, setExportLoading] = useState(false);
  const [templates, setTemplates] = useState([]);

  // Fetch functions
  const fetchDashboard = useCallback(async () => {
    try {
      const res = await fetch(`${API_URL}/api/timeline/dashboard`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setDashboard(data);
      }
    } catch (error) {
      console.error("Dashboard fetch error:", error);
    }
  }, [token]);

  const fetchCases = useCallback(async () => {
    try {
      const res = await fetch(`${API_URL}/api/cases`, {
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

  const fetchEvents = useCallback(async (caseId) => {
    if (!caseId) return;
    try {
      const res = await fetch(`${API_URL}/api/timeline/events/${caseId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setEvents(data.events || []);
      }
    } catch (error) {
      console.error("Events fetch error:", error);
    }
  }, [token]);

  const fetchTasks = useCallback(async () => {
    try {
      const params = new URLSearchParams();
      if (selectedCase) params.append("case_id", selectedCase);
      if (taskFilter.status) params.append("status", taskFilter.status);
      if (taskFilter.priority) params.append("priority", taskFilter.priority);
      if (taskFilter.assigned_to) params.append("assigned_to", taskFilter.assigned_to);

      const res = await fetch(`${API_URL}/api/timeline/tasks?${params}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setTasks(data.tasks || []);
      }
    } catch (error) {
      console.error("Tasks fetch error:", error);
    }
  }, [token, selectedCase, taskFilter]);

  const fetchMilestones = useCallback(async (caseId) => {
    if (!caseId) return;
    try {
      const res = await fetch(`${API_URL}/api/timeline/milestones/${caseId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setMilestones(data.milestones || []);
      }
    } catch (error) {
      console.error("Milestones fetch error:", error);
    }
  }, [token]);

  const fetchTemplates = useCallback(async () => {
    try {
      const res = await fetch(`${API_URL}/api/timeline/templates/milestones`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setTemplates(data.templates || []);
      }
    } catch (error) {
      console.error("Templates fetch error:", error);
    }
  }, [token]);

  // Initial load
  useEffect(() => {
    const loadData = async () => {
      setLoading(true);
      await Promise.all([fetchDashboard(), fetchCases(), fetchTasks(), fetchTemplates()]);
      setLoading(false);
    };
    loadData();
  }, [fetchDashboard, fetchCases, fetchTasks, fetchTemplates]);

  // Load case-specific data
  useEffect(() => {
    if (selectedCase) {
      fetchEvents(selectedCase);
      fetchMilestones(selectedCase);
    }
  }, [selectedCase, fetchEvents, fetchMilestones]);

  // Reload tasks when filter changes
  useEffect(() => {
    fetchTasks();
  }, [fetchTasks]);

  // Task actions
  const updateTaskStatus = async (taskId, newStatus) => {
    try {
      const res = await fetch(`${API_URL}/api/timeline/tasks/${taskId}`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({ status: newStatus })
      });
      if (res.ok) {
        toast.success("Görev durumu güncellendi");
        fetchTasks();
        fetchDashboard();
      }
    } catch (error) {
      toast.error("Güncelleme hatası");
    }
  };

  const deleteTask = async (taskId) => {
    if (!window.confirm("Bu görevi silmek istediğinize emin misiniz?")) return;
    try {
      const res = await fetch(`${API_URL}/api/timeline/tasks/${taskId}`, {
        method: "DELETE",
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        toast.success("Görev silindi");
        fetchTasks();
      }
    } catch (error) {
      toast.error("Silme hatası");
    }
  };

  // Apply template
  const applyTemplate = async (templateId) => {
    if (!selectedCase) {
      toast.error("Lütfen önce bir dava seçin");
      return;
    }
    try {
      const res = await fetch(`${API_URL}/api/timeline/templates/milestones/apply`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({
          case_id: selectedCase,
          template_id: templateId
        })
      });
      if (res.ok) {
        toast.success("Şablon uygulandı");
        setShowTemplateModal(false);
        fetchMilestones(selectedCase);
      }
    } catch (error) {
      toast.error("Şablon uygulama hatası");
    }
  };

  // Export timeline
  const exportTimeline = async (format) => {
    if (!selectedCase) {
      toast.error("Lütfen önce bir dava seçin");
      return;
    }
    setExportLoading(true);
    try {
      const res = await fetch(`${API_URL}/api/timeline/export/${selectedCase}?format=${format}`, {
        headers: { Authorization: `Bearer ${token}` }
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Export hatası");
      }

      // Get filename from Content-Disposition header
      const contentDisposition = res.headers.get("Content-Disposition");
      let filename = `timeline_${selectedCase}.${format}`;
      if (contentDisposition) {
        const match = contentDisposition.match(/filename="(.+)"/);
        if (match) filename = match[1];
      }

      // Create blob and download
      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);

      toast.success(`${format.toUpperCase()} olarak indirildi`);
      setShowExportModal(false);
    } catch (error) {
      toast.error(error.message || "Export hatası");
    }
    setExportLoading(false);
  };

  // Dashboard Stats Component
  const DashboardStats = () => (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
      <div className="bg-white rounded-xl p-4 shadow-sm border border-gray-100">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-blue-100 rounded-lg">
            <ListTodo className="w-5 h-5 text-blue-600" />
          </div>
          <div>
            <p className="text-2xl font-bold text-gray-900">{dashboard?.task_stats?.total || 0}</p>
            <p className="text-sm text-gray-500">Toplam Görev</p>
          </div>
        </div>
      </div>

      <div className="bg-white rounded-xl p-4 shadow-sm border border-gray-100">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-yellow-100 rounded-lg">
            <Clock className="w-5 h-5 text-yellow-600" />
          </div>
          <div>
            <p className="text-2xl font-bold text-gray-900">{dashboard?.task_stats?.pending || 0}</p>
            <p className="text-sm text-gray-500">Bekleyen</p>
          </div>
        </div>
      </div>

      <div className="bg-white rounded-xl p-4 shadow-sm border border-gray-100">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-green-100 rounded-lg">
            <CheckCircle2 className="w-5 h-5 text-green-600" />
          </div>
          <div>
            <p className="text-2xl font-bold text-gray-900">{dashboard?.task_stats?.completed || 0}</p>
            <p className="text-sm text-gray-500">Tamamlanan</p>
          </div>
        </div>
      </div>

      <div className="bg-white rounded-xl p-4 shadow-sm border border-gray-100">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-red-100 rounded-lg">
            <AlertTriangle className="w-5 h-5 text-red-600" />
          </div>
          <div>
            <p className="text-2xl font-bold text-gray-900">{dashboard?.task_stats?.overdue || 0}</p>
            <p className="text-sm text-gray-500">Gecikmiş</p>
          </div>
        </div>
      </div>
    </div>
  );

  // Timeline View Component
  const TimelineView = () => (
    <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-lg font-semibold text-gray-900">Dava Zaman Çizelgesi</h3>
        <div className="flex items-center gap-2">
          <select
            value={selectedCase || ""}
            onChange={(e) => setSelectedCase(e.target.value || null)}
            className="px-3 py-2 border rounded-lg text-sm"
          >
            <option value="">Dava Seçin</option>
            {cases.map((c) => (
              <option key={c.case_id} value={c.case_id}>
                {c.case_id} - {c.client_name || "İsimsiz"}
              </option>
            ))}
          </select>
          <button
            onClick={() => setShowNewEventModal(true)}
            disabled={!selectedCase}
            className="flex items-center gap-2 px-3 py-2 bg-indigo-600 text-white rounded-lg text-sm hover:bg-indigo-700 disabled:opacity-50"
          >
            <Plus className="w-4 h-4" />
            Olay Ekle
          </button>
        </div>
      </div>

      {!selectedCase ? (
        <div className="text-center py-12 text-gray-500">
          <Calendar className="w-12 h-12 mx-auto mb-3 opacity-50" />
          <p>Zaman çizelgesini görüntülemek için bir dava seçin</p>
        </div>
      ) : events.length === 0 ? (
        <div className="text-center py-12 text-gray-500">
          <Clock className="w-12 h-12 mx-auto mb-3 opacity-50" />
          <p>Henüz olay kaydı yok</p>
        </div>
      ) : (
        <div className="relative">
          {/* Timeline line */}
          <div className="absolute left-6 top-0 bottom-0 w-0.5 bg-gray-200" />

          {/* Events */}
          <div className="space-y-6">
            {events.map((event, index) => {
              const IconComponent = eventTypeIcons[event.event_type] || Flag;
              return (
                <div key={event.event_id} className="relative flex gap-4">
                  {/* Icon */}
                  <div className={`relative z-10 flex items-center justify-center w-12 h-12 rounded-full ${
                    event.importance === "high" ? "bg-red-100" :
                    event.importance === "medium" ? "bg-yellow-100" : "bg-blue-100"
                  }`}>
                    <IconComponent className={`w-5 h-5 ${
                      event.importance === "high" ? "text-red-600" :
                      event.importance === "medium" ? "text-yellow-600" : "text-blue-600"
                    }`} />
                  </div>

                  {/* Content */}
                  <div className="flex-1 bg-gray-50 rounded-lg p-4">
                    <div className="flex items-start justify-between">
                      <div>
                        <h4 className="font-medium text-gray-900">{event.title}</h4>
                        <p className="text-sm text-gray-600 mt-1">{event.description}</p>
                      </div>
                      <span className="text-xs text-gray-500">
                        {new Date(event.timestamp).toLocaleDateString("tr-TR", {
                          day: "numeric",
                          month: "short",
                          year: "numeric",
                          hour: "2-digit",
                          minute: "2-digit"
                        })}
                      </span>
                    </div>

                    {/* Metadata */}
                    {event.metadata && Object.keys(event.metadata).length > 0 && (
                      <div className="mt-2 flex flex-wrap gap-2">
                        {Object.entries(event.metadata).map(([key, value]) => (
                          <span key={key} className="px-2 py-1 bg-white rounded text-xs text-gray-600">
                            {key}: {String(value)}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );

  // Tasks View Component
  const TasksView = () => (
    <div className="space-y-6">
      {/* Filters */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-4">
        <div className="flex flex-wrap items-center gap-4">
          <div className="flex items-center gap-2">
            <Filter className="w-4 h-4 text-gray-500" />
            <span className="text-sm font-medium text-gray-700">Filtreler:</span>
          </div>

          <select
            value={taskFilter.status}
            onChange={(e) => setTaskFilter({ ...taskFilter, status: e.target.value })}
            className="px-3 py-1.5 border rounded-lg text-sm"
          >
            <option value="">Tüm Durumlar</option>
            <option value="pending">Bekleyen</option>
            <option value="in_progress">Devam Eden</option>
            <option value="completed">Tamamlanan</option>
          </select>

          <select
            value={taskFilter.priority}
            onChange={(e) => setTaskFilter({ ...taskFilter, priority: e.target.value })}
            className="px-3 py-1.5 border rounded-lg text-sm"
          >
            <option value="">Tüm Öncelikler</option>
            <option value="critical">Kritik</option>
            <option value="high">Yüksek</option>
            <option value="medium">Orta</option>
            <option value="low">Düşük</option>
          </select>

          <div className="ml-auto flex items-center gap-2">
            <button
              onClick={() => setViewMode("list")}
              className={`p-2 rounded ${viewMode === "list" ? "bg-indigo-100 text-indigo-600" : "text-gray-500"}`}
            >
              <List className="w-4 h-4" />
            </button>
            <button
              onClick={() => setViewMode("board")}
              className={`p-2 rounded ${viewMode === "board" ? "bg-indigo-100 text-indigo-600" : "text-gray-500"}`}
            >
              <LayoutGrid className="w-4 h-4" />
            </button>
          </div>

          <button
            onClick={() => setShowNewTaskModal(true)}
            className="flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white rounded-lg text-sm hover:bg-indigo-700"
          >
            <Plus className="w-4 h-4" />
            Yeni Görev
          </button>
        </div>
      </div>

      {/* Task List */}
      {viewMode === "list" ? (
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Görev</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Dava</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Öncelik</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Durum</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Son Tarih</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">İşlemler</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {tasks.map((task) => {
                const priority = priorityColors[task.priority] || priorityColors.medium;
                const status = statusColors[task.status] || statusColors.pending;
                const StatusIcon = status.icon;
                const isOverdue = task.due_date && new Date(task.due_date) < new Date() && task.status !== "completed";

                return (
                  <tr key={task.task_id} className={`hover:bg-gray-50 ${isOverdue ? "bg-red-50" : ""}`}>
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-3">
                        <button
                          onClick={() => updateTaskStatus(task.task_id, task.status === "completed" ? "pending" : "completed")}
                          className="text-gray-400 hover:text-green-600"
                        >
                          {task.status === "completed" ? (
                            <CheckSquare className="w-5 h-5 text-green-600" />
                          ) : (
                            <Square className="w-5 h-5" />
                          )}
                        </button>
                        <div>
                          <p className={`font-medium ${task.status === "completed" ? "line-through text-gray-400" : "text-gray-900"}`}>
                            {task.title}
                          </p>
                          {task.description && (
                            <p className="text-sm text-gray-500 truncate max-w-xs">{task.description}</p>
                          )}
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <span className="text-sm text-gray-600">{task.case_id}</span>
                    </td>
                    <td className="px-6 py-4">
                      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${priority.bg} ${priority.text}`}>
                        {task.priority === "critical" ? "Kritik" :
                         task.priority === "high" ? "Yüksek" :
                         task.priority === "medium" ? "Orta" : "Düşük"}
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      <span className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium ${status.bg} ${status.text}`}>
                        <StatusIcon className="w-3 h-3" />
                        {task.status === "pending" ? "Bekleyen" :
                         task.status === "in_progress" ? "Devam Eden" :
                         task.status === "completed" ? "Tamamlandı" : task.status}
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      {task.due_date ? (
                        <div className={`flex items-center gap-1 text-sm ${isOverdue ? "text-red-600 font-medium" : "text-gray-600"}`}>
                          <CalendarDays className="w-4 h-4" />
                          {new Date(task.due_date).toLocaleDateString("tr-TR")}
                          {isOverdue && <AlertTriangle className="w-4 h-4" />}
                        </div>
                      ) : (
                        <span className="text-sm text-gray-400">-</span>
                      )}
                    </td>
                    <td className="px-6 py-4 text-right">
                      <div className="flex items-center justify-end gap-2">
                        <button
                          onClick={() => updateTaskStatus(task.task_id, "in_progress")}
                          className="p-1 text-blue-600 hover:bg-blue-50 rounded"
                          title="Başlat"
                        >
                          <PlayCircle className="w-4 h-4" />
                        </button>
                        <button
                          onClick={() => deleteTask(task.task_id)}
                          className="p-1 text-red-600 hover:bg-red-50 rounded"
                          title="Sil"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>

          {tasks.length === 0 && (
            <div className="text-center py-12 text-gray-500">
              <ListTodo className="w-12 h-12 mx-auto mb-3 opacity-50" />
              <p>Görev bulunamadı</p>
            </div>
          )}
        </div>
      ) : (
        /* Kanban Board View */
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {["pending", "in_progress", "completed"].map((status) => {
            const statusConfig = statusColors[status];
            const StatusIcon = statusConfig.icon;
            const statusTasks = tasks.filter((t) => t.status === status);

            return (
              <div key={status} className="bg-white rounded-xl shadow-sm border border-gray-100">
                <div className={`px-4 py-3 border-b ${statusConfig.bg} rounded-t-xl`}>
                  <div className="flex items-center gap-2">
                    <StatusIcon className={`w-4 h-4 ${statusConfig.text}`} />
                    <span className={`font-medium ${statusConfig.text}`}>
                      {status === "pending" ? "Bekleyen" :
                       status === "in_progress" ? "Devam Eden" : "Tamamlanan"}
                    </span>
                    <span className="ml-auto bg-white px-2 py-0.5 rounded-full text-xs font-medium text-gray-600">
                      {statusTasks.length}
                    </span>
                  </div>
                </div>
                <div className="p-4 space-y-3 max-h-[500px] overflow-y-auto">
                  {statusTasks.map((task) => {
                    const priority = priorityColors[task.priority] || priorityColors.medium;
                    const isOverdue = task.due_date && new Date(task.due_date) < new Date() && task.status !== "completed";

                    return (
                      <div
                        key={task.task_id}
                        className={`p-3 bg-gray-50 rounded-lg border ${isOverdue ? "border-red-300 bg-red-50" : "border-gray-200"} hover:shadow-sm transition-shadow`}
                      >
                        <div className="flex items-start justify-between mb-2">
                          <h4 className="font-medium text-gray-900 text-sm">{task.title}</h4>
                          <span className={`px-2 py-0.5 rounded text-xs font-medium ${priority.bg} ${priority.text}`}>
                            {task.priority === "critical" ? "!" :
                             task.priority === "high" ? "H" :
                             task.priority === "medium" ? "M" : "L"}
                          </span>
                        </div>
                        {task.description && (
                          <p className="text-xs text-gray-500 mb-2 line-clamp-2">{task.description}</p>
                        )}
                        <div className="flex items-center justify-between text-xs text-gray-500">
                          <span>{task.case_id}</span>
                          {task.due_date && (
                            <span className={isOverdue ? "text-red-600" : ""}>
                              {new Date(task.due_date).toLocaleDateString("tr-TR")}
                            </span>
                          )}
                        </div>
                      </div>
                    );
                  })}
                  {statusTasks.length === 0 && (
                    <p className="text-center text-gray-400 text-sm py-4">Görev yok</p>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );

  // Milestones View Component
  const MilestonesView = () => (
    <div className="space-y-6">
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <select
              value={selectedCase || ""}
              onChange={(e) => setSelectedCase(e.target.value || null)}
              className="px-3 py-2 border rounded-lg text-sm"
            >
              <option value="">Dava Seçin</option>
              {cases.map((c) => (
                <option key={c.case_id} value={c.case_id}>
                  {c.case_id} - {c.client_name || "İsimsiz"}
                </option>
              ))}
            </select>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setShowTemplateModal(true)}
              className="flex items-center gap-2 px-3 py-2 bg-purple-100 text-purple-700 rounded-lg text-sm hover:bg-purple-200"
            >
              <Sparkles className="w-4 h-4" />
              Şablon Uygula
            </button>
            <button
              onClick={() => setShowNewMilestoneModal(true)}
              disabled={!selectedCase}
              className="flex items-center gap-2 px-3 py-2 bg-indigo-600 text-white rounded-lg text-sm hover:bg-indigo-700 disabled:opacity-50"
            >
              <Plus className="w-4 h-4" />
              Milestone Ekle
            </button>
          </div>
        </div>
      </div>

      {!selectedCase ? (
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-12 text-center text-gray-500">
          <Target className="w-12 h-12 mx-auto mb-3 opacity-50" />
          <p>Milestone'ları görüntülemek için bir dava seçin</p>
        </div>
      ) : (
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
          <div className="relative">
            {/* Progress line */}
            <div className="absolute left-6 top-6 bottom-6 w-1 bg-gray-200 rounded-full">
              <div
                className="w-full bg-gradient-to-b from-green-500 to-indigo-500 rounded-full transition-all"
                style={{
                  height: `${milestones.length > 0
                    ? (milestones.filter(m => m.status === "completed").length / milestones.length) * 100
                    : 0}%`
                }}
              />
            </div>

            {/* Milestones */}
            <div className="space-y-8">
              {milestones.map((milestone, index) => {
                const isCompleted = milestone.status === "completed";
                const isCurrent = milestone.status === "in_progress";

                return (
                  <div key={milestone.milestone_id} className="relative flex gap-4">
                    {/* Dot */}
                    <div className={`relative z-10 flex items-center justify-center w-12 h-12 rounded-full border-4 ${
                      isCompleted ? "bg-green-500 border-green-200" :
                      isCurrent ? "bg-indigo-500 border-indigo-200" :
                      "bg-white border-gray-300"
                    }`}>
                      {isCompleted ? (
                        <CheckCircle2 className="w-6 h-6 text-white" />
                      ) : isCurrent ? (
                        <Target className="w-6 h-6 text-white" />
                      ) : (
                        <span className="text-gray-400 font-medium">{index + 1}</span>
                      )}
                    </div>

                    {/* Content */}
                    <div className={`flex-1 p-4 rounded-lg ${
                      isCompleted ? "bg-green-50 border border-green-200" :
                      isCurrent ? "bg-indigo-50 border border-indigo-200" :
                      "bg-gray-50 border border-gray-200"
                    }`}>
                      <div className="flex items-start justify-between">
                        <div>
                          <h4 className={`font-semibold ${
                            isCompleted ? "text-green-800" :
                            isCurrent ? "text-indigo-800" :
                            "text-gray-700"
                          }`}>
                            {milestone.title}
                          </h4>
                          <p className="text-sm text-gray-600 mt-1">{milestone.description}</p>
                        </div>
                        <div className="text-right">
                          <span className={`inline-flex items-center px-2 py-1 rounded text-xs font-medium ${
                            isCompleted ? "bg-green-100 text-green-700" :
                            isCurrent ? "bg-indigo-100 text-indigo-700" :
                            "bg-gray-100 text-gray-700"
                          }`}>
                            {isCompleted ? "Tamamlandı" : isCurrent ? "Devam Ediyor" : "Bekliyor"}
                          </span>
                          {milestone.target_date && (
                            <p className="text-xs text-gray-500 mt-1">
                              Hedef: {new Date(milestone.target_date).toLocaleDateString("tr-TR")}
                            </p>
                          )}
                        </div>
                      </div>

                      {/* Criteria */}
                      {milestone.completion_criteria && milestone.completion_criteria.length > 0 && (
                        <div className="mt-3 pt-3 border-t border-gray-200">
                          <p className="text-xs font-medium text-gray-500 mb-2">Tamamlama Kriterleri:</p>
                          <ul className="space-y-1">
                            {milestone.completion_criteria.map((criteria, idx) => (
                              <li key={idx} className="flex items-center gap-2 text-sm text-gray-600">
                                <CheckCircle2 className={`w-4 h-4 ${isCompleted ? "text-green-500" : "text-gray-300"}`} />
                                {criteria}
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>

            {milestones.length === 0 && (
              <div className="text-center py-12 text-gray-500">
                <Milestone className="w-12 h-12 mx-auto mb-3 opacity-50" />
                <p>Henüz milestone tanımlanmamış</p>
                <p className="text-sm mt-1">Şablon uygulayarak veya manuel ekleyerek başlayın</p>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );

  // New Task Modal
  const NewTaskModal = () => {
    const [formData, setFormData] = useState({
      case_id: selectedCase || "",
      title: "",
      description: "",
      priority: "medium",
      due_date: "",
      assigned_to: ""
    });
    const [submitting, setSubmitting] = useState(false);

    const handleSubmit = async (e) => {
      e.preventDefault();
      if (!formData.title || !formData.case_id) {
        toast.error("Görev başlığı ve dava zorunludur");
        return;
      }
      setSubmitting(true);
      try {
        const res = await fetch(`${API_URL}/api/timeline/tasks`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`
          },
          body: JSON.stringify(formData)
        });
        if (res.ok) {
          toast.success("Görev oluşturuldu");
          setShowNewTaskModal(false);
          fetchTasks();
          fetchDashboard();
        } else {
          const err = await res.json();
          toast.error(err.detail || "Hata oluştu");
        }
      } catch (error) {
        toast.error("Görev oluşturma hatası");
      }
      setSubmitting(false);
    };

    return (
      <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
        <div className="bg-white rounded-xl shadow-xl max-w-lg w-full max-h-[90vh] overflow-y-auto">
          <div className="p-6 border-b">
            <h3 className="text-lg font-semibold text-gray-900">Yeni Görev Oluştur</h3>
          </div>
          <form onSubmit={handleSubmit} className="p-6 space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Dava *</label>
              <select
                value={formData.case_id}
                onChange={(e) => setFormData({ ...formData, case_id: e.target.value })}
                className="w-full px-3 py-2 border rounded-lg"
                required
              >
                <option value="">Dava Seçin</option>
                {cases.map((c) => (
                  <option key={c.case_id} value={c.case_id}>
                    {c.case_id} - {c.client_name || "İsimsiz"}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Görev Başlığı *</label>
              <input
                type="text"
                value={formData.title}
                onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                className="w-full px-3 py-2 border rounded-lg"
                placeholder="Görev açıklaması..."
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Açıklama</label>
              <textarea
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                className="w-full px-3 py-2 border rounded-lg"
                rows={3}
                placeholder="Detaylı açıklama..."
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Öncelik</label>
                <select
                  value={formData.priority}
                  onChange={(e) => setFormData({ ...formData, priority: e.target.value })}
                  className="w-full px-3 py-2 border rounded-lg"
                >
                  <option value="low">Düşük</option>
                  <option value="medium">Orta</option>
                  <option value="high">Yüksek</option>
                  <option value="critical">Kritik</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Son Tarih</label>
                <input
                  type="date"
                  value={formData.due_date}
                  onChange={(e) => setFormData({ ...formData, due_date: e.target.value })}
                  className="w-full px-3 py-2 border rounded-lg"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Atanan Kişi</label>
              <input
                type="text"
                value={formData.assigned_to}
                onChange={(e) => setFormData({ ...formData, assigned_to: e.target.value })}
                className="w-full px-3 py-2 border rounded-lg"
                placeholder="Kullanıcı adı veya email..."
              />
            </div>

            <div className="flex justify-end gap-3 pt-4">
              <button
                type="button"
                onClick={() => setShowNewTaskModal(false)}
                className="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-lg"
              >
                İptal
              </button>
              <button
                type="submit"
                disabled={submitting}
                className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50"
              >
                {submitting ? "Oluşturuluyor..." : "Oluştur"}
              </button>
            </div>
          </form>
        </div>
      </div>
    );
  };

  // Export Modal
  const ExportModal = () => (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl shadow-xl max-w-md w-full">
        <div className="p-6 border-b">
          <h3 className="text-lg font-semibold text-gray-900">Zaman Çizelgesini Dışa Aktar</h3>
          <p className="text-sm text-gray-500 mt-1">
            Dava: {selectedCase || "Seçili değil"}
          </p>
        </div>
        <div className="p-6 space-y-3">
          {/* CSV Export */}
          <button
            onClick={() => exportTimeline("csv")}
            disabled={exportLoading || !selectedCase}
            className="w-full flex items-center gap-4 p-4 border rounded-lg hover:border-green-300 hover:bg-green-50 transition-colors disabled:opacity-50"
          >
            <div className="p-3 bg-green-100 rounded-lg">
              <FileSpreadsheet className="w-6 h-6 text-green-600" />
            </div>
            <div className="text-left flex-1">
              <h4 className="font-medium text-gray-900">CSV (Excel)</h4>
              <p className="text-sm text-gray-500">Tablo formatında dışa aktar</p>
            </div>
            <Download className="w-5 h-5 text-gray-400" />
          </button>

          {/* PDF Export */}
          <button
            onClick={() => exportTimeline("pdf")}
            disabled={exportLoading || !selectedCase}
            className="w-full flex items-center gap-4 p-4 border rounded-lg hover:border-red-300 hover:bg-red-50 transition-colors disabled:opacity-50"
          >
            <div className="p-3 bg-red-100 rounded-lg">
              <FileText className="w-6 h-6 text-red-600" />
            </div>
            <div className="text-left flex-1">
              <h4 className="font-medium text-gray-900">PDF Raporu</h4>
              <p className="text-sm text-gray-500">Mahkemeye hazır profesyonel rapor</p>
            </div>
            <Download className="w-5 h-5 text-gray-400" />
          </button>

          {/* PNG Export */}
          <button
            onClick={() => exportTimeline("png")}
            disabled={exportLoading || !selectedCase}
            className="w-full flex items-center gap-4 p-4 border rounded-lg hover:border-blue-300 hover:bg-blue-50 transition-colors disabled:opacity-50"
          >
            <div className="p-3 bg-blue-100 rounded-lg">
              <Image className="w-6 h-6 text-blue-600" />
            </div>
            <div className="text-left flex-1">
              <h4 className="font-medium text-gray-900">PNG Görsel</h4>
              <p className="text-sm text-gray-500">Sunumlar için görsel zaman çizelgesi</p>
            </div>
            <Download className="w-5 h-5 text-gray-400" />
          </button>

          {exportLoading && (
            <div className="flex items-center justify-center py-4">
              <RefreshCw className="w-5 h-5 text-indigo-600 animate-spin mr-2" />
              <span className="text-sm text-gray-600">Hazırlanıyor...</span>
            </div>
          )}
        </div>
        <div className="p-4 border-t flex justify-end">
          <button
            onClick={() => setShowExportModal(false)}
            disabled={exportLoading}
            className="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-lg"
          >
            Kapat
          </button>
        </div>
      </div>
    </div>
  );

  // Template Modal
  const TemplateModal = () => (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        <div className="p-6 border-b">
          <h3 className="text-lg font-semibold text-gray-900">Milestone Şablonları</h3>
          <p className="text-sm text-gray-500 mt-1">Dava türüne uygun şablonu seçin</p>
        </div>
        <div className="p-6 space-y-4">
          {templates.map((template) => (
            <div
              key={template.template_id}
              className="p-4 border rounded-lg hover:border-indigo-300 hover:bg-indigo-50 cursor-pointer transition-colors"
              onClick={() => applyTemplate(template.template_id)}
            >
              <div className="flex items-start justify-between">
                <div>
                  <h4 className="font-medium text-gray-900">{template.name}</h4>
                  <p className="text-sm text-gray-500 mt-1">{template.description}</p>
                  <p className="text-xs text-gray-400 mt-2">{template.milestones?.length || 0} milestone</p>
                </div>
                <ChevronRight className="w-5 h-5 text-gray-400" />
              </div>
            </div>
          ))}

          {templates.length === 0 && (
            <p className="text-center text-gray-500 py-8">Şablon bulunamadı</p>
          )}
        </div>
        <div className="p-4 border-t flex justify-end">
          <button
            onClick={() => setShowTemplateModal(false)}
            className="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-lg"
          >
            Kapat
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
          <p className="text-gray-600">Yükleniyor...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b">
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
                <h1 className="text-xl font-bold text-gray-900">Dava Zaman Çizelgesi & Görevler</h1>
                <p className="text-sm text-gray-500">Dava takibi ve görev yönetimi</p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={() => setShowExportModal(true)}
                disabled={!selectedCase}
                className="flex items-center gap-2 px-3 py-2 bg-green-600 text-white rounded-lg text-sm hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <Download className="w-4 h-4" />
                Dışa Aktar
              </button>
              <button
                onClick={() => {
                  fetchDashboard();
                  fetchTasks();
                }}
                className="p-2 hover:bg-gray-100 rounded-lg"
              >
                <RefreshCw className="w-5 h-5 text-gray-600" />
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 py-6">
        {/* Dashboard Stats */}
        <DashboardStats />

        {/* Tabs */}
        <div className="flex gap-2 mb-6">
          {[
            { id: "timeline", label: "Zaman Çizelgesi", icon: Calendar },
            { id: "tasks", label: "Görevler", icon: ListTodo },
            { id: "milestones", label: "Milestone'lar", icon: Target }
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition-colors ${
                activeTab === tab.id
                  ? "bg-indigo-600 text-white"
                  : "bg-white text-gray-700 hover:bg-gray-100"
              }`}
            >
              <tab.icon className="w-4 h-4" />
              {tab.label}
            </button>
          ))}
        </div>

        {/* Tab Content */}
        {activeTab === "timeline" && <TimelineView />}
        {activeTab === "tasks" && <TasksView />}
        {activeTab === "milestones" && <MilestonesView />}
      </main>

      {/* Modals */}
      {showNewTaskModal && <NewTaskModal />}
      {showTemplateModal && <TemplateModal />}
      {showExportModal && <ExportModal />}
    </div>
  );
}
