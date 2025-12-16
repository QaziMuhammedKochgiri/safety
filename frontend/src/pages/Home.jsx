import React from 'react';
import { Link } from 'react-router-dom';
import { useLanguage } from '../contexts/LanguageContext';
import { t } from '../translations';
import { mockStats } from '../mock';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Scale, Globe, Users, ArrowRight, Shield, FileText, Brain, Fingerprint, Sparkles } from 'lucide-react';

const Home = () => {
  const { language } = useLanguage();

  const services = [
    {
      icon: Scale,
      title: t(language, 'service1Title'),
      description: t(language, 'service1Description'),
    },
    {
      icon: Globe,
      title: t(language, 'service2Title'),
      description: t(language, 'service2Description'),
    },
    {
      icon: Users,
      title: t(language, 'service3Title'),
      description: t(language, 'service3Description'),
    },
  ];

  return (
    <div className="min-h-screen">
      {/* Hero Section */}
      <section className="relative bg-gradient-to-br from-blue-50 via-white to-blue-50 py-20 lg:py-32 overflow-hidden">
        {/* Background Image with Overlay */}
        <div className="absolute inset-0 z-0">
          <img
            src="https://images.unsplash.com/photo-1536640712-4d4c36ff0e4e?w=1920&q=80"
            alt="Family silhouette"
            className="w-full h-full object-cover opacity-10"
          />
          <div className="absolute inset-0 bg-gradient-to-br from-blue-50/95 via-white/95 to-blue-50/95"></div>
        </div>

        <div className="container mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
            {/* Left Content */}
            <div>
              <div className="inline-flex items-center px-4 py-2 bg-blue-100 rounded-full mb-6">
                <Shield className="w-4 h-4 text-blue-600 mr-2" />
                <span className="text-sm font-medium text-blue-900">
                  {language === 'de' ? 'Internationale Experten' : 'International Experts'}
                </span>
              </div>
              
              <h1 className="text-4xl md:text-5xl lg:text-6xl font-bold text-gray-900 mb-6 leading-tight">
                {t(language, 'heroTitle')}
              </h1>
              
              <p className="text-xl md:text-2xl text-blue-600 font-semibold mb-6">
                {t(language, 'heroSubtitle')}
              </p>
              
              <p className="text-lg text-gray-600 mb-10">
                {t(language, 'heroDescription')}
              </p>
              
              <div className="flex flex-col sm:flex-row gap-4">
                <Link to="/book-consultation">
                  <Button size="lg" className="bg-blue-600 hover:bg-blue-700 text-lg px-8 shadow-lg w-full sm:w-auto">
                    {t(language, 'heroButton')}
                    <ArrowRight className="ml-2 w-5 h-5" />
                  </Button>
                </Link>
                <a href="mailto:info@safechild.mom">
                  <Button size="lg" variant="outline" className="text-lg px-8 border-2 w-full sm:w-auto">
                    {t(language, 'heroButtonSecondary')}
                  </Button>
                </a>
              </div>
            </div>

            {/* Right Image */}
            <div className="hidden lg:block">
              <div className="relative">
                <div className="absolute -inset-4 bg-gradient-to-r from-blue-600 to-blue-400 rounded-2xl opacity-20 blur-2xl"></div>
                <img
                  src="https://images.unsplash.com/photo-1476703993599-0035a21b17a9?w=800&q=80"
                  alt="Parent and child embrace"
                  className="relative rounded-2xl shadow-2xl w-full h-[500px] object-cover"
                />
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Mobile Quick Access - AI & Forensics */}
      <section className="py-16 bg-gradient-to-br from-purple-50 via-blue-50 to-indigo-50">
        <div className="container mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-12">
            <div className="inline-flex items-center justify-center w-16 h-16 bg-gradient-to-br from-purple-500 to-blue-600 rounded-2xl mb-4 shadow-lg">
              <Sparkles className="w-8 h-8 text-white" />
            </div>
            <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-4">
              {language === 'de' ? 'Unsere Hauptdienste' : 'Our Main Services'}
            </h2>
            <p className="text-lg text-gray-600 max-w-2xl mx-auto">
              {language === 'de'
                ? 'Zugriff auf KI-gestützte Rechtsberatung und forensische Analyse'
                : 'Access AI-powered legal assistance and forensic analysis'}
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 max-w-4xl mx-auto">
            {/* AI Features Card */}
            <Link to="/dashboard">
              <Card className="border-2 border-purple-200 hover:border-purple-500 hover:shadow-2xl transition-all duration-300 group cursor-pointer overflow-hidden">
                <CardContent className="p-8">
                  <div className="flex flex-col items-center text-center space-y-4">
                    <div className="w-20 h-20 bg-gradient-to-br from-purple-500 to-pink-500 rounded-2xl flex items-center justify-center group-hover:scale-110 transition-transform duration-300 shadow-xl">
                      <Brain className="w-10 h-10 text-white" />
                    </div>
                    <div>
                      <h3 className="text-2xl font-bold text-gray-900 mb-2 group-hover:text-purple-600 transition-colors">
                        {language === 'de' ? '🤖 KI Features' : '🤖 AI Features'}
                      </h3>
                      <p className="text-gray-600 mb-4">
                        {language === 'de'
                          ? 'Lawyer AI, Risikoanalyse, Petition Generator, Übersetzer und mehr'
                          : 'Lawyer AI, Risk Analysis, Petition Generator, Translator and more'}
                      </p>
                      <div className="flex flex-wrap gap-2 justify-center text-xs">
                        <span className="px-3 py-1 bg-purple-100 text-purple-700 rounded-full">24/7 AI Chat</span>
                        <span className="px-3 py-1 bg-pink-100 text-pink-700 rounded-full">{language === 'de' ? 'Risiko' : 'Risk'}</span>
                        <span className="px-3 py-1 bg-blue-100 text-blue-700 rounded-full">{language === 'de' ? 'Dokumente' : 'Documents'}</span>
                        <span className="px-3 py-1 bg-indigo-100 text-indigo-700 rounded-full">{language === 'de' ? 'Übersetzer' : 'Translator'}</span>
                      </div>
                    </div>
                    <Button className="w-full bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600 text-white shadow-lg group-hover:shadow-xl transition-all">
                      {language === 'de' ? 'Zugriff auf KI Features' : 'Access AI Features'}
                      <ArrowRight className="ml-2 w-5 h-5 group-hover:translate-x-1 transition-transform" />
                    </Button>
                  </div>
                </CardContent>
              </Card>
            </Link>

            {/* Forensics Card */}
            <Link to="/forensic-analysis">
              <Card className="border-2 border-indigo-200 hover:border-indigo-500 hover:shadow-2xl transition-all duration-300 group cursor-pointer overflow-hidden">
                <CardContent className="p-8">
                  <div className="flex flex-col items-center text-center space-y-4">
                    <div className="w-20 h-20 bg-gradient-to-br from-indigo-500 to-blue-600 rounded-2xl flex items-center justify-center group-hover:scale-110 transition-transform duration-300 shadow-xl">
                      <Fingerprint className="w-10 h-10 text-white" />
                    </div>
                    <div>
                      <h3 className="text-2xl font-bold text-gray-900 mb-2 group-hover:text-indigo-600 transition-colors">
                        {language === 'de' ? '🔍 Forensik' : '🔍 Forensics'}
                      </h3>
                      <p className="text-gray-600 mb-4">
                        {language === 'de'
                          ? 'WhatsApp, Telegram, SMS Analyse, Beweissammlung, Timeline Erstellung'
                          : 'WhatsApp, Telegram, SMS Analysis, Evidence Collection, Timeline Creation'}
                      </p>
                      <div className="flex flex-wrap gap-2 justify-center text-xs">
                        <span className="px-3 py-1 bg-green-100 text-green-700 rounded-full">WhatsApp</span>
                        <span className="px-3 py-1 bg-blue-100 text-blue-700 rounded-full">Telegram</span>
                        <span className="px-3 py-1 bg-purple-100 text-purple-700 rounded-full">{language === 'de' ? 'Beweise' : 'Evidence'}</span>
                        <span className="px-3 py-1 bg-indigo-100 text-indigo-700 rounded-full">Timeline</span>
                      </div>
                    </div>
                    <Button className="w-full bg-gradient-to-r from-indigo-500 to-blue-600 hover:from-indigo-600 hover:to-blue-700 text-white shadow-lg group-hover:shadow-xl transition-all">
                      {language === 'de' ? 'Forensik starten' : 'Start Forensics'}
                      <ArrowRight className="ml-2 w-5 h-5 group-hover:translate-x-1 transition-transform" />
                    </Button>
                  </div>
                </CardContent>
              </Card>
            </Link>
          </div>

          {/* Additional Quick Links */}
          <div className="mt-12 flex flex-wrap justify-center gap-4">
            <Link to="/services">
              <Button variant="outline" className="border-2 hover:bg-blue-50">
                <Shield className="w-4 h-4 mr-2" />
                {language === 'de' ? 'Alle Dienste' : 'All Services'}
              </Button>
            </Link>
            <Link to="/documents">
              <Button variant="outline" className="border-2 hover:bg-blue-50">
                <FileText className="w-4 h-4 mr-2" />
                {language === 'de' ? 'Dokumente' : 'Documents'}
              </Button>
            </Link>
            <Link to="/faq">
              <Button variant="outline" className="border-2 hover:bg-blue-50">
                <Globe className="w-4 h-4 mr-2" />
                FAQ
              </Button>
            </Link>
          </div>
        </div>
      </section>

      {/* Services Section */}
      <section className="py-20 bg-gray-50">
        <div className="container mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-4">
              {t(language, 'servicesTitle')}
            </h2>
            <p className="text-lg text-gray-600 max-w-2xl mx-auto">
              {t(language, 'servicesSubtitle')}
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {services.map((service, index) => {
              const Icon = service.icon;
              return (
                <Card key={index} className="border-2 hover:border-blue-500 hover:shadow-xl transition-all duration-300 group overflow-hidden">
                  <CardHeader>
                    <div className="w-14 h-14 bg-gradient-to-br from-blue-500 to-blue-600 rounded-lg flex items-center justify-center mb-4 group-hover:scale-110 transition-transform duration-300 shadow-lg">
                      <Icon className="w-7 h-7 text-white" />
                    </div>
                    <CardTitle className="text-xl group-hover:text-blue-600 transition-colors">{service.title}</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <CardDescription className="text-base mb-4">
                      {service.description}
                    </CardDescription>
                    <Link to="/services" className="text-blue-600 hover:text-blue-700 font-medium inline-flex items-center group-hover:translate-x-1 transition-transform">
                      {t(language, 'learnMore')}
                      <ArrowRight className="ml-2 w-4 h-4" />
                    </Link>
                  </CardContent>
                </Card>
              );
            })}
          </div>
        </div>
      </section>

      {/* Stats Section */}
      <section className="py-16 bg-white border-y">
        <div className="container mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-8">
            <div className="text-center">
              <div className="text-4xl md:text-5xl font-bold text-blue-600 mb-2">
                {mockStats.cases}
              </div>
              <div className="text-sm md:text-base text-gray-600">
                {t(language, 'statsCases')}
              </div>
            </div>
            <div className="text-center">
              <div className="text-4xl md:text-5xl font-bold text-blue-600 mb-2">
                {mockStats.lawyers}
              </div>
              <div className="text-sm md:text-base text-gray-600">
                {t(language, 'statsLawyers')}
              </div>
            </div>
            <div className="text-center">
              <div className="text-4xl md:text-5xl font-bold text-blue-600 mb-2">
                {mockStats.countries}
              </div>
              <div className="text-sm md:text-base text-gray-600">
                {t(language, 'statsCountries')}
              </div>
            </div>
            <div className="text-center">
              <div className="text-4xl md:text-5xl font-bold text-blue-600 mb-2">
                {mockStats.experience}
              </div>
              <div className="text-sm md:text-base text-gray-600">
                {t(language, 'statsExperience')}
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Hague Convention Countries */}
      <section className="py-16 bg-gradient-to-br from-blue-50 to-white">
        <div className="container mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-12">
            <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-4">
              {language === 'de'
                ? 'Haager Übereinkommen - Vertragsstaaten'
                : 'Hague Convention - Member States'}
            </h2>
            <p className="text-lg text-gray-600 max-w-2xl mx-auto">
              {language === 'de'
                ? 'Wir vertreten Fälle in allen Vertragsstaaten des Haager Übereinkommens über die zivilrechtlichen Aspekte internationaler Kindesentführung'
                : 'We represent cases in all member states of the Hague Convention on the Civil Aspects of International Child Abduction'}
            </p>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4 max-w-6xl mx-auto">
            {[
              'Albania', 'Andorra', 'Argentina', 'Armenia', 'Australia',
              'Austria', 'Azerbaijan', 'Bahamas', 'Belarus', 'Belgium',
              'Belize', 'Bosnia and Herzegovina', 'Brazil', 'Bulgaria', 'Burkina Faso',
              'Canada', 'Chile', 'China (Hong Kong, Macau)', 'Colombia', 'Costa Rica',
              'Croatia', 'Cyprus', 'Czech Republic', 'Denmark', 'Dominican Republic',
              'Ecuador', 'El Salvador', 'Estonia', 'Fiji', 'Finland',
              'France', 'Georgia', 'Germany', 'Greece', 'Guatemala',
              'Honduras', 'Hungary', 'Iceland', 'Ireland', 'Israel',
              'Italy', 'Japan', 'Kazakhstan', 'Latvia', 'Lithuania',
              'Luxembourg', 'Malta', 'Mauritius', 'Mexico', 'Moldova',
              'Monaco', 'Montenegro', 'Morocco', 'Netherlands', 'New Zealand',
              'Nicaragua', 'North Macedonia', 'Norway', 'Panama', 'Paraguay',
              'Peru', 'Poland', 'Portugal', 'Romania', 'Russia',
              'San Marino', 'Serbia', 'Seychelles', 'Singapore', 'Slovakia',
              'Slovenia', 'South Africa', 'South Korea', 'Spain', 'Sri Lanka',
              'Sweden', 'Switzerland', 'Thailand', 'Trinidad and Tobago', 'Turkey',
              'Turkmenistan', 'Ukraine', 'United Kingdom', 'United States', 'Uruguay',
              'Uzbekistan', 'Venezuela', 'Vietnam', 'Zimbabwe'
            ].map((country, index) => (
              <div
                key={index}
                className="bg-white border border-gray-200 rounded-lg p-3 text-center hover:border-blue-500 hover:shadow-md transition-all duration-200 text-sm"
              >
                {country}
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="relative py-20 bg-gradient-to-r from-blue-600 to-blue-800 text-white overflow-hidden">
        {/* Background Pattern */}
        <div className="absolute inset-0 opacity-10">
          <img
            src="https://images.pexels.com/photos/51953/mother-daughter-love-sunset-51953.jpeg"
            alt="Hope and reunion"
            className="w-full h-full object-cover"
          />
        </div>
        <div className="container mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
          <div className="max-w-3xl mx-auto text-center">
            <div className="inline-flex items-center justify-center w-20 h-20 bg-white/20 backdrop-blur-sm rounded-full mb-6">
              <FileText className="w-10 h-10" />
            </div>
            <h2 className="text-3xl md:text-4xl font-bold mb-6">
              {language === 'de'
                ? 'Bereit, für Ihre Rechte zu kämpfen?'
                : 'Ready to Fight for Your Rights?'}
            </h2>
            <p className="text-lg mb-8 opacity-90">
              {language === 'de'
                ? 'Kontaktieren Sie uns heute für eine kostenlose Erstberatung. Unser Expertenteam steht bereit, Ihnen zu helfen.'
                : 'Contact us today for a free initial consultation. Our expert team is ready to help you.'}
            </p>
            <Link to="/book-consultation">
              <Button size="lg" className="bg-white text-blue-600 hover:bg-gray-100 text-lg px-8 shadow-xl hover:shadow-2xl transition-all">
                {t(language, 'heroButton')}
                <ArrowRight className="ml-2 w-5 h-5" />
              </Button>
            </Link>
          </div>
        </div>
      </section>
    </div>
  );
};

export default Home;
