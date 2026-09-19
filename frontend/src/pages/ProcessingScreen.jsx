import React, { useEffect, useState } from 'react';
import { documentAPI, questionAPI } from '../services/api';
import { CheckCircle2, Circle, Clock, AlertTriangle, ArrowRight, Loader2 } from 'lucide-react';

const STAGES = [
  { id: 'VALIDATE', label: 'File Validated (MIME & size check)' },
  { id: 'STORE', label: 'Document Stored & Hashed' },
  { id: 'TEXT_EXTRACT', label: 'Text & Visual Layer Extraction' },
  { id: 'BOUNDARIES', label: 'Detecting Question Boundaries' },
  { id: 'MULTIPAGE', label: 'Reconstructing Multi-Page Questions' },
  { id: 'OPTIONS', label: 'Extracting Standardized Options (A-D)' },
  { id: 'ANSWERS', label: 'Detecting & Linking Answer Keys' },
  { id: 'CONFIDENCE', label: 'Calculating Explainable Confidence' },
];

export default function ProcessingScreen({ jobInfo, onComplete }) {
  const [statusData, setStatusData] = useState(null);
  const [discoveredQuestions, setDiscoveredQuestions] = useState(0);
  const [discoveredWarnings, setDiscoveredWarnings] = useState(0);
  const [completed, setCompleted] = useState(false);

  useEffect(() => {
    let intervalId = null;

    const poll = async () => {
      try {
        const data = await documentAPI.getStatus(jobInfo.documentId);
        setStatusData(data);

        // Fetch partial discovered counts
        try {
          const qData = await questionAPI.listByDocument(jobInfo.documentId);
          setDiscoveredQuestions(qData.total_count || 0);
          setDiscoveredWarnings(qData.review_required_count || 0);
        } catch (e) {
          // ignore transient count errors while pipeline runs
        }

        if (
          data.status === 'COMPLETED' ||
          data.status === 'COMPLETED_WITH_WARNINGS' ||
          data.status === 'FAILED'
        ) {
          clearInterval(intervalId);
          setCompleted(true);
        }
      } catch (err) {
        console.error('Polling error:', err);
      }
    };

    poll();
    intervalId = setInterval(poll, 1200);

    return () => clearInterval(intervalId);
  }, [jobInfo.documentId]);

  // Determine stage progression index based on backend progress_pct
  const getStageState = (idx) => {
    const pct = statusData?.progress_pct || 0;
    const stageThreshold = (idx + 1) * 12.5;

    if (completed && statusData?.status !== 'FAILED') return 'done';
    if (pct >= stageThreshold) return 'done';
    if (pct >= stageThreshold - 12.5) return 'current';
    return 'pending';
  };

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      {/* Header */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-sm">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xs font-bold uppercase tracking-wider text-cyan-400">
                Pipeline Processing
              </span>
              <span
                className={`px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider ${
                  completed
                    ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                    : 'bg-blue-500/10 text-blue-400 border border-blue-500/20'
                }`}
              >
                {statusData?.status || 'PROCESSING'}
              </span>
            </div>
            <h1 className="text-xl font-extrabold text-white mt-1">
              {jobInfo.jobName || jobInfo.originalFilename}
            </h1>
            <p className="text-xs text-slate-400 mt-0.5">
              Current Stage: <span className="text-slate-200 font-semibold">{statusData?.current_step || 'Initializing...'}</span>
            </p>
          </div>

          {/* Quick Metrics */}
          <div className="flex items-center gap-4 bg-slate-950 p-3 rounded-xl border border-slate-800">
            <div className="text-center px-2">
              <span className="block text-xl font-extrabold text-white">{discoveredQuestions}</span>
              <span className="text-[10px] text-slate-400 uppercase font-bold">Questions</span>
            </div>
            <div className="w-px h-8 bg-slate-800"></div>
            <div className="text-center px-2">
              <span className="block text-xl font-extrabold text-amber-400">{discoveredWarnings}</span>
              <span className="text-[10px] text-slate-400 uppercase font-bold">Warnings</span>
            </div>
          </div>
        </div>

        {/* Progress Bar */}
        <div className="mt-6">
          <div className="w-full h-2 bg-slate-950 rounded-full overflow-hidden border border-slate-800">
            <div
              className="h-full bg-gradient-to-r from-blue-600 via-indigo-600 to-cyan-500 transition-all duration-500 ease-out"
              style={{ width: `${statusData?.progress_pct || 0}%` }}
            ></div>
          </div>
        </div>
      </div>

      {/* Discrete Real-Time Stages Card */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-sm">
        <h2 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-4">
          Pipeline Execution Stages
        </h2>

        <div className="space-y-3">
          {STAGES.map((stage, idx) => {
            const state = getStageState(idx);
            return (
              <div
                key={stage.id}
                className={`flex items-center gap-3 p-3 rounded-xl border transition ${
                  state === 'done'
                    ? 'bg-emerald-500/5 border-emerald-500/20 text-emerald-300'
                    : state === 'current'
                    ? 'bg-blue-500/10 border-blue-500/30 text-white shadow-sm'
                    : 'bg-slate-950/40 border-slate-800/60 text-slate-500'
                }`}
              >
                {state === 'done' ? (
                  <CheckCircle2 className="w-5 h-5 text-emerald-400 flex-shrink-0" />
                ) : state === 'current' ? (
                  <Loader2 className="w-5 h-5 text-blue-400 animate-spin flex-shrink-0" />
                ) : (
                  <Circle className="w-5 h-5 text-slate-700 flex-shrink-0" />
                )}

                <div className="flex-1">
                  <p className="text-xs font-semibold">{stage.label}</p>
                </div>

                <span className="text-[10px] uppercase font-mono font-bold">
                  {state === 'done' ? 'Completed' : state === 'current' ? 'In Progress' : 'Pending'}
                </span>
              </div>
            );
          })}
        </div>

        {completed && (
          <div className="mt-6 pt-5 border-t border-slate-800 flex justify-end">
            <button
              onClick={() => onComplete(jobInfo.documentId, jobInfo.originalFilename)}
              className="inline-flex items-center gap-2 px-5 py-2.5 bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white text-xs font-bold rounded-xl shadow-lg shadow-emerald-500/25 transition"
            >
              <span>Inspect Extracted Questions & Review Queue</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
