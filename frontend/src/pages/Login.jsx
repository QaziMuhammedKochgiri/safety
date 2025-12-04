import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { useLanguage } from '../contexts/LanguageContext';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { toast } from 'sonner';
import { Lock, Mail, ArrowRight } from 'lucide-react';

const Login = () => {
  const { language } = useLanguage();
  const { login } = useAuth();
  const navigate = useNavigate();
  const [formData, setFormData] = useState({ email: '', password: '' });
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    const result = await login(formData.email, formData.password);

    if (result.success) {
      toast.success(
        language === 'de' ? 'Erfolgreich angemeldet' : 'Successfully logged in'
      );
      // Redirect based on role
      if (result.role === 'admin') {
        navigate('/admin');
      } else {
        navigate('/portal');
      }
    } else {
      toast.error(
        language === 'de' ? 'Anmeldung fehlgeschlagen' : 'Login failed',
        { description: result.error }
      );
    }
    
    setLoading(false);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-blue-50 flex items-center justify-center p-4 sm:p-6 md:p-8">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            {language === 'de' ? 'Kundenportal' : 'Client Portal'}
          </h1>
          <p className="text-gray-600">
            {language === 'de' ? 'Melden Sie sich an, um auf Ihre Dokumente zuzugreifen' : 'Sign in to access your documents'}
          </p>
        </div>

        <Card className="border-2">
          <CardHeader>
            <CardTitle className="text-2xl">
              {language === 'de' ? 'Anmelden' : 'Sign In'}
            </CardTitle>
            <CardDescription>
              {language === 'de' ? 'Geben Sie Ihre Anmeldedaten ein' : 'Enter your credentials'}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="email">
                  {language === 'de' ? 'E-Mail' : 'Email'}
                </Label>
                <div className="relative">
                  <Mail className="absolute left-3 top-3 w-5 h-5 text-gray-400" />
                  <Input
                    id="email"
                    type="email"
                    placeholder={language === 'de' ? 'ihre@email.de' : 'your@email.com'}
                    value={formData.email}
                    onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                    className="pl-10"
                    required
                  />
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="password">
                  {language === 'de' ? 'Passwort' : 'Password'}
                </Label>
                <div className="relative">
                  <Lock className="absolute left-3 top-3 w-5 h-5 text-gray-400" />
                  <Input
                    id="password"
                    type="password"
                    placeholder="••••••••"
                    value={formData.password}
                    onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                    className="pl-10"
                    required
                  />
                </div>
              </div>

              <Button
                type="submit"
                className="w-full bg-blue-600 hover:bg-blue-700"
                disabled={loading}
              >
                {loading ? (
                  language === 'de' ? 'Anmelden...' : 'Signing in...'
                ) : (
                  <>
                    {language === 'de' ? 'Anmelden' : 'Sign In'}
                    <ArrowRight className="ml-2 w-4 h-4" />
                  </>
                )}
              </Button>
            </form>

            <div className="mt-6 text-center">
              <p className="text-sm text-gray-600">
                {language === 'de' ? 'Noch kein Konto?' : "Don't have an account?"}{' '}
                <Link to="/register" className="text-blue-600 hover:text-blue-700 font-medium">
                  {language === 'de' ? 'Registrieren' : 'Register'}
                </Link>
              </p>
            </div>

            <div className="mt-4 text-center">
              <Link to="/" className="text-sm text-gray-600 hover:text-gray-900">
                ← {language === 'de' ? 'Zurück zur Startseite' : 'Back to homepage'}
              </Link>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default Login;
