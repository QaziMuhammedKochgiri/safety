import React, { useEffect, useRef, useState, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from './ui/card';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Textarea } from './ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogTrigger } from './ui/dialog';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { ScrollArea } from './ui/scroll-area';
import { toast } from 'sonner';
import {
  Calendar,
  Clock,
  FileText,
  MessageSquare,
  Users,
  AlertTriangle,
  CheckCircle,
  XCircle,
  Plus,
  Filter,
  Download,
  RefreshCw,
  ChevronLeft,
  ChevronRight,
  ZoomIn,
  ZoomOut,
  Search,
  Target,
  Flag,
  Gavel,
  Shield,
  Loader2,
  Eye,
  Edit,
  Trash2
} from 'lucide-react';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Event type configurations
const EVENT_TYPES = {
  case_created: { icon: FileText, color: '#22c55e', label: 'Fall erstellt' },
  case_updated: { icon: Edit, color: '#3b82f6', label: 'Fall aktualisiert' },
  document_uploaded: { icon: FileText, color: '#8b5cf6', label: 'Dokument hochgeladen' },
  document_signed: { icon: CheckCircle, color: '#10b981', label: 'Dokument unterschrieben' },
  evidence_collected: { icon: Shield, color: '#f59e0b', label: 'Beweis gesammelt' },
  meeting_scheduled: { icon: Calendar, color: '#06b6d4', label: 'Termin geplant' },
  meeting_completed: { icon: CheckCircle, color: '#22c55e', label: 'Termin abgeschlossen' },
  task_created: { icon: Target, color: '#6366f1', label: 'Aufgabe erstellt' },
  task_completed: { icon: CheckCircle, color: '#22c55e', label: 'Aufgabe abgeschlossen' },
  milestone_reached: { icon: Flag, color: '#f97316', label: 'Meilenstein erreicht' },
  court_date_set: { icon: Gavel, color: '#ef4444', label: 'Gerichtstermin festgelegt' },
  message_sent: { icon: MessageSquare, color: '#64748b', label: 'Nachricht gesendet' },
  forensic_analysis: { icon: Search, color: '#a855f7', label: 'Forensische Analyse' },
  client_contact: { icon: Users, color: '#14b8a6', label: 'Kundenkontakt' },
  payment_received: { icon: CheckCircle, color: '#22c55e', label: 'Zahlung erhalten' },
  note_added: { icon: MessageSquare, color: '#94a3b8', label: 'Notiz hinzugefugt' },
  status_change: { icon: AlertTriangle, color: '#eab308', label: 'Statusanderung' },
  deadline_set: { icon: Clock, color: '#ef4444', label: 'Frist gesetzt' },
  custom: { icon: FileText, color: '#64748b', label: 'Sonstiges' }
};

// Priority configurations
const PRIORITY_CONFIG = {
  low: { color: '#22c55e', label: 'Niedrig' },
  medium: { color: '#f59e0b', label: 'Mittel' },
  high: { color: '#ef4444', label: 'Hoch' },
  urgent: { color: '#dc2626', label: 'Dringend' }
};

// Task status configurations
const STATUS_CONFIG = {
  pending: { color: '#94a3b8', label: 'Ausstehend' },
  in_progress: { color: '#3b82f6', label: 'In Bearbeitung' },
  completed: { color: '#22c55e', label: 'Abgeschlossen' },
  cancelled: { color: '#ef4444', label: 'Storniert' },
  blocked: { color: '#f97316', label: 'Blockiert' }
};

const CaseTimeline = ({ caseId, token, clientName }) => {
  const timelineRef = useRef(null);
  const [events, setEvents] = useState([]);
  const [tasks, setTasks] = useState([]);
  const [milestones, setMilestones] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('timeline');
  const [selectedEvent, setSelectedEvent] = useState(null);
  const [filterType, setFilterType] = useState('all');
  const [dateRange, setDateRange] = useState({ start: null, end: null });

  // New Event Dialog
  const [showNewEventDialog, setShowNewEventDialog] = useState(false);
  const [newEvent, setNewEvent] = useState({
    event_type: 'custom',
    title: '',
    description: ''
  });

  // New Task Dialog
  const [showNewTaskDialog, setShowNewTaskDialog] = useState(false);
  const [newTask, setNewTask] = useState({
    title: '',
    description: '',
    priority: 'medium',
    due_date: '',
    assigned_to: ''
  });

  // Fetch data
  const fetchTimelineData = useCallback(async () => {
    if (!caseId || !token) return;

    setLoading(true);
    try {
      const headers = { Authorization: `Bearer ${token}` };

      // Fetch timeline events, tasks, and milestones in parallel
      const [eventsRes, tasksRes, milestonesRes] = await Promise.all([
        axios.get(`${API}/timeline/events/${caseId}`, { headers }),
        axios.get(`${API}/timeline/tasks`, { params: { case_id: caseId }, headers }),
        axios.get(`${API}/timeline/milestones/${caseId}`, { headers })
      ]);

      setEvents(eventsRes.data.events || []);
      setTasks(tasksRes.data.tasks || []);
      setMilestones(milestonesRes.data.milestones || []);
    } catch (error) {
      console.error('Fetch timeline error:', error);
      toast.error('Zeitplan konnte nicht geladen werden');
    } finally {
      setLoading(false);
    }
  }, [caseId, token]);

  useEffect(() => {
    fetchTimelineData();
  }, [fetchTimelineData]);

  // Create new event
  const handleCreateEvent = async () => {
    if (!newEvent.title.trim()) {
      toast.error('Titel erforderlich');
      return;
    }

    try {
      const response = await axios.post(
        `${API}/timeline/events`,
        {
          case_id: caseId,
          ...newEvent
        },
        { headers: { Authorization: `Bearer ${token}` } }
      );

      if (response.data) {
        toast.success('Ereignis erstellt');
        setEvents([response.data, ...events]);
        setShowNewEventDialog(false);
        setNewEvent({ event_type: 'custom', title: '', description: '' });
      }
    } catch (error) {
      console.error('Create event error:', error);
      toast.error('Ereignis konnte nicht erstellt werden');
    }
  };

  // Create new task
  const handleCreateTask = async () => {
    if (!newTask.title.trim()) {
      toast.error('Titel erforderlich');
      return;
    }

    try {
      const response = await axios.post(
        `${API}/timeline/tasks`,
        {
          case_id: caseId,
          ...newTask
        },
        { headers: { Authorization: `Bearer ${token}` } }
      );

      if (response.data) {
        toast.success('Aufgabe erstellt');
        setTasks([...tasks, response.data]);
        setShowNewTaskDialog(false);
        setNewTask({
          title: '',
          description: '',
          priority: 'medium',
          due_date: '',
          assigned_to: ''
        });
      }
    } catch (error) {
      console.error('Create task error:', error);
      toast.error('Aufgabe konnte nicht erstellt werden');
    }
  };

  // Update task status
  const handleUpdateTaskStatus = async (taskId, newStatus) => {
    try {
      await axios.put(
        `${API}/timeline/tasks/${taskId}`,
        { status: newStatus },
        { headers: { Authorization: `Bearer ${token}` } }
      );

      setTasks(tasks.map(t =>
        t.task_id === taskId
          ? { ...t, status: newStatus, completed_at: newStatus === 'completed' ? new Date().toISOString() : null }
          : t
      ));
      toast.success('Aufgabenstatus aktualisiert');
    } catch (error) {
      console.error('Update task error:', error);
      toast.error('Aktualisierung fehlgeschlagen');
    }
  };

  // Update milestone status
  const handleUpdateMilestone = async (milestoneId, newStatus) => {
    try {
      await axios.put(
        `${API}/timeline/milestones/${milestoneId}`,
        { status: newStatus },
        { headers: { Authorization: `Bearer ${token}` } }
      );

      setMilestones(milestones.map(m =>
        m.milestone_id === milestoneId
          ? { ...m, status: newStatus, completed_at: newStatus === 'completed' ? new Date().toISOString() : null }
          : m
      ));
      toast.success('Meilenstein aktualisiert');
    } catch (error) {
      console.error('Update milestone error:', error);
      toast.error('Aktualisierung fehlgeschlagen');
    }
  };

  // Filter events
  const filteredEvents = events.filter(event => {
    if (filterType === 'all') return true;
    return event.event_type === filterType;
  });

  // Format date
  const formatDate = (dateStr) => {
    if (!dateStr) return '-';
    const date = new Date(dateStr);
    return date.toLocaleDateString('de-DE', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  // Get event icon component
  const getEventIcon = (eventType) => {
    const config = EVENT_TYPES[eventType] || EVENT_TYPES.custom;
    const IconComponent = config.icon;
    return <IconComponent className="w-4 h-4" style={{ color: config.color }} />;
  };

  // Calculate timeline statistics
  const stats = {
    totalEvents: events.length,
    totalTasks: tasks.length,
    completedTasks: tasks.filter(t => t.status === 'completed').length,
    pendingTasks: tasks.filter(t => t.status === 'pending').length,
    overdueTasks: tasks.filter(t =>
      t.due_date && new Date(t.due_date) < new Date() && t.status !== 'completed'
    ).length,
    completedMilestones: milestones.filter(m => m.status === 'completed').length,
    totalMilestones: milestones.length
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <Loader2 className="w-8 h-8 animate-spin text-gray-400" />
        <span className="ml-2">Zeitplan wird geladen...</span>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-semibold flex items-center gap-2">
            <Calendar className="w-5 h-5" />
            Fall-Zeitplan
          </h2>
          {clientName && (
            <p className="text-sm text-gray-500">{clientName}</p>
          )}
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" onClick={fetchTimelineData}>
            <RefreshCw className="w-4 h-4 mr-1" />
            Aktualisieren
          </Button>
          <Dialog open={showNewEventDialog} onOpenChange={setShowNewEventDialog}>
            <DialogTrigger asChild>
              <Button size="sm">
                <Plus className="w-4 h-4 mr-1" />
                Ereignis
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Neues Ereignis erstellen</DialogTitle>
              </DialogHeader>
              <div className="space-y-4 py-4">
                <div className="space-y-2">
                  <Label>Ereignistyp</Label>
                  <Select
                    value={newEvent.event_type}
                    onValueChange={(v) => setNewEvent({...newEvent, event_type: v})}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {Object.entries(EVENT_TYPES).map(([key, config]) => (
                        <SelectItem key={key} value={key}>
                          {config.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label>Titel</Label>
                  <Input
                    value={newEvent.title}
                    onChange={(e) => setNewEvent({...newEvent, title: e.target.value})}
                    placeholder="Ereignistitel..."
                  />
                </div>
                <div className="space-y-2">
                  <Label>Beschreibung</Label>
                  <Textarea
                    value={newEvent.description}
                    onChange={(e) => setNewEvent({...newEvent, description: e.target.value})}
                    placeholder="Optionale Beschreibung..."
                    rows={3}
                  />
                </div>
              </div>
              <DialogFooter>
                <Button variant="outline" onClick={() => setShowNewEventDialog(false)}>
                  Abbrechen
                </Button>
                <Button onClick={handleCreateEvent}>
                  Erstellen
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
          <Dialog open={showNewTaskDialog} onOpenChange={setShowNewTaskDialog}>
            <DialogTrigger asChild>
              <Button size="sm" variant="secondary">
                <Plus className="w-4 h-4 mr-1" />
                Aufgabe
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Neue Aufgabe erstellen</DialogTitle>
              </DialogHeader>
              <div className="space-y-4 py-4">
                <div className="space-y-2">
                  <Label>Titel</Label>
                  <Input
                    value={newTask.title}
                    onChange={(e) => setNewTask({...newTask, title: e.target.value})}
                    placeholder="Aufgabentitel..."
                  />
                </div>
                <div className="space-y-2">
                  <Label>Beschreibung</Label>
                  <Textarea
                    value={newTask.description}
                    onChange={(e) => setNewTask({...newTask, description: e.target.value})}
                    placeholder="Optionale Beschreibung..."
                    rows={2}
                  />
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>Prioritat</Label>
                    <Select
                      value={newTask.priority}
                      onValueChange={(v) => setNewTask({...newTask, priority: v})}
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {Object.entries(PRIORITY_CONFIG).map(([key, config]) => (
                          <SelectItem key={key} value={key}>
                            {config.label}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-2">
                    <Label>Falligkeitsdatum</Label>
                    <Input
                      type="date"
                      value={newTask.due_date}
                      onChange={(e) => setNewTask({...newTask, due_date: e.target.value})}
                    />
                  </div>
                </div>
                <div className="space-y-2">
                  <Label>Zugewiesen an</Label>
                  <Input
                    value={newTask.assigned_to}
                    onChange={(e) => setNewTask({...newTask, assigned_to: e.target.value})}
                    placeholder="E-Mail oder Name..."
                  />
                </div>
              </div>
              <DialogFooter>
                <Button variant="outline" onClick={() => setShowNewTaskDialog(false)}>
                  Abbrechen
                </Button>
                <Button onClick={handleCreateTask}>
                  Erstellen
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        </div>
      </div>

      {/* Statistics Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-gray-500">Ereignisse</p>
                <p className="text-2xl font-bold">{stats.totalEvents}</p>
              </div>
              <FileText className="w-8 h-8 text-blue-500 opacity-50" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-gray-500">Aufgaben</p>
                <p className="text-2xl font-bold">
                  {stats.completedTasks}/{stats.totalTasks}
                </p>
              </div>
              <Target className="w-8 h-8 text-green-500 opacity-50" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-gray-500">Uberfällig</p>
                <p className="text-2xl font-bold text-red-500">{stats.overdueTasks}</p>
              </div>
              <AlertTriangle className="w-8 h-8 text-red-500 opacity-50" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-gray-500">Meilensteine</p>
                <p className="text-2xl font-bold">
                  {stats.completedMilestones}/{stats.totalMilestones}
                </p>
              </div>
              <Flag className="w-8 h-8 text-orange-500 opacity-50" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Main Content Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="timeline">
            <Clock className="w-4 h-4 mr-1" />
            Zeitplan
          </TabsTrigger>
          <TabsTrigger value="tasks">
            <Target className="w-4 h-4 mr-1" />
            Aufgaben ({tasks.length})
          </TabsTrigger>
          <TabsTrigger value="milestones">
            <Flag className="w-4 h-4 mr-1" />
            Meilensteine ({milestones.length})
          </TabsTrigger>
        </TabsList>

        {/* Timeline Tab */}
        <TabsContent value="timeline" className="mt-4">
          <Card>
            <CardHeader className="pb-2">
              <div className="flex items-center justify-between">
                <CardTitle className="text-sm">Ereignis-Verlauf</CardTitle>
                <Select value={filterType} onValueChange={setFilterType}>
                  <SelectTrigger className="w-[180px]">
                    <Filter className="w-4 h-4 mr-2" />
                    <SelectValue placeholder="Filter" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">Alle Ereignisse</SelectItem>
                    {Object.entries(EVENT_TYPES).map(([key, config]) => (
                      <SelectItem key={key} value={key}>
                        {config.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </CardHeader>
            <CardContent>
              <ScrollArea className="h-[400px] pr-4">
                {filteredEvents.length === 0 ? (
                  <div className="text-center py-8 text-gray-500">
                    <Clock className="w-12 h-12 mx-auto mb-2 opacity-30" />
                    <p>Keine Ereignisse gefunden</p>
                  </div>
                ) : (
                  <div className="relative">
                    {/* Timeline line */}
                    <div className="absolute left-4 top-0 bottom-0 w-0.5 bg-gray-200" />

                    {/* Timeline events */}
                    <div className="space-y-4">
                      {filteredEvents.map((event, index) => {
                        const config = EVENT_TYPES[event.event_type] || EVENT_TYPES.custom;
                        const IconComponent = config.icon;

                        return (
                          <div key={event.event_id || index} className="relative pl-10">
                            {/* Icon circle */}
                            <div
                              className="absolute left-0 w-8 h-8 rounded-full flex items-center justify-center bg-white border-2"
                              style={{ borderColor: config.color }}
                            >
                              <IconComponent className="w-4 h-4" style={{ color: config.color }} />
                            </div>

                            {/* Event content */}
                            <div className="bg-gray-50 rounded-lg p-3 hover:bg-gray-100 transition-colors">
                              <div className="flex items-start justify-between">
                                <div>
                                  <h4 className="font-medium text-sm">{event.title}</h4>
                                  {event.description && (
                                    <p className="text-xs text-gray-500 mt-1">
                                      {event.description}
                                    </p>
                                  )}
                                  <div className="flex items-center gap-2 mt-2">
                                    <Badge
                                      variant="outline"
                                      className="text-xs"
                                      style={{ borderColor: config.color, color: config.color }}
                                    >
                                      {config.label}
                                    </Badge>
                                    {event.is_automated && (
                                      <Badge variant="secondary" className="text-xs">
                                        Automatisch
                                      </Badge>
                                    )}
                                  </div>
                                </div>
                                <div className="text-right">
                                  <span className="text-xs text-gray-400">
                                    {formatDate(event.created_at)}
                                  </span>
                                  {event.created_by && (
                                    <p className="text-xs text-gray-400 mt-1">
                                      von {event.created_by}
                                    </p>
                                  )}
                                </div>
                              </div>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                )}
              </ScrollArea>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Tasks Tab */}
        <TabsContent value="tasks" className="mt-4">
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm">Aufgabenliste</CardTitle>
            </CardHeader>
            <CardContent>
              <ScrollArea className="h-[400px]">
                {tasks.length === 0 ? (
                  <div className="text-center py-8 text-gray-500">
                    <Target className="w-12 h-12 mx-auto mb-2 opacity-30" />
                    <p>Keine Aufgaben vorhanden</p>
                  </div>
                ) : (
                  <div className="space-y-3">
                    {tasks.map((task) => {
                      const priorityConfig = PRIORITY_CONFIG[task.priority] || PRIORITY_CONFIG.medium;
                      const statusConfig = STATUS_CONFIG[task.status] || STATUS_CONFIG.pending;
                      const isOverdue = task.due_date && new Date(task.due_date) < new Date() && task.status !== 'completed';

                      return (
                        <div
                          key={task.task_id}
                          className={`p-3 rounded-lg border ${
                            isOverdue ? 'border-red-300 bg-red-50' : 'border-gray-200 bg-white'
                          }`}
                        >
                          <div className="flex items-start justify-between">
                            <div className="flex-1">
                              <div className="flex items-center gap-2">
                                <h4 className={`font-medium text-sm ${
                                  task.status === 'completed' ? 'line-through text-gray-400' : ''
                                }`}>
                                  {task.title}
                                </h4>
                                <Badge
                                  variant="outline"
                                  className="text-xs"
                                  style={{
                                    borderColor: priorityConfig.color,
                                    color: priorityConfig.color
                                  }}
                                >
                                  {priorityConfig.label}
                                </Badge>
                              </div>
                              {task.description && (
                                <p className="text-xs text-gray-500 mt-1">{task.description}</p>
                              )}
                              <div className="flex items-center gap-3 mt-2 text-xs text-gray-500">
                                {task.due_date && (
                                  <span className={`flex items-center gap-1 ${isOverdue ? 'text-red-500' : ''}`}>
                                    <Clock className="w-3 h-3" />
                                    {formatDate(task.due_date).split(',')[0]}
                                    {isOverdue && ' (uberfällig)'}
                                  </span>
                                )}
                                {task.assigned_to && (
                                  <span className="flex items-center gap-1">
                                    <Users className="w-3 h-3" />
                                    {task.assigned_to}
                                  </span>
                                )}
                              </div>
                            </div>
                            <div className="flex items-center gap-2">
                              <Select
                                value={task.status}
                                onValueChange={(v) => handleUpdateTaskStatus(task.task_id, v)}
                              >
                                <SelectTrigger className="w-[130px] h-8">
                                  <SelectValue />
                                </SelectTrigger>
                                <SelectContent>
                                  {Object.entries(STATUS_CONFIG).map(([key, config]) => (
                                    <SelectItem key={key} value={key}>
                                      {config.label}
                                    </SelectItem>
                                  ))}
                                </SelectContent>
                              </Select>
                            </div>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                )}
              </ScrollArea>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Milestones Tab */}
        <TabsContent value="milestones" className="mt-4">
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm">Fall-Meilensteine</CardTitle>
            </CardHeader>
            <CardContent>
              <ScrollArea className="h-[400px]">
                {milestones.length === 0 ? (
                  <div className="text-center py-8 text-gray-500">
                    <Flag className="w-12 h-12 mx-auto mb-2 opacity-30" />
                    <p>Keine Meilensteine vorhanden</p>
                  </div>
                ) : (
                  <div className="relative">
                    {/* Progress bar */}
                    <div className="mb-6">
                      <div className="flex items-center justify-between text-sm mb-2">
                        <span className="text-gray-500">Fortschritt</span>
                        <span className="font-medium">
                          {stats.completedMilestones} / {stats.totalMilestones} abgeschlossen
                        </span>
                      </div>
                      <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
                        <div
                          className="h-full bg-green-500 transition-all"
                          style={{
                            width: `${(stats.completedMilestones / stats.totalMilestones) * 100}%`
                          }}
                        />
                      </div>
                    </div>

                    {/* Milestone list */}
                    <div className="space-y-3">
                      {milestones.map((milestone, index) => {
                        const isCompleted = milestone.status === 'completed';
                        const isInProgress = milestone.status === 'in_progress';

                        return (
                          <div
                            key={milestone.milestone_id}
                            className={`p-3 rounded-lg border ${
                              isCompleted
                                ? 'border-green-300 bg-green-50'
                                : isInProgress
                                  ? 'border-blue-300 bg-blue-50'
                                  : 'border-gray-200 bg-white'
                            }`}
                          >
                            <div className="flex items-center gap-3">
                              <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
                                isCompleted
                                  ? 'bg-green-500 text-white'
                                  : isInProgress
                                    ? 'bg-blue-500 text-white'
                                    : 'bg-gray-200 text-gray-500'
                              }`}>
                                {isCompleted ? (
                                  <CheckCircle className="w-5 h-5" />
                                ) : (
                                  <span className="font-medium text-sm">{index + 1}</span>
                                )}
                              </div>
                              <div className="flex-1">
                                <h4 className="font-medium text-sm">{milestone.title}</h4>
                                {milestone.description && (
                                  <p className="text-xs text-gray-500">{milestone.description}</p>
                                )}
                                <div className="flex items-center gap-2 mt-1">
                                  {milestone.phase && (
                                    <Badge variant="outline" className="text-xs">
                                      {milestone.phase}
                                    </Badge>
                                  )}
                                  {milestone.target_date && (
                                    <span className="text-xs text-gray-400">
                                      Ziel: {formatDate(milestone.target_date).split(',')[0]}
                                    </span>
                                  )}
                                </div>
                              </div>
                              <div>
                                <Select
                                  value={milestone.status}
                                  onValueChange={(v) => handleUpdateMilestone(milestone.milestone_id, v)}
                                >
                                  <SelectTrigger className="w-[130px] h-8">
                                    <SelectValue />
                                  </SelectTrigger>
                                  <SelectContent>
                                    <SelectItem value="pending">Ausstehend</SelectItem>
                                    <SelectItem value="in_progress">In Bearbeitung</SelectItem>
                                    <SelectItem value="completed">Abgeschlossen</SelectItem>
                                    <SelectItem value="skipped">Ubersprungen</SelectItem>
                                  </SelectContent>
                                </Select>
                              </div>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                )}
              </ScrollArea>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default CaseTimeline;
