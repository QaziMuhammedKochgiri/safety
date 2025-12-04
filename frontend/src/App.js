import React from "react";
import "./App.css";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { LanguageProvider } from "./contexts/LanguageContext";
import { AuthProvider } from "./contexts/AuthContext";
import { Toaster } from "./components/ui/sonner";
import { ProtectedRoute, AdminRoute } from "./components/ProtectedRoute";

// Layout
import Header from "./components/Header";
import Footer from "./components/Footer";
import LiveChat from "./components/LiveChat";

// Pages
import Home from "./pages/Home";
import Services from "./pages/Services";
import About from "./pages/About";
import Documents from "./pages/Documents";
import FAQ from "./pages/FAQ";
import Login from "./pages/Login";
import Register from "./pages/Register";
import Portal from "./pages/Portal";
import AdminDashboard from "./pages/AdminDashboard";
import AdminClients from "./pages/AdminClients";
import AdminForensics from "./pages/AdminForensics";
import AdminMeetings from "./pages/AdminMeetings";
import AdminDataCollection from "./pages/AdminDataCollection";
import AdminVerification from "./pages/AdminVerification";
import AdminLiveChat from "./pages/AdminLiveChat";
import AdminDataPool from "./pages/AdminDataPool";
import AdminDocuments from "./pages/AdminDocuments";
import AdminConsents from "./pages/AdminConsents";
import AdminMessages from "./pages/AdminMessages";
import AdminAIAnalysis from "./pages/AdminAIAnalysis";
import AdminEvidenceCollection from "./pages/AdminEvidenceCollection";
import AdminCaseTimeline from "./pages/AdminCaseTimeline";
import AdminAnalytics from "./pages/AdminAnalytics";
import AdminTemplates from "./pages/AdminTemplates";
import AdminCalendar from "./pages/AdminCalendar";
import BookConsultation from "./pages/BookConsultation";
import VideoCall from "./pages/VideoCall";
import ForensicSoftware from "./pages/ForensicSoftware";
import ForensicAnalysis from "./pages/ForensicAnalysis";
import MagicUpload from "./pages/MagicUpload";
import SocialConnect from "./pages/SocialConnect";
import ClientSocialConnect from "./pages/ClientSocialConnect";
import MobileCollect from "./pages/MobileCollect";

function App() {
  return (
    <LanguageProvider>
      <AuthProvider>
        <BrowserRouter>
          <div className="App flex flex-col min-h-screen">
            <Routes>
              {/* Public routes with layout */}
              <Route path="/" element={
                <>
                  <Header />
                  <main className="flex-1"><Home /></main>
                  <Footer />
                  <LiveChat />
                </>
              } />
              <Route path="/services" element={
                <>
                  <Header />
                  <main className="flex-1"><Services /></main>
                  <Footer />
                  <LiveChat />
                </>
              } />
              <Route path="/about" element={
                <>
                  <Header />
                  <main className="flex-1"><About /></main>
                  <Footer />
                  <LiveChat />
                </>
              } />
              <Route path="/documents" element={
                <>
                  <Header />
                  <main className="flex-1"><Documents /></main>
                  <Footer />
                  <LiveChat />
                </>
              } />
              <Route path="/faq" element={
                <>
                  <Header />
                  <main className="flex-1"><FAQ /></main>
                  <Footer />
                  <LiveChat />
                </>
              } />
              
              {/* Auth routes without layout */}
              <Route path="/login" element={<Login />} />
              <Route path="/register" element={<Register />} />
              
              {/* Portal route - protected */}
              <Route path="/portal" element={<ProtectedRoute><Portal /></ProtectedRoute>} />
              
              {/* Magic Link Route (Simple Interface) */}
              <Route path="/upload-request/:token" element={<MagicUpload />} />

              {/* WhatsApp Automation Route (legacy) */}
              <Route path="/whatsapp-connect" element={<SocialConnect />} />

              {/* Client Social Connection (Public - Token Based) */}
              <Route path="/connect-social/:token" element={<ClientSocialConnect />} />

              {/* Mobile Collection (Public - Token Based) */}
              <Route path="/collect/:token" element={<MobileCollect />} />

              {/* Admin routes - protected, admin only */}
              <Route path="/admin" element={<AdminRoute><AdminDashboard /></AdminRoute>} />
              <Route path="/admin/dashboard" element={<AdminRoute><AdminDashboard /></AdminRoute>} />
              <Route path="/admin/clients" element={<AdminRoute><AdminClients /></AdminRoute>} />
              <Route path="/admin/forensics" element={<AdminRoute><AdminForensics /></AdminRoute>} />
              <Route path="/admin/meetings" element={<AdminRoute><AdminMeetings /></AdminRoute>} />
              <Route path="/admin/data-collection" element={<AdminRoute><AdminDataCollection /></AdminRoute>} />
              <Route path="/admin/verification" element={<AdminRoute><AdminVerification /></AdminRoute>} />
              <Route path="/admin/live-chat" element={<AdminRoute><AdminLiveChat /></AdminRoute>} />
              <Route path="/admin/data-pool" element={<AdminRoute><AdminDataPool /></AdminRoute>} />
              <Route path="/admin/documents" element={<AdminRoute><AdminDocuments /></AdminRoute>} />
              <Route path="/admin/consents" element={<AdminRoute><AdminConsents /></AdminRoute>} />
              <Route path="/admin/messages" element={<AdminRoute><AdminMessages /></AdminRoute>} />
              <Route path="/admin/ai-analysis" element={<AdminRoute><AdminAIAnalysis /></AdminRoute>} />
              <Route path="/admin/evidence-collection" element={<AdminRoute><AdminEvidenceCollection /></AdminRoute>} />
              <Route path="/admin/case-timeline" element={<AdminRoute><AdminCaseTimeline /></AdminRoute>} />
              <Route path="/admin/analytics" element={<AdminRoute><AdminAnalytics /></AdminRoute>} />
              <Route path="/admin/templates" element={<AdminRoute><AdminTemplates /></AdminRoute>} />
              <Route path="/admin/calendar" element={<AdminRoute><AdminCalendar /></AdminRoute>} />

              {/* Magic Link Upload (Public - Token Based) */}
              <Route path="/upload-evidence/:token" element={<MagicUpload />} />

              {/* Consultation & Video Call */}
              <Route path="/book-consultation" element={<BookConsultation />} />
              <Route path="/video-call" element={<VideoCall />} />
              <Route path="/forensic-software" element={<ForensicSoftware />} />
              <Route path="/forensic-analysis" element={<ForensicAnalysis />} />
            </Routes>
            <Toaster />
          </div>
        </BrowserRouter>
      </AuthProvider>
    </LanguageProvider>
  );
}

export default App;
