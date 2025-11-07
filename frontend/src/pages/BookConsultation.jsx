import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { useLanguage } from '../contexts/LanguageContext';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { toast } from 'sonner';
import { Video, CreditCard, Calendar, CheckCircle } from 'lucide-react';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const BookConsultation = () => {
  const { language } = useLanguage();
  const { user, token } = useAuth();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);

  const handleBookConsultation = async () => {
    if (!user) {
      navigate('/login');
      return;
    }

    setLoading(true);
    try {
      const origin = window.location.origin;
      const response = await axios.post(
        `${API}/payment/create-checkout`,
        { origin_url: origin },
        { headers: { Authorization: `Bearer ${token}` } }
      );

      if (response.data.url) {
        window.location.href = response.data.url;
      }
    } catch (error) {
      toast.error(
        language === 'de' ? 'Fehler beim Erstellen der Buchung' : 'Failed to create booking',
        { description: error.response?.data?.detail || error.message }
      );
    } finally {
      setLoading(false);
    }
  };

  const handleStartFreeCall = () => {
    if (!user) {
      navigate('/login');
      return;
    }
    navigate(`/video-call?room=safechild-${user.clientNumber}`);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-blue-50 py-12">
      <div className="container mx-auto px-4">
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold text-gray-900 mb-4">
            {language === 'de' ? 'Beratung buchen' : 'Book Consultation'}
          </h1>
          <p className="text-xl text-gray-600">
            {language === 'de' 
              ? 'Wählen Sie Ihre bevorzugte Konsultationsoption' 
              : 'Choose your preferred consultation option'}
          </p>
        </div>

        <div className="grid md:grid-cols-2 gap-8 max-w-5xl mx-auto">
          <Card className="border-2 hover:border-green-500 hover:shadow-xl transition-all">
            <CardHeader className="text-center">
              <div className="w-20 h-20 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <Video className="w-10 h-10 text-green-600" />
              </div>
              <CardTitle className="text-2xl">
                {language === 'de' ? 'Kostenloser Video-Anruf' : 'Free Video Call'}
              </CardTitle>
              <CardDescription className="text-lg">
                {language === 'de' ? 'Schnelle Erstberatung' : 'Quick Initial Consultation'}
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4 mb-6">
                <div className="flex items-center space-x-3">
                  <CheckCircle className="w-5 h-5 text-green-600" />
                  <span>{language === 'de' ? '15 Minuten Beratung' : '15 minutes consultation'}</span>
                </div>
                <div className="flex items-center space-x-3">
                  <CheckCircle className="w-5 h-5 text-green-600" />
                  <span>{language === 'de' ? 'Sofort verfügbar' : 'Available immediately'}</span>
                </div>
                <div className="flex items-center space-x-3">
                  <CheckCircle className="w-5 h-5 text-green-600" />
                  <span>{language === 'de' ? 'Keine Zahlung erforderlich' : 'No payment required'}</span>
                </div>
              </div>
              <div className="text-center mb-4">
                <div className="text-4xl font-bold text-green-600">€0</div>
                <p className="text-sm text-gray-600">{language === 'de' ? 'Kostenlos' : 'Free'}</p>
              </div>
              <Button
                onClick={handleStartFreeCall}
                className="w-full bg-green-600 hover:bg-green-700 text-lg py-6"
              >
                <Video className="w-5 h-5 mr-2" />
                {language === 'de' ? 'Jetzt starten' : 'Start Now'}
              </Button>
            </CardContent>
          </Card>

          <Card className="border-2 border-blue-500 hover:shadow-xl transition-all relative">
            <div className="absolute top-0 right-0 bg-blue-600 text-white px-4 py-1 rounded-bl-lg text-sm font-medium">
              {language === 'de' ? 'Empfohlen' : 'Recommended'}
            </div>
            <CardHeader className="text-center">
              <div className="w-20 h-20 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <Calendar className="w-10 h-10 text-blue-600" />
              </div>
              <CardTitle className="text-2xl">
                {language === 'de' ? 'Ausführliche Beratung' : 'Comprehensive Consultation'}
              </CardTitle>
              <CardDescription className="text-lg">
                {language === 'de' ? 'Detaillierte rechtliche Analyse' : 'Detailed legal analysis'}
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4 mb-6">
                <div className="flex items-center space-x-3">
                  <CheckCircle className="w-5 h-5 text-blue-600" />
                  <span>{language === 'de' ? '60 Minuten Beratung' : '60 minutes consultation'}</span>
                </div>
                <div className="flex items-center space-x-3">
                  <CheckCircle className="w-5 h-5 text-blue-600" />
                  <span>{language === 'de' ? 'Fallanalyse & Strategie' : 'Case analysis & strategy'}</span>
                </div>
                <div className="flex items-center space-x-3">
                  <CheckCircle className="w-5 h-5 text-blue-600" />
                  <span>{language === 'de' ? 'Schriftlicher Bericht' : 'Written report'}</span>
                </div>
                <div className="flex items-center space-x-3">
                  <CheckCircle className="w-5 h-5 text-blue-600" />
                  <span>{language === 'de' ? 'Follow-up Support' : 'Follow-up support'}</span>
                </div>
              </div>
              <div className="text-center mb-4">
                <div className="text-4xl font-bold text-blue-600">€150</div>
                <p className="text-sm text-gray-600">{language === 'de' ? 'Einmalige Zahlung' : 'One-time payment'}</p>
              </div>
              <Button
                onClick={handleBookConsultation}
                disabled={loading}
                className="w-full bg-blue-600 hover:bg-blue-700 text-lg py-6"
              >
                <CreditCard className="w-5 h-5 mr-2" />
                {loading 
                  ? (language === 'de' ? 'Lädt...' : 'Loading...') 
                  : (language === 'de' ? 'Jetzt buchen' : 'Book Now')}
              </Button>
            </CardContent>
          </Card>
        </div>

        <Card className="mt-12 max-w-3xl mx-auto border-2">
          <CardContent className="p-8">
            <h3 className="text-xl font-bold mb-4">
              {language === 'de' ? 'Wie funktioniert es?' : 'How does it work?'}
            </h3>
            <div className="space-y-4">
              <div className="flex items-start space-x-3">
                <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center flex-shrink-0">
                  <span className="font-bold text-blue-600">1</span>
                </div>
                <div>
                  <p className="font-medium">
                    {language === 'de' ? 'Option wählen' : 'Choose option'}
                  </p>
                  <p className="text-sm text-gray-600">
                    {language === 'de' 
                      ? 'Wählen Sie zwischen kostenlosem Anruf oder ausführlicher Beratung'
                      : 'Choose between free call or comprehensive consultation'}
                  </p>
                </div>
              </div>
              <div className="flex items-start space-x-3">
                <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center flex-shrink-0">
                  <span className="font-bold text-blue-600">2</span>
                </div>
                <div>
                  <p className="font-medium">
                    {language === 'de' ? 'Zahlung (falls zutreffend)' : 'Payment (if applicable)'}
                  </p>
                  <p className="text-sm text-gray-600">
                    {language === 'de' 
                      ? 'Sichere Zahlung über Stripe für bezahlte Beratungen'
                      : 'Secure payment via Stripe for paid consultations'}
                  </p>
                </div>
              </div>
              <div className="flex items-start space-x-3">
                <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center flex-shrink-0">
                  <span className="font-bold text-blue-600">3</span>
                </div>
                <div>
                  <p className="font-medium">
                    {language === 'de' ? 'Video-Konsultation' : 'Video consultation'}
                  </p>
                  <p className="text-sm text-gray-600">
                    {language === 'de' 
                      ? 'Treffen Sie unsere Experten per Video-Anruf'
                      : 'Meet our experts via video call'}
                  </p>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default BookConsultation;
