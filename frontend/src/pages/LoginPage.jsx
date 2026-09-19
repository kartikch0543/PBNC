import React, { useState } from 'react';
import { authAPI, setAuthToken } from '../services/api';
import { LogIn, UserPlus, Lock, Mail, ShieldCheck } from 'lucide-react';

export default function LoginPage({ onAuthSuccess }) {
  const [mode, setMode] = useState('login'); // 'login' | 'register'
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setErrorMsg('');
    setLoading(true);

    try {
      if (mode === 'register') {
        await authAPI.register(email, password);
      }
      const data = await authAPI.login(email, password);
      setAuthToken(data.access_token);
      const user = await authAPI.getMe();
      onAuthSuccess(user);
    } catch (err) {
      const msg = err.response?.data?.detail || err.response?.data?.error?.message || 'Authentication failed';
      setErrorMsg(typeof msg === 'string' ? msg : JSON.stringify(msg));
    } finally {
      setLoading(false);
    }
  };

  const autofillDemo = () => {
    setEmail('evaluator@pragatibharati.org');
    setPassword('evaluator123');
  };

  return (
    <div className="max-w-md mx-auto my-12 p-6 bg-slate-900 border border-slate-800 rounded-2xl shadow-xl shadow-black/40">
      <div className="text-center mb-6">
        <div className="inline-flex p-3 rounded-2xl bg-blue-600/10 border border-blue-500/20 text-blue-400 mb-3">
          <ShieldCheck className="w-8 h-8" />
        </div>
        <h2 className="text-xl font-bold text-white">Reviewer Authentication</h2>
        <p className="text-xs text-slate-400 mt-1">Sign in to access document ingestion and reviewer workbench</p>
      </div>

      {/* Tabs */}
      <div className="flex bg-slate-950 p-1 rounded-lg border border-slate-800 mb-6">
        <button
          type="button"
          onClick={() => { setMode('login'); setErrorMsg(''); }}
          className={`flex-1 py-1.5 text-xs font-semibold rounded-md transition ${
            mode === 'login' ? 'bg-slate-800 text-white shadow' : 'text-slate-400 hover:text-white'
          }`}
        >
          Sign In
        </button>
        <button
          type="button"
          onClick={() => { setMode('register'); setErrorMsg(''); }}
          className={`flex-1 py-1.5 text-xs font-semibold rounded-md transition ${
            mode === 'register' ? 'bg-slate-800 text-white shadow' : 'text-slate-400 hover:text-white'
          }`}
        >
          Create Account
        </button>
      </div>

      {errorMsg && (
        <div className="mb-4 p-3 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400 text-xs font-medium">
          {errorMsg}
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-xs font-semibold text-slate-300 mb-1.5">Email Address</label>
          <div className="relative">
            <Mail className="w-4 h-4 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="evaluator@pragatibharati.org"
              required
              className="w-full pl-9 pr-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-white placeholder-slate-500 focus:outline-none focus:border-blue-500 transition"
            />
          </div>
        </div>

        <div>
          <label className="block text-xs font-semibold text-slate-300 mb-1.5">Password</label>
          <div className="relative">
            <Lock className="w-4 h-4 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              minLength={8}
              required
              className="w-full pl-9 pr-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-white placeholder-slate-500 focus:outline-none focus:border-blue-500 transition"
            />
          </div>
        </div>

        <button
          type="submit"
          disabled={loading}
          className="w-full py-2.5 px-4 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white font-semibold text-xs rounded-lg shadow-lg shadow-blue-500/20 disabled:opacity-50 transition flex items-center justify-center gap-2"
        >
          {loading ? (
            <span>Authenticating...</span>
          ) : mode === 'login' ? (
            <>
              <LogIn className="w-4 h-4" />
              <span>Sign In to DocuQ</span>
            </>
          ) : (
            <>
              <UserPlus className="w-4 h-4" />
              <span>Create Reviewer Account</span>
            </>
          )}
        </button>
      </form>

      <div className="mt-6 pt-4 border-t border-slate-800 text-center">
        <button
          type="button"
          onClick={autofillDemo}
          className="text-xs text-cyan-400 hover:text-cyan-300 font-medium underline transition"
        >
          ⚡ Quick Auto-Fill Demo Reviewer Credentials
        </button>
      </div>
    </div>
  );
}
