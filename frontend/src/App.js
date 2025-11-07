import React from "react";
import "./App.css";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { LanguageProvider } from "./contexts/LanguageContext";
import { AuthProvider } from "./contexts/AuthContext";
import { Toaster } from "./components/ui/sonner";

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
import BookConsultation from "./pages/BookConsultation";
import VideoCall from "./pages/VideoCall";
import ForensicSoftware from "./pages/ForensicSoftware";

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
              
              {/* Portal route without public layout */}
              <Route path="/portal" element={<Portal />} />
              
              {/* Admin routes */}
              <Route path="/admin" element={<AdminDashboard />} />
              <Route path="/admin/clients" element={<AdminClients />} />
              
              {/* Consultation & Video Call */}
              <Route path="/book-consultation" element={<BookConsultation />} />
              <Route path="/video-call" element={<VideoCall />} />
            </Routes>
            <Toaster />
          </div>
        </BrowserRouter>
      </AuthProvider>
    </LanguageProvider>
  );
}

export default App;
