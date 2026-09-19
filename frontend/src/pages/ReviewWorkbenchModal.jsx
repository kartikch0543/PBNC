import React, { useState } from 'react';
import { questionAPI, documentAPI } from '../services/api';
import { X, Check, AlertTriangle, FileText, ExternalLink, Save, ArrowLeft, ArrowRight } from 'lucide-react';

export default function ReviewWorkbenchModal({ documentId, question, warnings, onClose, onSaveSuccess }) {
  const [stem, setStem] = useState(question.question_text || '');
  const [options, setOptions] = useState(question.options || []);
  const [answer, setAnswer] = useState(question.detected_answer || '');
  const [reviewNotes, setReviewNotes] = useState(question.review_notes || '');
  const [activePage, setActivePage] = useState(question.source_pages?.[0] || 1);
  const [saving, setSaving] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');

  const qWarnings = warnings.filter((w) => w.question_id === question.id);

  const handleOptionTextChange = (idx, newText) => {
    const updated = [...options];
    updated[idx] = { ...updated[idx], text: newText };
    setOptions(updated);
  };

  const handleSave = async () => {
    setSaving(true);
    setErrorMsg('');
    try {
      const updated = await questionAPI.review(question.id, {
        question_text: stem,
        options: options,
        detected_answer: answer || null,
        review_notes: reviewNotes || null,
        mark_reviewed: true,
      });
      onSaveSuccess(updated);
    } catch (err) {
      setErrorMsg('Failed to save correction.');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-6xl max-h-[90vh] flex flex-col shadow-2xl shadow-black/80 overflow-hidden">
        {/* Modal Header */}
        <div className="p-4 px-6 border-b border-slate-800 flex items-center justify-between bg-slate-950">
          <div className="flex items-center gap-3">
            <span className="px-2.5 py-1 rounded-md bg-blue-600/15 border border-blue-500/30 text-blue-400 font-bold text-xs">
              {question.question_number ? `Question ${question.question_number}` : 'Unnumbered Question'}
            </span>
            <div>
              <h2 className="text-sm font-bold text-white">Reviewer Correction Workbench</h2>
              <p className="text-[11px] text-slate-400">
                Side-by-side human audit & ground-truth verification
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Modal Split Body */}
        <div className="flex-1 overflow-y-auto grid grid-cols-1 lg:grid-cols-2 divide-y lg:divide-y-0 lg:divide-x divide-slate-800">
          {/* Left Column: Human Correction Form */}
          <div className="p-6 space-y-5 overflow-y-auto">
            {errorMsg && (
              <div className="p-3 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400 text-xs">
                {errorMsg}
              </div>
            )}

            {/* Explainable Confidence & Why Low Warning */}
            <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">
                  Explainable Extraction Confidence
                </span>
                <span
                  className={`text-xs font-extrabold px-2 py-0.5 rounded-full ${
                    question.confidence_score >= 0.8
                      ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                      : question.confidence_score >= 0.5
                      ? 'bg-amber-500/10 text-amber-400 border border-amber-500/20'
                      : 'bg-red-500/10 text-red-400 border border-red-500/20'
                  }`}
                >
                  {Math.round(question.confidence_score * 100)}% Confidence
                </span>
              </div>

              {qWarnings.length > 0 ? (
                <div className="space-y-1.5 pt-2">
                  <span className="text-[10px] font-bold text-amber-400 uppercase tracking-wider block">
                    Uncertainty Diagnostic Flags:
                  </span>
                  {qWarnings.map((w, idx) => (
                    <div
                      key={idx}
                      className="text-xs text-amber-300/90 bg-amber-500/10 border-l-2 border-amber-400 px-3 py-1.5 rounded-r"
                    >
                      <span className="font-bold">[{w.warning_code}]</span> {w.message}
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-xs text-slate-400">
                  Clean extraction: question boundaries, options, and answer matched reliably.
                </p>
              )}
            </div>

            {/* Editable Question Text */}
            <div>
              <label className="block text-xs font-bold text-slate-300 uppercase tracking-wider mb-1.5">
                Question Stem (Text)
              </label>
              <textarea
                rows={4}
                value={stem}
                onChange={(e) => setStem(e.target.value)}
                className="w-full p-3 bg-slate-950 border border-slate-800 rounded-xl text-xs text-white placeholder-slate-500 focus:outline-none focus:border-blue-500 transition leading-relaxed font-sans"
              />
            </div>

            {/* Editable Options */}
            <div>
              <label className="block text-xs font-bold text-slate-300 uppercase tracking-wider mb-2">
                Options Choices
              </label>
              <div className="space-y-2">
                {options.map((opt, idx) => (
                  <div key={idx} className="flex items-center gap-2">
                    <span className="w-8 h-8 rounded-lg bg-slate-950 border border-slate-800 flex items-center justify-center text-xs font-bold text-white flex-shrink-0">
                      {opt.key}
                    </span>
                    <input
                      type="text"
                      value={opt.text}
                      onChange={(e) => handleOptionTextChange(idx, e.target.value)}
                      className="flex-1 px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-slate-200 focus:outline-none focus:border-blue-500 transition"
                    />
                  </div>
                ))}
              </div>
            </div>

            {/* Editable Correct Answer */}
            <div>
              <label className="block text-xs font-bold text-slate-300 uppercase tracking-wider mb-1.5">
                Verified Correct Answer Key
              </label>
              <input
                type="text"
                value={answer}
                onChange={(e) => setAnswer(e.target.value)}
                placeholder="e.g. A, B, C, D"
                className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-white placeholder-slate-500 focus:outline-none focus:border-blue-500 transition font-mono uppercase"
              />
            </div>

            {/* Reviewer Audit Notes */}
            <div>
              <label className="block text-xs font-bold text-slate-300 uppercase tracking-wider mb-1.5">
                Reviewer Audit Notes
              </label>
              <input
                type="text"
                value={reviewNotes}
                onChange={(e) => setReviewNotes(e.target.value)}
                placeholder="Explain what was modified for audit trail (e.g. Corrected OCR typo in option C)"
                className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-white placeholder-slate-500 focus:outline-none focus:border-blue-500 transition"
              />
            </div>
          </div>

          {/* Right Column: Source Document Page Preview */}
          <div className="p-6 bg-slate-950/60 flex flex-col space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">
                  Source Document Traceability
                </span>
                <p className="text-[11px] text-slate-500">
                  Page {activePage} of {question.source_pages?.join(', ')}
                </p>
              </div>

              {question.source_pages && question.source_pages.length > 1 && (
                <div className="flex items-center gap-1.5 bg-slate-900 p-1 rounded-lg border border-slate-800">
                  {question.source_pages.map((p) => (
                    <button
                      key={p}
                      onClick={() => setActivePage(p)}
                      className={`px-2.5 py-1 rounded text-xs font-bold transition ${
                        activePage === p ? 'bg-blue-600 text-white' : 'text-slate-400 hover:text-white'
                      }`}
                    >
                      Page {p}
                    </button>
                  ))}
                </div>
              )}
            </div>

            {/* High-DPI Page Image Preview */}
            <div className="flex-1 bg-slate-950 border border-slate-800 rounded-xl overflow-auto p-2 flex items-center justify-center min-h-[350px]">
              <img
                src={documentAPI.getSourcePageUrl(documentId, activePage)}
                alt={`Source page ${activePage}`}
                className="max-w-full max-h-[500px] object-contain rounded border border-slate-800 shadow-md"
                onError={(e) => {
                  e.target.style.display = 'none';
                  e.target.parentNode.innerHTML =
                    '<p class="text-xs text-slate-500 text-center p-6">Source page preview unavailable</p>';
                }}
              />
            </div>
          </div>
        </div>

        {/* Modal Footer */}
        <div className="p-4 px-6 border-t border-slate-800 bg-slate-950 flex items-center justify-between">
          <div className="text-[11px] text-slate-500">
            Original extraction is safely preserved in database audit logs.
          </div>
          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 rounded-lg border border-slate-800 text-xs font-semibold text-slate-300 hover:text-white transition"
            >
              Cancel
            </button>
            <button
              type="button"
              disabled={saving}
              onClick={handleSave}
              className="inline-flex items-center gap-2 px-5 py-2 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white text-xs font-bold rounded-lg shadow-lg shadow-blue-500/25 transition disabled:opacity-50"
            >
              <Save className="w-3.5 h-3.5" />
              <span>{saving ? 'Saving Correction...' : 'Save Correction & Mark Reviewed'}</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
