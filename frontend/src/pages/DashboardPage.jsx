import React, { useEffect, useState } from 'react';
import { dashboardAPI } from '../services/api';
import { FileText, HelpCircle, AlertTriangle, XCircle, PlusCircle, ArrowRight, RefreshCw } from 'lucide-react';

export default function DashboardPage({ onNavigateCreate, onSelectDocument }) {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  const fetchStats = async () => {
    setLoading(true);
    try {
      const data = await dashboardAPI.getStats();
      setStats(data);
    } catch (err) {
      console.error('Failed to load dashboard stats:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStats();
  }, []);

  return (
    <div className="space-y-6">
      {/* Header & Quick Action */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-extrabold text-white tracking-tight">Intelligence Dashboard</h1>
          <p className="text-xs text-slate-400 mt-1">
            Real-time status of ingested examination papers, question extractions, and reviewer QA queue
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={fetchStats}
            title="Refresh statistics"
            className="p-2 rounded-lg bg-slate-900 border border-slate-800 text-slate-400 hover:text-white transition"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          </button>
          <button
            onClick={onNavigateCreate}
            className="inline-flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white text-xs font-bold rounded-lg shadow-lg shadow-blue-500/20 transition"
          >
            <PlusCircle className="w-4 h-4" />
            <span>Create Processing Job</span>
          </button>
        </div>
      </div>

      {/* 4 Metric KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Total Documents */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-sm">
          <div className="flex items-center justify-between mb-3">
            <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">Total Documents</span>
            <div className="p-2 rounded-lg bg-blue-500/10 text-blue-400 border border-blue-500/20">
              <FileText className="w-4 h-4" />
            </div>
          </div>
          <div className="text-3xl font-extrabold text-white">
            {stats ? stats.total_documents : '...'}
          </div>
          <p className="text-[11px] text-slate-500 mt-1">Ingested exam papers & answer keys</p>
        </div>

        {/* Total Questions */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-sm">
          <div className="flex items-center justify-between mb-3">
            <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">Total Questions</span>
            <div className="p-2 rounded-lg bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
              <HelpCircle className="w-4 h-4" />
            </div>
          </div>
          <div className="text-3xl font-extrabold text-white">
            {stats ? stats.total_questions : '...'}
          </div>
          <p className="text-[11px] text-slate-500 mt-1">Structured questions in PostgreSQL</p>
        </div>

        {/* Review Required */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-sm">
          <div className="flex items-center justify-between mb-3">
            <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">Review Required</span>
            <div className="p-2 rounded-lg bg-amber-500/10 text-amber-400 border border-amber-500/20">
              <AlertTriangle className="w-4 h-4" />
            </div>
          </div>
          <div className="text-3xl font-extrabold text-amber-400">
            {stats ? stats.review_required_count : '...'}
          </div>
          <p className="text-[11px] text-slate-500 mt-1">Low confidence or audit warnings</p>
        </div>

        {/* Failed Jobs */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-sm">
          <div className="flex items-center justify-between mb-3">
            <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">Failed Jobs</span>
            <div className="p-2 rounded-lg bg-red-500/10 text-red-400 border border-red-500/20">
              <XCircle className="w-4 h-4" />
            </div>
          </div>
          <div className="text-3xl font-extrabold text-slate-400">
            {stats ? stats.failed_jobs_count : '0'}
          </div>
          <p className="text-[11px] text-slate-500 mt-1">Extraction pipeline failures</p>
        </div>
      </div>

      {/* Recent Processing Jobs Section */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-sm">
        <div className="p-5 border-b border-slate-800 flex items-center justify-between">
          <div>
            <h2 className="text-base font-bold text-white">Recent Processing Jobs</h2>
            <p className="text-xs text-slate-400 mt-0.5">Asynchronous document pipeline ingestion log</p>
          </div>
          <button
            onClick={onNavigateCreate}
            className="text-xs text-blue-400 hover:text-blue-300 font-semibold flex items-center gap-1 transition"
          >
            <span>+ Upload New Paper</span>
          </button>
        </div>

        {stats?.recent_jobs && stats.recent_jobs.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-950 text-slate-400 border-b border-slate-800 uppercase font-bold text-[10px] tracking-wider">
                <tr>
                  <th className="py-3 px-4">Document / Job</th>
                  <th className="py-3 px-4">Type</th>
                  <th className="py-3 px-4">Status</th>
                  <th className="py-3 px-4">Questions</th>
                  <th className="py-3 px-4">Warnings</th>
                  <th className="py-3 px-4">Created</th>
                  <th className="py-3 px-4 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 text-slate-300">
                {stats.recent_jobs.map((job) => {
                  const isCompleted = job.processing_status === 'COMPLETED' || job.processing_status === 'COMPLETED_WITH_WARNINGS';
                  return (
                    <tr key={job.id} className="hover:bg-slate-800/30 transition">
                      <td className="py-3 px-4 font-semibold text-white flex items-center gap-2">
                        <FileText className="w-4 h-4 text-blue-400 flex-shrink-0" />
                        <span className="truncate max-w-[240px]">{job.original_filename}</span>
                      </td>
                      <td className="py-3 px-4 text-slate-400 font-mono text-[11px]">
                        {job.document_type}
                      </td>
                      <td className="py-3 px-4">
                        <span
                          className={`px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider inline-flex items-center gap-1 border ${
                            job.processing_status === 'COMPLETED'
                              ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
                              : job.processing_status === 'COMPLETED_WITH_WARNINGS'
                              ? 'bg-amber-500/10 text-amber-400 border-amber-500/20'
                              : job.processing_status === 'FAILED'
                              ? 'bg-red-500/10 text-red-400 border-red-500/20'
                              : 'bg-blue-500/10 text-blue-400 border-blue-500/20'
                          }`}
                        >
                          {job.processing_status}
                        </span>
                      </td>
                      <td className="py-3 px-4 font-bold text-white">
                        {job.question_count}
                      </td>
                      <td className="py-3 px-4">
                        {job.warning_count > 0 ? (
                          <span className="text-amber-400 font-semibold">{job.warning_count} flags</span>
                        ) : (
                          <span className="text-slate-500">0</span>
                        )}
                      </td>
                      <td className="py-3 px-4 text-slate-500 text-[11px]">
                        {job.created_at ? new Date(job.created_at).toLocaleDateString() : 'N/A'}
                      </td>
                      <td className="py-3 px-4 text-right">
                        <button
                          onClick={() => onSelectDocument(job.id, job.original_filename)}
                          className="text-xs text-cyan-400 hover:text-cyan-300 font-semibold inline-flex items-center gap-1 transition"
                        >
                          <span>Inspect</span>
                          <ArrowRight className="w-3.5 h-3.5" />
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="p-8 text-center text-slate-500 text-xs">
            No processing jobs have been submitted yet. Click "Create Processing Job" to get started.
          </div>
        )}
      </div>
    </div>
  );
}
