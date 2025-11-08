import React from 'react';
import { Link } from 'react-router-dom';
import { useLanguage } from '../contexts/LanguageContext';
import { t } from '../translations';
import { mockStats } from '../mock';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Scale, Globe, Users, ArrowRight, Shield, FileText } from 'lucide-react';

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
            src="https://images.unsplash.com/photo-1758389298577-87fed4a80ed2"
            alt="Family silhouette"
            className="w-full h-full object-cover opacity-10"
          />
          <div className="absolute inset-0 bg-gradient-to-br from-blue-50/95 via-white/95 to-blue-50/95"></div>
        </div>

        <div className="container mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
          <div className="grid lg:grid-cols-2 gap-12 items-center">
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
                  src="https://images.unsplash.com/photo-1761628835064-32088526e123"
                  alt="Parent and child embrace"
                  className="relative rounded-2xl shadow-2xl w-full h-[500px] object-cover"
                />
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Stats Section */}
      <section className="py-16 bg-white border-y">
        <div className="container mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
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
            <p className="text-lg text-gray-600 max-w-3xl mx-auto">
              {language === 'de'
                ? 'Wir sind spezialisiert auf internationale Kindschaftsrecht in allen Mitgliedsstaaten des Haager Übereinkommens über die zivilrechtlichen Aspekte internationaler Kindesentführung.'
                : 'We specialize in international child custody law in all member states of the Hague Convention on the Civil Aspects of International Child Abduction.'}
            </p>
          </div>

          <div className="bg-white rounded-2xl shadow-xl p-8 md:p-12">
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4 text-sm">
              {[
                'Albania', 'Andorra', 'Argentina', 'Armenia', 'Australia', 'Austria', 
                'Azerbaijan', 'Bahamas', 'Belarus', 'Belgium', 'Belize', 'Bolivia',
                'Bosnia and Herzegovina', 'Brazil', 'Bulgaria', 'Burkina Faso', 'Canada', 'Chile',
                'China (Hong Kong & Macao)', 'Colombia', 'Costa Rica', 'Croatia', 'Cyprus', 'Czech Republic',
                'Denmark', 'Dominican Republic', 'Ecuador', 'El Salvador', 'Estonia', 'Fiji',
                'Finland', 'France', 'Gabon', 'Georgia', 'Germany', 'Greece',
                'Guatemala', 'Guyana', 'Honduras', 'Hungary', 'Iceland', 'India',
                'Ireland', 'Israel', 'Italy', 'Jamaica', 'Japan', 'Kazakhstan',
                'Latvia', 'Lesotho', 'Lithuania', 'Luxembourg', 'Malta', 'Mauritius',
                'Mexico', 'Monaco', 'Mongolia', 'Montenegro', 'Morocco', 'Netherlands',
                'New Zealand', 'Nicaragua', 'North Macedonia', 'Norway', 'Pakistan', 'Panama',
                'Paraguay', 'Peru', 'Philippines', 'Poland', 'Portugal', 'Republic of Korea',
                'Republic of Moldova', 'Romania', 'Russian Federation', 'San Marino', 'Serbia', 'Seychelles',
                'Singapore', 'Slovakia', 'Slovenia', 'South Africa', 'Spain', 'Sri Lanka',
                'Sweden', 'Switzerland', 'Thailand', 'Trinidad and Tobago', 'Turkey', 'Turkmenistan',
                'Ukraine', 'United Kingdom', 'United States', 'Uruguay', 'Uzbekistan', 'Venezuela',
                'Zimbabwe'
              ].map((country, index) => (
                <div 
                  key={index}
                  className="flex items-center space-x-2 p-3 bg-gradient-to-r from-blue-50 to-white rounded-lg border border-blue-100 hover:border-blue-300 hover:shadow-md transition-all"
                >
                  <div className="w-2 h-2 bg-blue-600 rounded-full flex-shrink-0"></div>
                  <span className="text-gray-700 font-medium">{country}</span>
                </div>
              ))}
            </div>

            <div className="mt-8 p-6 bg-blue-50 rounded-xl border-l-4 border-blue-600">
              <p className="text-sm text-gray-700">
                <strong className="text-blue-900">
                  {language === 'de' ? '📋 Hinweis:' : '📋 Note:'}
                </strong>{' '}
                {language === 'de'
                  ? 'Das Haager Übereinkommen von 1980 ist ein internationales Abkommen zum Schutz von Kindern vor den schädlichen Auswirkungen einer widerrechtlichen Entführung oder Zurückhaltung über internationale Grenzen hinweg.'
                  : 'The 1980 Hague Convention is an international treaty to protect children from the harmful effects of wrongful removal or retention across international borders.'}
              </p>
            </div>
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

          <div className="grid md:grid-cols-3 gap-8">
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
