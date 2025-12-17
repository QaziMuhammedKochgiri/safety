import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { Clock, ArrowLeft, Loader2, Download } from 'lucide-react';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { toast } from 'sonner';
import axios from 'axios';

const API = process.env.REACT_APP_API_URL || "/api";

const TimelineGenerator = () => {
  const navigate = useNavigate();
  const { token } = useAuth();
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [eventsList, setEventsList] = useState('');

  const handleGenerate = async () => {
    if (!eventsList.trim()) {
      toast.error('Please describe events');
      return;
    }

    setLoading(true);
    try {
      const events = eventsList.split('\n').filter(e => e.trim()).map((e, idx) => ({
        date: '2024-01-01',
        event_type: 'incident',
        description: e.trim(),
        severity: 'moderate'
      }));

      const response = await axios.post(
        `${API}/ai/generate-timeline`,
        { case_id: `case_${Date.now()}`, events },
        { headers: { Authorization: `Bearer ${token}` } }
      );

      setResult(response.data);
      toast.success('Timeline generated!');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Generation failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-pink-50 via-rose-50 to-red-50">
      <div className="max-w-6xl mx-auto p-4 md:p-8">
        <Button variant="ghost" onClick={() => navigate('/dashboard')} className="mb-4">
          <ArrowLeft className="w-4 h-4 mr-2" />Back
        </Button>
        <div className="bg-gradient-to-r from-pink-600 to-rose-600 rounded-3xl shadow-2xl p-8 text-white mb-8">
          <div className="flex items-center gap-4">
            <div className="bg-white/20 p-4 rounded-2xl">
              <Clock className="w-12 h-12" />
            </div>
            <div>
              <h1 className="text-4xl font-bold mb-2">Timeline Generator</h1>
              <p className="text-pink-100 text-lg">Create chronological case timeline</p>
            </div>
          </div>
        </div>

        {!result ? (
          <Card className="border-2 shadow-xl">
            <CardHeader><CardTitle>List Case Events</CardTitle></CardHeader>
            <CardContent className="space-y-6">
              <textarea
                value={eventsList}
                onChange={(e) => setEventsList(e.target.value)}
                placeholder="List events chronologically:&#10;- January 5: First incident of verbal abuse&#10;- February 12: Child refused to go with father&#10;- March 1: Filed for custody modification..."
                rows={12}
                className="w-full px-4 py-3 border rounded-lg focus:outline-none focus:ring-2 focus:ring-pink-500"
              />
              <Button
                onClick={handleGenerate}
                disabled={loading || !eventsList.trim()}
                className="w-full h-14 text-lg bg-gradient-to-r from-pink-600 to-rose-600"
              >
                {loading ? <><Loader2 className="w-5 h-5 mr-2 animate-spin" />Generating...</> :
                <><Clock className="w-5 h-5 mr-2" />Generate Timeline</>}
              </Button>
            </CardContent>
          </Card>
        ) : (
          <div className="space-y-6">
            <Card>
              <CardHeader><CardTitle>Case Timeline</CardTitle></CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {result.chronological_events?.map((event, idx) => (
                    <div key={idx} className="flex gap-4 items-start">
                      <div className="flex-shrink-0 w-24 text-sm text-gray-500">{event.date}</div>
                      <div className="flex-1 p-4 bg-gray-50 rounded-lg">
                        <p className="font-medium">{event.description}</p>
                        <Badge className="mt-2">{event.event_type}</Badge>
                      </div>
                    </div>
                  ))}
                </div>
                {result.court_narrative && (
                  <div className="mt-6 p-4 bg-blue-50 rounded-lg">
                    <h4 className="font-bold mb-2">Court Narrative:</h4>
                    <p className="text-gray-700">{result.court_narrative}</p>
                  </div>
                )}
              </CardContent>
            </Card>
            <Button onClick={() => setResult(null)} variant="outline" className="w-full">
              New Timeline
            </Button>
          </div>
        )}
      </div>
    </div>
  );
};

export default TimelineGenerator;
