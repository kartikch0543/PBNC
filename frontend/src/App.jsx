import React, { useState, useEffect } from 'react';
import Navbar from './components/Navbar';
import LoginPage from './pages/LoginPage';
import DashboardPage from './pages/DashboardPage';
import NewJobPage from './pages/NewJobPage';
import ProcessingScreen from './pages/ProcessingScreen';
import ResultsPage from './pages/ResultsPage';
import { authAPI, getAuthToken, clearAuthToken } from './services/api';

export default function App() {
  const [user, setUser] = useState(null);
  const [activeTab, setActiveTab] = useState('dashboard');
  const [loadingInitial, setLoadingInitial] = useState(true);
  const [activeJob, setActiveJob] = useState(null);
  const [activeDocument, setActiveDocument] = useState({ id: null, name: '' });

  useEffect(() => {
    const initAuth = async () => {
      const token = getAuthToken();
      if (token) {
        try {
          const profile = await authAPI.getMe();
          setUser(profile);
          setActiveTab('dashboard');
        } catch (err) {
          clearAuthToken();
          setUser(null);
          setActiveTab('login');
        }
      } else {
        setActiveTab('login');
      }
      setLoadingInitial(false);
    };

    initAuth();

    const handleAuthExpired = () => {
      setUser(null);
      setActiveTab('login');
    };

    window.addEventListener('docuq:auth_expired', handleAuthExpired);
    return () => window.removeEventListener('docuq:auth_expired', handleAuthExpired);
  }, []);

  const handleLogout = () => {
    clearAuthToken();
    setUser(null);
    setActiveTab('login');
  };

  const handleAuthSuccess = (authenticatedUser) => {
    setUser(authenticatedUser);
    setActiveTab('dashboard');
  };

  const handleJobCreated = (jobData) => {
    setActiveJob(jobData);
    setActiveDocument({ id: jobData.documentId, name: jobData.jobName });
    setActiveTab('processing');
  };

  const handleProcessingComplete = (docId, docName) => {
    setActiveDocument({ id: docId, name: docName });
    setActiveTab('results');
  };

  const handleSelectDocument = (docId, docName) => {
    setActiveDocument({ id: docId, name: docName });
    setActiveTab('results');
  };

  if (loadingInitial) {
    return (
      <div className="min-h-screen bg-[#090d16] flex items-center justify-center text-slate-400 text-xs font-semibold">
        <div className="flex items-center gap-2">
          <div className="w-2 h-2 rounded-full bg-blue-500 animate-ping"></div>
          <span>Loading DocuQ Intelligence Platform...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#090d16] text-[#f8fafc] flex flex-col">
      <Navbar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        user={user}
        onLogout={handleLogout}
      />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {!user || activeTab === 'login' ? (
          <LoginPage onAuthSuccess={handleAuthSuccess} />
        ) : activeTab === 'dashboard' ? (
          <DashboardPage
            onNavigateCreate={() => setActiveTab('new-job')}
            onSelectDocument={handleSelectDocument}
          />
        ) : activeTab === 'new-job' ? (
          <NewJobPage onJobCreated={handleJobCreated} />
        ) : activeTab === 'processing' && activeJob ? (
          <ProcessingScreen
            jobInfo={activeJob}
            onComplete={handleProcessingComplete}
          />
        ) : activeTab === 'results' && activeDocument.id ? (
          <ResultsPage
            documentId={activeDocument.id}
            documentName={activeDocument.name}
            onBack={() => setActiveTab('dashboard')}
          />
        ) : (
          <DashboardPage
            onNavigateCreate={() => setActiveTab('new-job')}
            onSelectDocument={handleSelectDocument}
          />
        )}
      </main>

      <footer className="border-t border-slate-900 bg-slate-950 py-4 px-6 text-center text-[11px] text-slate-500">
        DocuQ — Document Intelligence & Question Extraction SaaS • Pragati Bharati Candidate Submission
      </footer>
    </div>
  );
}
