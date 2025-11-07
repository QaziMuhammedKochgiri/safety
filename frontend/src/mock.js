export const mockLawyers = [
  {
    id: 1,
    name: 'Dr. jur. Anna Müller',
    title: 'Dr. jur.',
    specialization: { de: 'Haager Übereinkommen', en: 'Hague Convention' },
    education: { de: 'Promotion in Internationalem Familienrecht, Universität Amsterdam', en: 'PhD in International Family Law, University of Amsterdam' },
    experience: { de: '15 Jahre Erfahrung', en: '15 years experience' },
    image: 'https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?w=400&h=400&fit=crop'
  },
  {
    id: 2,
    name: 'Dr. jur. Michael Schmidt',
    title: 'Dr. jur.',
    specialization: { de: 'Internationale Kindesentführung', en: 'International Child Abduction' },
    education: { de: 'Promotion in Völkerrecht, Universität Heidelberg', en: 'PhD in International Law, University of Heidelberg' },
    experience: { de: '12 Jahre Erfahrung', en: '12 years experience' },
    image: 'https://images.unsplash.com/photo-1560250097-0b93528c311a?w=400&h=400&fit=crop'
  },
  {
    id: 3,
    name: 'Dr. jur. Sarah van der Berg',
    title: 'Dr. jur.',
    specialization: { de: 'Sorgerechtsberatung', en: 'Custody Rights Consultation' },
    education: { de: 'Promotion in Familienrecht, Universität Leiden', en: 'PhD in Family Law, Leiden University' },
    experience: { de: '10 Jahre Erfahrung', en: '10 years experience' },
    image: 'https://images.unsplash.com/photo-1551836022-d5d88e9218df?w=400&h=400&fit=crop'
  },
  {
    id: 4,
    name: 'Dr. jur. Thomas Weber',
    title: 'Dr. jur.',
    specialization: { de: 'EU-Familienrecht', en: 'EU Family Law' },
    education: { de: 'Promotion in Europäischem Recht, Universität München', en: 'PhD in European Law, University of Munich' },
    experience: { de: '14 Jahre Erfahrung', en: '14 years experience' },
    image: 'https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=400&h=400&fit=crop'
  },
  {
    id: 5,
    name: 'Dr. jur. Laura Hoffmann',
    title: 'Dr. jur.',
    specialization: { de: 'Grenzüberschreitende Streitigkeiten', en: 'Cross-Border Disputes' },
    education: { de: 'Promotion in Zivilprozessrecht, Universität Wien', en: 'PhD in Civil Procedure, University of Vienna' },
    experience: { de: '11 Jahre Erfahrung', en: '11 years experience' },
    image: 'https://images.unsplash.com/photo-1594744803329-e58b31de8bf5?w=400&h=400&fit=crop'
  },
  {
    id: 6,
    name: 'Dr. jur. Robert Klein',
    title: 'Dr. jur.',
    specialization: { de: 'Internationales Privatrecht', en: 'Private International Law' },
    education: { de: 'Promotion in Internationalem Privatrecht, Universität Zürich', en: 'PhD in Private International Law, University of Zurich' },
    experience: { de: '13 Jahre Erfahrung', en: '13 years experience' },
    image: 'https://images.unsplash.com/photo-1519085360753-af0119f7cbe7?w=400&h=400&fit=crop'
  },
  {
    id: 7,
    name: 'Dr. jur. Emma de Vries',
    title: 'Dr. jur.',
    specialization: { de: 'Kinderrechte', en: 'Children\'s Rights' },
    education: { de: 'Promotion in Kinderrechten, Universität Utrecht', en: 'PhD in Children\'s Rights, Utrecht University' },
    experience: { de: '9 Jahre Erfahrung', en: '9 years experience' },
    image: 'https://images.unsplash.com/photo-1580489944761-15a19d654956?w=400&h=400&fit=crop'
  },
  {
    id: 8,
    name: 'Dr. jur. David Richter',
    title: 'Dr. jur.',
    specialization: { de: 'Mediation & Streitbeilegung', en: 'Mediation & Dispute Resolution' },
    education: { de: 'Promotion in Mediation, Universität Berlin', en: 'PhD in Mediation, University of Berlin' },
    experience: { de: '16 Jahre Erfahrung', en: '16 years experience' },
    image: 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=400&h=400&fit=crop'
  }
];

export const mockFAQs = [
  {
    id: 1,
    question: { 
      de: 'Was ist das Haager Übereinkommen?', 
      en: 'What is the Hague Convention?' 
    },
    answer: { 
      de: 'Das Haager Übereinkommen über die zivilrechtlichen Aspekte internationaler Kindesentführung ist ein multilateraler Vertrag, der den prompten Rückführung von Kindern regelt, die unrechtmäßig in einen anderen Vertragsstaat verbracht oder dort zurückgehalten wurden.',
      en: 'The Hague Convention on the Civil Aspects of International Child Abduction is a multilateral treaty that provides an expeditious method to return children who have been wrongfully removed or retained in a contracting state.'
    }
  },
  {
    id: 2,
    question: { 
      de: 'Wie lange dauert ein internationaler Sorgerechtsfall?', 
      en: 'How long does an international custody case take?' 
    },
    answer: { 
      de: 'Die Dauer variiert je nach Komplexität des Falls und den beteiligten Ländern. Im Durchschnitt dauert ein Fall zwischen 6 und 18 Monaten. Wir arbeiten daran, den Prozess so schnell wie möglich abzuschließen.',
      en: 'The duration varies depending on the complexity of the case and the countries involved. On average, a case takes between 6 and 18 months. We work to complete the process as quickly as possible.'
    }
  },
  {
    id: 3,
    question: { 
      de: 'Was sind meine Rechte als Elternteil?', 
      en: 'What are my rights as a parent?' 
    },
    answer: { 
      de: 'Als Elternteil haben Sie das Recht auf Kontakt zu Ihrem Kind, unabhängig davon, in welchem Land sich das Kind befindet. Unsere Anwälte helfen Ihnen, diese Rechte international durchzusetzen.',
      en: 'As a parent, you have the right to contact with your child, regardless of which country the child is in. Our lawyers help you enforce these rights internationally.'
    }
  },
  {
    id: 4,
    question: { 
      de: 'Welche Dokumente benötige ich?', 
      en: 'What documents do I need?' 
    },
    answer: { 
      de: 'Typischerweise benötigen Sie Geburtsurkunden, Sorgerechtsbeschlüsse, Reisedokumente und jegliche Kommunikation mit dem anderen Elternteil. Wir beraten Sie gerne im Detail während der Erstberatung.',
      en: 'Typically, you need birth certificates, custody orders, travel documents, and any communication with the other parent. We will advise you in detail during the initial consultation.'
    }
  },
  {
    id: 5,
    question: { 
      de: 'Was kostet eine rechtliche Vertretung?', 
      en: 'How much does legal representation cost?' 
    },
    answer: { 
      de: 'Die Kosten variieren je nach Komplexität des Falls. Wir bieten eine kostenlose Erstberatung an und erstellen dann einen transparenten Kostenvoranschlag für Ihren spezifischen Fall.',
      en: 'Costs vary depending on the complexity of the case. We offer a free initial consultation and then provide a transparent cost estimate for your specific case.'
    }
  }
];

export const mockStats = {
  cases: '250+',
  lawyers: '8',
  countries: '35+',
  experience: '15+'
};

// Mock client numbers for testing
export const mockClientNumbers = ['SC2025001', 'SC2025002', 'SC2025003'];

// Mock file numbers for testing
export const mockFileNumbers = ['DOC2025001', 'DOC2025002', 'DOC2025003'];

// Real landmark cases data
export const mockLandmarkCases = [
  {
    id: 1,
    caseNumber: 'SC2020-MONASKY',
    title: { 
      de: 'Monasky v. Taglieri (2020) - U.S. Supreme Court', 
      en: 'Monasky v. Taglieri (2020) - U.S. Supreme Court' 
    },
    year: 2020,
    countries: { de: 'USA - Italien', en: 'USA - Italy' },
    outcome: { de: 'Erfolgreich', en: 'Successful' },
    description: {
      de: 'Wegweisender Fall des U.S. Supreme Court zur Bestimmung des "gewöhnlichen Aufenthalts" eines Kindes. Das Gericht entschied, dass der gewöhnliche Aufenthalt anhand der Gesamtheit der Umstände bestimmt wird, nicht nur aufgrund der elterlichen Absicht.',
      en: 'Landmark U.S. Supreme Court case clarifying determination of a child\'s "habitual residence." The Court held that habitual residence is determined by the totality of circumstances, not by parental intent alone.'
    },
    facts: {
      de: 'Amerikanische Mutter und italienischer Vater lebten in Italien. Nach Beziehungsende kehrte die Mutter mit dem Säugling in die USA zurück. Vater beantragte Rückführung nach Italien gemäß Haager Übereinkommen.',
      en: 'American mother and Italian father lived together in Italy. After relationship deteriorated, mother returned to U.S. with infant. Father filed Hague Convention petition seeking child\'s return to Italy.'
    },
    legalPrinciple: {
      de: 'Der gewöhnliche Aufenthalt wird durch die Gesamtheit der Umstände bestimmt, einschließlich der tatsächlichen Lebensumstände, der Verbindungen des Kindes zum Land und der Dauer des Aufenthalts.',
      en: 'Habitual residence is determined by totality of circumstances, including actual living arrangements, child\'s connections to the country, and duration of stay.'
    },
    impact: {
      de: 'Führender Präzedenzfall in US-Gerichten zur Bestimmung des gewöhnlichen Aufenthalts. Erleichtert zurückgebliebenen Eltern die Rückführung ihrer Kinder.',
      en: 'Leading precedent in U.S. courts for determining habitual residence. Makes it easier for left-behind parents to seek return of children.'
    }
  },
  {
    id: 2,
    caseNumber: 'SC2023-WINSTON',
    title: { 
      de: 'Winston & Strawn - Mexiko Rückführungsfall (2023)', 
      en: 'Winston & Strawn - Mexico Return Case (2023)' 
    },
    year: 2023,
    countries: { de: 'USA - Mexiko', en: 'USA - Mexico' },
    outcome: { de: 'Erfolgreich', en: 'Successful' },
    description: {
      de: 'Präzedenzfall zur Rückführung eines aus Mexiko in die USA entführten Kindes. Das Gericht wies die "gut integriert"-Verteidigung der Mutter zurück und ordnete die Rückführung an.',
      en: 'Precedent-setting case for return of child abducted from Mexico to U.S. Court rejected mother\'s "well-settled" defense and ordered child\'s return.'
    },
    facts: {
      de: 'Kind war gewöhnlich in Mexiko ansässig, wo Eltern gemeinsames Sorgerecht hatten. Mutter behielt Kind nach Besuch unrechtmäßig in den USA und beantragte Asyl.',
      en: 'Child was habitually resident in Mexico where parents shared custody. Mother wrongfully retained child in U.S. after visit and claimed asylum.'
    },
    legalPrinciple: {
      de: 'Die Verbindungen des Kindes zum Land des gewöhnlichen Aufenthalts (Familie, Schule, Gemeinschaft) überwiegen die kurze Zeit in einem neuen Land bei der Beurteilung der Integration.',
      en: 'Child\'s connections to country of habitual residence (family, school, community) outweigh short time in new country when evaluating "well-settled" defense.'
    },
    impact: {
      de: 'Erschwert entführenden Eltern die Vermeidung der Rückführung durch kurzfristige Integration. Betont die Wichtigkeit schnellen Handelns.',
      en: 'Makes it harder for abducting parents to avoid return based on short-term integration. Emphasizes importance of prompt action.'
    }
  },
  {
    id: 3,
    caseNumber: 'SC2021-URGENT',
    title: { 
      de: 'Dringende Schutzmaßnahmen - Deutschland/Niederlande (2021)', 
      en: 'Emergency Protection Measures - Germany/Netherlands (2021)' 
    },
    year: 2021,
    countries: { de: 'Deutschland - Niederlande', en: 'Germany - Netherlands' },
    outcome: { de: 'Erfolgreich', en: 'Successful' },
    description: {
      de: 'Fall demonstriert erfolgreiche Koordination zwischen deutschen und niederländischen Behörden zur Sicherstellung der Kinderrückführung innerhalb von 6 Wochen.',
      en: 'Case demonstrates successful coordination between German and Dutch authorities to secure child\'s return within 6 weeks.'
    },
    facts: {
      de: 'Deutscher Vater suchte Rückführung seiner 4-jährigen Tochter aus den Niederlanden. Mutter hatte das Kind nach einem vereinbarten Besuch nicht zurückgebracht.',
      en: 'German father sought return of 4-year-old daughter from Netherlands. Mother failed to return child after agreed visit.'
    },
    legalPrinciple: {
      de: 'Schnelle gerichtliche Entscheidungen und internationale Zusammenarbeit sind entscheidend für erfolgreiche Rückführungen gemäß Haager Übereinkommen.',
      en: 'Swift court decisions and international cooperation are critical for successful returns under Hague Convention.'
    },
    impact: {
      de: 'Zeigt die Effektivität der EU-weiten Zusammenarbeit bei Kindesentführungsfällen und die Bedeutung forensischer Beweise.',
      en: 'Shows effectiveness of EU-wide cooperation in child abduction cases and importance of forensic evidence.'
    }
  }
];
