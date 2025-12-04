import React, { useState, useEffect, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";
import { toast } from "sonner";
import {
  Calendar,
  ChevronLeft,
  ChevronRight,
  Plus,
  Clock,
  MapPin,
  Users,
  AlertTriangle,
  RefreshCw,
  Filter,
  Download,
  X,
  Check,
  Gavel,
  FileText,
  Bell,
  Video,
  Scale,
  Target
} from "lucide-react";

const API_URL = process.env.REACT_APP_API_URL || "http://localhost:8000";

// Event type config
const eventTypes = {
  meeting: { label: "Toplantı", color: "#4F46E5", icon: Users },
  court_date: { label: "Mahkeme", color: "#DC2626", icon: Gavel },
  deadline: { label: "Son Tarih", color: "#F59E0B", icon: AlertTriangle },
  task: { label: "Görev", color: "#10B981", icon: Target },
  reminder: { label: "Hatırlatma", color: "#8B5CF6", icon: Bell },
  consultation: { label: "Danışmanlık", color: "#3B82F6", icon: Video },
  deposition: { label: "İfade", color: "#EC4899", icon: FileText },
  filing: { label: "Dosyalama", color: "#6366F1", icon: FileText },
  hearing: { label: "Duruşma", color: "#EF4444", icon: Scale },
  other: { label: "Diğer", color: "#6B7280", icon: Calendar }
};

export default function AdminCalendar() {
  const { token } = useAuth();
  const navigate = useNavigate();

  // State
  const [loading, setLoading] = useState(true);
  const [events, setEvents] = useState([]);
  const [currentDate, setCurrentDate] = useState(new Date());
  const [view, setView] = useState("month"); // month, week, day
  const [selectedDate, setSelectedDate] = useState(null);
  const [showEventModal, setShowEventModal] = useState(false);
  const [selectedEvent, setSelectedEvent] = useState(null);
  const [upcomingDeadlines, setUpcomingDeadlines] = useState({ urgent: [], upcoming: [] });

  // Form state
  const [eventForm, setEventForm] = useState({
    title: "",
    event_type: "meeting",
    start_time: "",
    end_time: "",
    all_day: false,
    location: "",
    description: "",
    client_name: ""
  });

  // Fetch events
  const fetchEvents = useCallback(async () => {
    const year = currentDate.getFullYear();
    const month = currentDate.getMonth();

    // Get first and last day of displayed calendar (including overflow days)
    const firstDay = new Date(year, month, 1);
    firstDay.setDate(firstDay.getDate() - firstDay.getDay());
    const lastDay = new Date(year, month + 1, 0);
    lastDay.setDate(lastDay.getDate() + (6 - lastDay.getDay()));

    try {
      const res = await fetch(
        `${API_URL}/api/calendar/events?start_date=${firstDay.toISOString()}&end_date=${lastDay.toISOString()}`,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      if (res.ok) {
        const data = await res.json();
        setEvents(data.events || []);
      }
    } catch (error) {
      console.error("Events fetch error:", error);
    }
    setLoading(false);
  }, [token, currentDate]);

  // Fetch deadlines
  const fetchDeadlines = useCallback(async () => {
    try {
      const res = await fetch(`${API_URL}/api/calendar/deadlines?days=14`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setUpcomingDeadlines({
          urgent: data.urgent || [],
          upcoming: data.upcoming || []
        });
      }
    } catch (error) {
      console.error("Deadlines fetch error:", error);
    }
  }, [token]);

  useEffect(() => {
    fetchEvents();
    fetchDeadlines();
  }, [fetchEvents, fetchDeadlines]);

  // Navigate months
  const prevMonth = () => {
    setCurrentDate(new Date(currentDate.getFullYear(), currentDate.getMonth() - 1, 1));
  };

  const nextMonth = () => {
    setCurrentDate(new Date(currentDate.getFullYear(), currentDate.getMonth() + 1, 1));
  };

  const goToToday = () => {
    setCurrentDate(new Date());
  };

  // Open event modal
  const openNewEvent = (date) => {
    setSelectedEvent(null);
    const dateStr = date ? date.toISOString().slice(0, 16) : new Date().toISOString().slice(0, 16);
    setEventForm({
      title: "",
      event_type: "meeting",
      start_time: dateStr,
      end_time: "",
      all_day: false,
      location: "",
      description: "",
      client_name: ""
    });
    setShowEventModal(true);
  };

  const openEditEvent = (event) => {
    setSelectedEvent(event);
    setEventForm({
      title: event.title,
      event_type: event.event_type,
      start_time: new Date(event.start_time).toISOString().slice(0, 16),
      end_time: event.end_time ? new Date(event.end_time).toISOString().slice(0, 16) : "",
      all_day: event.all_day || false,
      location: event.location || "",
      description: event.description || "",
      client_name: event.client_name || ""
    });
    setShowEventModal(true);
  };

  // Save event
  const saveEvent = async () => {
    if (!eventForm.title || !eventForm.start_time) {
      toast.error("Başlık ve başlangıç zamanı zorunludur");
      return;
    }

    try {
      const url = selectedEvent
        ? `${API_URL}/api/calendar/events/${selectedEvent.event_id}`
        : `${API_URL}/api/calendar/events`;

      const res = await fetch(url, {
        method: selectedEvent ? "PUT" : "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify(eventForm)
      });

      if (res.ok) {
        toast.success(selectedEvent ? "Etkinlik güncellendi" : "Etkinlik oluşturuldu");
        setShowEventModal(false);
        fetchEvents();
        fetchDeadlines();
      } else {
        const err = await res.json();
        toast.error(err.detail || "Hata oluştu");
      }
    } catch (error) {
      toast.error("İşlem hatası");
    }
  };

  // Delete event
  const deleteEvent = async () => {
    if (!selectedEvent || !window.confirm("Bu etkinliği silmek istediğinize emin misiniz?")) return;

    try {
      const res = await fetch(`${API_URL}/api/calendar/events/${selectedEvent.event_id}`, {
        method: "DELETE",
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        toast.success("Etkinlik silindi");
        setShowEventModal(false);
        fetchEvents();
      }
    } catch (error) {
      toast.error("Silme hatası");
    }
  };

  // Export ICS
  const exportICS = async () => {
    try {
      const res = await fetch(`${API_URL}/api/calendar/export/ics`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        const blob = new Blob([data.content], { type: "text/calendar" });
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = data.filename;
        a.click();
        toast.success("Takvim indirildi");
      }
    } catch (error) {
      toast.error("Dışa aktarma hatası");
    }
  };

  // Generate calendar grid
  const generateCalendarDays = () => {
    const year = currentDate.getFullYear();
    const month = currentDate.getMonth();

    const firstDay = new Date(year, month, 1);
    const lastDay = new Date(year, month + 1, 0);

    const days = [];
    const startPadding = firstDay.getDay();

    // Previous month days
    for (let i = startPadding - 1; i >= 0; i--) {
      const date = new Date(year, month, -i);
      days.push({ date, isCurrentMonth: false });
    }

    // Current month days
    for (let i = 1; i <= lastDay.getDate(); i++) {
      const date = new Date(year, month, i);
      days.push({ date, isCurrentMonth: true });
    }

    // Next month days
    const remainingDays = 42 - days.length;
    for (let i = 1; i <= remainingDays; i++) {
      const date = new Date(year, month + 1, i);
      days.push({ date, isCurrentMonth: false });
    }

    return days;
  };

  // Get events for a specific day
  const getEventsForDay = (date) => {
    const dayStart = new Date(date);
    dayStart.setHours(0, 0, 0, 0);
    const dayEnd = new Date(date);
    dayEnd.setHours(23, 59, 59, 999);

    return events.filter((event) => {
      const eventDate = new Date(event.start_time);
      return eventDate >= dayStart && eventDate <= dayEnd;
    });
  };

  const calendarDays = generateCalendarDays();
  const today = new Date();
  today.setHours(0, 0, 0, 0);

  const monthNames = [
    "Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran",
    "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"
  ];

  const dayNames = ["Paz", "Pzt", "Sal", "Çar", "Per", "Cum", "Cmt"];

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <RefreshCw className="w-8 h-8 text-indigo-600 animate-spin" />
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
              <button onClick={() => navigate("/admin")} className="text-gray-500 hover:text-gray-700">
                ← Admin
              </button>
              <div>
                <h1 className="text-xl font-bold text-gray-900">Takvim</h1>
                <p className="text-sm text-gray-500">Etkinlik ve randevu yönetimi</p>
              </div>
            </div>

            <div className="flex items-center gap-3">
              <button
                onClick={exportICS}
                className="flex items-center gap-2 px-3 py-2 text-gray-700 hover:bg-gray-100 rounded-lg"
              >
                <Download className="w-4 h-4" />
                ICS
              </button>
              <button
                onClick={() => openNewEvent(new Date())}
                className="flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700"
              >
                <Plus className="w-4 h-4" />
                Yeni Etkinlik
              </button>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 py-6">
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          {/* Calendar Grid */}
          <div className="lg:col-span-3 bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
            {/* Calendar Header */}
            <div className="p-4 border-b flex items-center justify-between">
              <div className="flex items-center gap-4">
                <button onClick={prevMonth} className="p-2 hover:bg-gray-100 rounded-lg">
                  <ChevronLeft className="w-5 h-5" />
                </button>
                <h2 className="text-lg font-semibold text-gray-900">
                  {monthNames[currentDate.getMonth()]} {currentDate.getFullYear()}
                </h2>
                <button onClick={nextMonth} className="p-2 hover:bg-gray-100 rounded-lg">
                  <ChevronRight className="w-5 h-5" />
                </button>
              </div>
              <button
                onClick={goToToday}
                className="px-3 py-1.5 text-sm font-medium text-indigo-600 hover:bg-indigo-50 rounded-lg"
              >
                Bugün
              </button>
            </div>

            {/* Day Names */}
            <div className="grid grid-cols-7 border-b">
              {dayNames.map((day) => (
                <div key={day} className="py-2 text-center text-sm font-medium text-gray-500">
                  {day}
                </div>
              ))}
            </div>

            {/* Calendar Days */}
            <div className="grid grid-cols-7">
              {calendarDays.map(({ date, isCurrentMonth }, idx) => {
                const dayEvents = getEventsForDay(date);
                const isToday = date.getTime() === today.getTime();
                const isSelected = selectedDate && date.getTime() === selectedDate.getTime();

                return (
                  <div
                    key={idx}
                    onClick={() => {
                      setSelectedDate(date);
                      if (dayEvents.length === 0) openNewEvent(date);
                    }}
                    className={`min-h-[100px] border-b border-r p-2 cursor-pointer transition-colors ${
                      isCurrentMonth ? "bg-white" : "bg-gray-50"
                    } ${isSelected ? "bg-indigo-50" : "hover:bg-gray-50"}`}
                  >
                    <div className={`text-sm font-medium mb-1 ${
                      isToday
                        ? "w-7 h-7 flex items-center justify-center bg-indigo-600 text-white rounded-full"
                        : isCurrentMonth
                        ? "text-gray-900"
                        : "text-gray-400"
                    }`}>
                      {date.getDate()}
                    </div>
                    <div className="space-y-1">
                      {dayEvents.slice(0, 3).map((event) => {
                        const config = eventTypes[event.event_type] || eventTypes.other;
                        return (
                          <div
                            key={event.event_id}
                            onClick={(e) => {
                              e.stopPropagation();
                              openEditEvent(event);
                            }}
                            className="text-xs p-1 rounded truncate cursor-pointer hover:opacity-80"
                            style={{ backgroundColor: `${event.color || config.color}20`, color: event.color || config.color }}
                          >
                            {event.title}
                          </div>
                        );
                      })}
                      {dayEvents.length > 3 && (
                        <div className="text-xs text-gray-500 pl-1">
                          +{dayEvents.length - 3} daha
                        </div>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            {/* Upcoming Deadlines */}
            <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-4">
              <h3 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
                <AlertTriangle className="w-5 h-5 text-orange-500" />
                Yaklaşan Tarihler
              </h3>

              {upcomingDeadlines.urgent.length > 0 && (
                <div className="mb-4">
                  <p className="text-xs font-medium text-red-600 mb-2">Acil (3 gün içinde)</p>
                  <div className="space-y-2">
                    {upcomingDeadlines.urgent.map((d) => (
                      <div key={d.event_id} className="p-2 bg-red-50 border border-red-200 rounded-lg">
                        <p className="text-sm font-medium text-red-800">{d.title}</p>
                        <p className="text-xs text-red-600">
                          {new Date(d.start_time).toLocaleDateString("tr-TR")} ({d.days_until} gün)
                        </p>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {upcomingDeadlines.upcoming.length > 0 && (
                <div>
                  <p className="text-xs font-medium text-yellow-600 mb-2">Bu Hafta</p>
                  <div className="space-y-2">
                    {upcomingDeadlines.upcoming.map((d) => (
                      <div key={d.event_id} className="p-2 bg-yellow-50 border border-yellow-200 rounded-lg">
                        <p className="text-sm font-medium text-yellow-800">{d.title}</p>
                        <p className="text-xs text-yellow-600">
                          {new Date(d.start_time).toLocaleDateString("tr-TR")}
                        </p>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {upcomingDeadlines.urgent.length === 0 && upcomingDeadlines.upcoming.length === 0 && (
                <p className="text-sm text-gray-500 text-center py-4">
                  Yaklaşan kritik tarih yok
                </p>
              )}
            </div>

            {/* Event Types Legend */}
            <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-4">
              <h3 className="font-semibold text-gray-900 mb-4">Etkinlik Türleri</h3>
              <div className="space-y-2">
                {Object.entries(eventTypes).slice(0, 6).map(([key, config]) => {
                  const Icon = config.icon;
                  return (
                    <div key={key} className="flex items-center gap-2">
                      <div className="w-3 h-3 rounded-full" style={{ backgroundColor: config.color }} />
                      <Icon className="w-4 h-4" style={{ color: config.color }} />
                      <span className="text-sm text-gray-600">{config.label}</span>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        </div>
      </main>

      {/* Event Modal */}
      {showEventModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl shadow-xl max-w-lg w-full max-h-[90vh] overflow-y-auto">
            <div className="p-6 border-b flex items-center justify-between">
              <h3 className="text-lg font-semibold text-gray-900">
                {selectedEvent ? "Etkinliği Düzenle" : "Yeni Etkinlik"}
              </h3>
              <button onClick={() => setShowEventModal(false)} className="p-2 hover:bg-gray-100 rounded-lg">
                <X className="w-5 h-5 text-gray-500" />
              </button>
            </div>

            <div className="p-6 space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Başlık *</label>
                <input
                  type="text"
                  value={eventForm.title}
                  onChange={(e) => setEventForm({ ...eventForm, title: e.target.value })}
                  className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500"
                  placeholder="Etkinlik başlığı..."
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Tür</label>
                <select
                  value={eventForm.event_type}
                  onChange={(e) => setEventForm({ ...eventForm, event_type: e.target.value })}
                  className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500"
                >
                  {Object.entries(eventTypes).map(([key, config]) => (
                    <option key={key} value={key}>{config.label}</option>
                  ))}
                </select>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Başlangıç *</label>
                  <input
                    type="datetime-local"
                    value={eventForm.start_time}
                    onChange={(e) => setEventForm({ ...eventForm, start_time: e.target.value })}
                    className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Bitiş</label>
                  <input
                    type="datetime-local"
                    value={eventForm.end_time}
                    onChange={(e) => setEventForm({ ...eventForm, end_time: e.target.value })}
                    className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Konum</label>
                <input
                  type="text"
                  value={eventForm.location}
                  onChange={(e) => setEventForm({ ...eventForm, location: e.target.value })}
                  className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500"
                  placeholder="Adres veya link..."
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Müvekkil</label>
                <input
                  type="text"
                  value={eventForm.client_name}
                  onChange={(e) => setEventForm({ ...eventForm, client_name: e.target.value })}
                  className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500"
                  placeholder="Müvekkil adı..."
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Açıklama</label>
                <textarea
                  value={eventForm.description}
                  onChange={(e) => setEventForm({ ...eventForm, description: e.target.value })}
                  className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500"
                  rows={3}
                  placeholder="Detaylar..."
                />
              </div>
            </div>

            <div className="p-4 border-t flex justify-between">
              {selectedEvent && (
                <button
                  onClick={deleteEvent}
                  className="px-4 py-2 text-red-600 hover:bg-red-50 rounded-lg"
                >
                  Sil
                </button>
              )}
              <div className={`flex gap-3 ${!selectedEvent ? "ml-auto" : ""}`}>
                <button
                  onClick={() => setShowEventModal(false)}
                  className="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-lg"
                >
                  İptal
                </button>
                <button
                  onClick={saveEvent}
                  className="flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700"
                >
                  <Check className="w-4 h-4" />
                  Kaydet
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
