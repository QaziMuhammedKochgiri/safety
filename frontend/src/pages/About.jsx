import React, { useState, useEffect } from 'react';
import { useLanguage } from '../contexts/LanguageContext';
import { t } from '../translations';
import { mockLawyers } from '../mock';
import { Card, CardContent } from '../components/ui/card';
import { GraduationCap, Briefcase, Award, Calendar, MapPin } from 'lucide-react';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const About = () => {
  const { language } = useLanguage();
  const [landmarkCases, setLandmarkCases] = useState([]);

  useEffect(() => {
    const fetchLandmarkCases = async () => {
      try {
        const response = await axios.get(`${API}/cases/landmark`);
        setLandmarkCases(response.data.cases || []);
      } catch (error) {
        console.error('Error fetching landmark cases:', error);
      }
    };
    fetchLandmarkCases();
  }, []);

  return (
    <div className="min-h-screen bg-gray-50 py-20">
      <div className="container mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="text-center mb-16">
          <h1 className="text-4xl md:text-5xl font-bold text-gray-900 mb-4">
            {t(language, 'aboutTitle')}
          </h1>
          <p className="text-xl text-gray-600 max-w-3xl mx-auto">
            {t(language, 'aboutSubtitle')}
          </p>
        </div>

        {/* Description */}
        <div className="max-w-4xl mx-auto mb-20">
          <Card className="border-2">
            <CardContent className="p-8">
              <p className="text-lg text-gray-700 leading-relaxed">
                {t(language, 'aboutDescription')}
              </p>
              <div className="mt-8 grid md:grid-cols-3 gap-6">
                <div className="text-center p-6 bg-blue-50 rounded-lg">
                  <div className="text-3xl font-bold text-blue-600 mb-2">8</div>
                  <div className="text-sm text-gray-700">
                    {language === 'de' ? 'Spezialisierte Anwälte' : 'Specialized Lawyers'}
                  </div>
                </div>
                <div className="text-center p-6 bg-blue-50 rounded-lg">
                  <div className="text-3xl font-bold text-blue-600 mb-2">PhD</div>
                  <div className="text-sm text-gray-700">
                    {language === 'de' ? 'Mindestqualifikation' : 'Minimum Qualification'}
                  </div>
                </div>
                <div className="text-center p-6 bg-blue-50 rounded-lg">
                  <div className="text-3xl font-bold text-blue-600 mb-2">35+</div>
                  <div className="text-sm text-gray-700">
                    {language === 'de' ? 'Länder Weltweit' : 'Countries Worldwide'}
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Team Section */}
        <div className="mb-12">
          <h2 className="text-3xl md:text-4xl font-bold text-center text-gray-900 mb-12">
            {t(language, 'teamTitle')}
          </h2>

          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8">
            {mockLawyers.map((lawyer) => (
              <Card key={lawyer.id} className="overflow-hidden hover:shadow-xl transition-all duration-300 border-2 hover:border-blue-500">
                <div className="aspect-square overflow-hidden">
                  <img
                    src={lawyer.image}
                    alt={lawyer.name}
                    className="w-full h-full object-cover hover:scale-110 transition-transform duration-300"
                  />
                </div>
                <CardContent className="p-6">
                  <h3 className="text-xl font-bold text-gray-900 mb-1">
                    {lawyer.name}
                  </h3>
                  <div className="text-sm text-blue-600 font-semibold mb-4">
                    {lawyer.specialization[language]}
                  </div>
                  <div className="space-y-3">
                    <div className="flex items-start space-x-2">
                      <GraduationCap className="w-5 h-5 text-gray-400 mt-0.5 flex-shrink-0" />
                      <span className="text-sm text-gray-600">
                        {lawyer.education[language]}
                      </span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <Briefcase className="w-5 h-5 text-gray-400 flex-shrink-0" />
                      <span className="text-sm text-gray-600">
                        {lawyer.experience[language]}
                      </span>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>

        {/* Landmark Cases Section */}
        {landmarkCases.length > 0 && (
          <div className="mt-20">
            <h2 className="text-3xl font-bold text-center text-gray-900 mb-4">
              {language === 'de' ? 'Erfolgreiche Präzedenzfälle' : 'Landmark Success Cases'}
            </h2>
            <p className="text-center text-gray-600 mb-12 max-w-3xl mx-auto">
              {language === 'de'
                ? 'Internationale Fälle, die Geschichte geschrieben haben und die Rechte von Eltern weltweit gestärkt haben.'
                : 'International cases that made history and strengthened parental rights worldwide.'}
            </p>

            <div className="grid md:grid-cols-3 gap-8">
              {landmarkCases.map((case_) => (
                <Card key={case_.caseNumber} className="border-2 hover:border-blue-500 hover:shadow-xl transition-all duration-300">
                  <CardContent className="p-6">
                    <div className="flex items-center space-x-2 text-blue-600 mb-4">
                      <Award className="w-5 h-5" />
                      <span className="font-semibold">{case_.outcome[language]}</span>
                    </div>
                    
                    <h3 className="text-xl font-bold text-gray-900 mb-3">
                      {case_.title[language]}
                    </h3>
                    
                    <div className="space-y-2 mb-4">
                      <div className="flex items-center space-x-2 text-sm text-gray-600">
                        <Calendar className="w-4 h-4" />
                        <span>{case_.year}</span>
                      </div>
                      <div className="flex items-center space-x-2 text-sm text-gray-600">
                        <MapPin className="w-4 h-4" />
                        <span>{case_.countries[language]}</span>
                      </div>
                    </div>
                    
                    <p className="text-gray-700 text-sm leading-relaxed mb-4">
                      {case_.description[language]}
                    </p>
                    
                    <div className="bg-blue-50 rounded-lg p-4 mt-4">
                      <p className="text-xs font-semibold text-blue-900 mb-2">
                        {language === 'de' ? 'Rechtlicher Grundsatz:' : 'Legal Principle:'}
                      </p>
                      <p className="text-xs text-blue-800 leading-relaxed">
                        {case_.legalPrinciple[language]}
                      </p>
                    </div>
                    
                    {case_.documentNumber && case_.pdfAvailable && (
                      <button
                        onClick={async () => {
                          try {
                            const response = await axios.get(`${API}/documents/${case_.documentNumber}/download`, {
                              responseType: 'blob',
                            });
                            const url = window.URL.createObjectURL(new Blob([response.data]));
                            const link = document.createElement('a');
                            link.href = url;
                            link.setAttribute('download', `${case_.caseNumber}.pdf`);
                            document.body.appendChild(link);
                            link.click();
                            link.remove();
                            window.URL.revokeObjectURL(url);
                          } catch (error) {
                            console.error('Download error:', error);
                          }
                        }}
                        className="mt-4 w-full bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-4 rounded-lg flex items-center justify-center space-x-2 transition-colors"
                      >
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                        </svg>
                        <span>
                          {language === 'de' ? 'Gerichtsentscheidung herunterladen (PDF)' : 'Download Court Decision (PDF)'}
                        </span>
                      </button>
                    )}
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>
        )}

        {/* Values Section */}
        <div className="mt-20 bg-gradient-to-br from-blue-50 to-white rounded-2xl p-12">
          <h2 className="text-3xl font-bold text-center text-gray-900 mb-12">
            {language === 'de' ? 'Unsere Werte' : 'Our Values'}
          </h2>
          <div className="grid md:grid-cols-3 gap-8">
            <div className="text-center">
              <div className="w-16 h-16 bg-blue-600 rounded-full flex items-center justify-center mx-auto mb-4">
                <span className="text-2xl font-bold text-white">1</span>
              </div>
              <h3 className="text-xl font-bold text-gray-900 mb-2">
                {language === 'de' ? 'Kinderwohl zuerst' : 'Children First'}
              </h3>
              <p className="text-gray-600">
                {language === 'de'
                  ? 'Das Wohl und die Rechte der Kinder stehen im Mittelpunkt unserer Arbeit.'
                  : 'The wellbeing and rights of children are at the heart of our work.'}
              </p>
            </div>
            <div className="text-center">
              <div className="w-16 h-16 bg-blue-600 rounded-full flex items-center justify-center mx-auto mb-4">
                <span className="text-2xl font-bold text-white">2</span>
              </div>
              <h3 className="text-xl font-bold text-gray-900 mb-2">
                {language === 'de' ? 'Expertise' : 'Expertise'}
              </h3>
              <p className="text-gray-600">
                {language === 'de'
                  ? 'Hochqualifizierte Anwälte mit akademischer Exzellenz und praktischer Erfahrung.'
                  : 'Highly qualified lawyers with academic excellence and practical experience.'}
              </p>
            </div>
            <div className="text-center">
              <div className="w-16 h-16 bg-blue-600 rounded-full flex items-center justify-center mx-auto mb-4">
                <span className="text-2xl font-bold text-white">3</span>
              </div>
              <h3 className="text-xl font-bold text-gray-900 mb-2">
                {language === 'de' ? 'Transparenz' : 'Transparency'}
              </h3>
              <p className="text-gray-600">
                {language === 'de'
                  ? 'Klare Kommunikation und vollständige Transparenz in allen Prozessen.'
                  : 'Clear communication and complete transparency in all processes.'}
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default About;
