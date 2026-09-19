import React, { useEffect, useState } from 'react';
import { questionAPI, documentAPI } from '../services/api';
import {
  FileText,
  Search,
  Filter,
  CheckCircle,
  AlertTriangle,
  Code,
  Edit3,
  Copy,
  ExternalLink,
  RefreshCw,
  Eye,
} from 'lucide-react';
import ReviewWorkbenchModal from './ReviewWorkbenchModal';

export default function ResultsPage({ documentId, documentName, onBack }) {
  const [questions, setQuestions] = useState([]);
  const [warnings, setWarnings] = useState([]);
  const [answersData, setAnswersData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeFilter, setActiveFilter] = useState('ALL'); // 'ALL' | 'CONFIDENT' | 'REVIEW' | 'UNCERTAIN'
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedQuestion, setSelectedQuestion] = useState(null);
  const [showJsonModal, setShowJsonModal] = useState(false);
  const [copied, setCopied] = useState(false);

  const fetchData = async () => {
    if (!documentId) return;
    setLoading(true);
    try {
      const [qData, warnData, ansData] = await Promise.all([
        questionAPI.listByDocument(documentId),
        questionAPI.getWarnings(documentId),
        questionAPI.getAnswers(documentId),
      ]);
      setQuestions(qData.questions || []);
      setWarnings(warnData || []);
      setAnswersData(ansData || {});
    } catch (err) {
      console.error('Failed to load results:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [documentId]);

  const handleReviewSave = (updatedQuestion) => {
    setQuestions((prev) =>
      prev.map((q) => (q.id === updatedQuestion.id ? updatedQuestion : q))
    );
    setSelectedQuestion(null);
  };

  // Filter questions
  const filteredQuestions = questions.filter((q) => {
    const qWarns = warnings.filter((w) => w.question_id === q.id);
    const confPct = Math.round(q.confidence_score * 100);

    // Search query check
    const matchesSearch =
      q.question_text.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (q.options && q.options.some((o) => o.text.toLowerCase().includes(searchQuery.toLowerCase())));

    if (!matchesSearch) return false;

    if (activeFilter === 'CONFIDENT') return confPct >= 80 && qWarns.length === 0;
    if (activeFilter === 'REVIEW') return confPct < 80 || qWarns.length > 0;
    if (activeFilter === 'UNCERTAIN') return !q.detected_answer;
    return true;
  });

  const confidentCount = questions.filter(
    (q) => Math.round(q.confidence_score * 100) >= 80 && !warnings.some((w) => w.question_id === q.id)
  ).length;
  const reviewCount = questions.length - confidentCount;
  const answeredCount = answersData?.answered_questions || questions.filter((q) => q.detected_answer).length;

  const structuredExport = questions.map((q) => ({
    question: q.question_text,
    options: (q.options || []).map((o) => o.text),
    answer: q.detected_answer,
    source_pages: q.source_pages || [],
    confidence: Math.round(q.confidence_score * 100) / 100,
  }));

  const copyExportJson = () => {
    navigator.clipboard.writeText(JSON.stringify(structuredExport, null, 2));
    setCopied(true);
    setTimeout(() => setCopied(false), 2500);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-xs font-bold uppercase tracking-wider text-blue-400">
              Extracted Results
            </span>
          </div>
          <h1 className="text-2xl font-extrabold text-white tracking-tight mt-0.5">
            {documentName || 'Document Assessment'}
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Machine-readable question stems, options, confidence validation, and human review workbench
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={fetchData}
            title="Refresh"
            className="p-2 rounded-lg bg-slate-900 border border-slate-800 text-slate-400 hover:text-white transition"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          </button>
          <button
            onClick={() => setShowJsonModal(true)}
            className="inline-flex items-center gap-2 px-3.5 py-2 rounded-lg bg-cyan-500/10 border border-cyan-500/30 text-cyan-400 hover:bg-cyan-500/20 text-xs font-bold transition"
          >
            <Code className="w-4 h-4" />
            <span>Structured JSON (Sec 7)</span>
          </button>
        </div>
      </div>

      {/* KPI Stats Banner */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 text-center">
          <span className="block text-2xl font-extrabold text-white">{questions.length}</span>
          <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400">Total Questions</span>
        </div>
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 text-center">
          <span className="block text-2xl font-extrabold text-emerald-400">{confidentCount}</span>
          <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400">Confident (≥80%)</span>
        </div>
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 text-center">
          <span className="block text-2xl font-extrabold text-amber-400">{reviewCount}</span>
          <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400">Review Required</span>
        </div>
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 text-center">
          <span className="block text-2xl font-extrabold text-cyan-400">{answeredCount}</span>
          <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400">Answers Matched</span>
        </div>
      </div>

      {/* Search & Filter Toolbar */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 flex flex-col sm:flex-row items-center justify-between gap-3 shadow-sm">
        {/* Search */}
        <div className="relative w-full sm:w-80">
          <Search className="w-4 h-4 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search questions or options..."
            className="w-full pl-9 pr-3 py-1.5 bg-slate-950 border border-slate-800 rounded-lg text-xs text-white placeholder-slate-500 focus:outline-none focus:border-blue-500 transition"
          />
        </div>

        {/* Filter Chips */}
        <div className="flex items-center gap-1.5 w-full sm:w-auto overflow-x-auto">
          <button
            onClick={() => setActiveFilter('ALL')}
            className={`px-3 py-1 rounded-lg text-xs font-semibold transition ${
              activeFilter === 'ALL'
                ? 'bg-blue-600 text-white shadow'
                : 'bg-slate-950 text-slate-400 hover:text-white border border-slate-800'
            }`}
          >
            All ({questions.length})
          </button>
          <button
            onClick={() => setActiveFilter('CONFIDENT')}
            className={`px-3 py-1 rounded-lg text-xs font-semibold transition ${
              activeFilter === 'CONFIDENT'
                ? 'bg-emerald-600 text-white shadow'
                : 'bg-slate-950 text-slate-400 hover:text-white border border-slate-800'
            }`}
          >
            Confident ({confidentCount})
          </button>
          <button
            onClick={() => setActiveFilter('REVIEW')}
            className={`px-3 py-1 rounded-lg text-xs font-semibold transition ${
              activeFilter === 'REVIEW'
                ? 'bg-amber-600 text-white shadow'
                : 'bg-slate-950 text-slate-400 hover:text-white border border-slate-800'
            }`}
          >
            Review Required ({reviewCount})
          </button>
          <button
            onClick={() => setActiveFilter('UNCERTAIN')}
            className={`px-3 py-1 rounded-lg text-xs font-semibold transition ${
              activeFilter === 'UNCERTAIN'
                ? 'bg-cyan-600 text-white shadow'
                : 'bg-slate-950 text-slate-400 hover:text-white border border-slate-800'
            }`}
          >
            Unmatched Answers
          </button>
        </div>
      </div>

      {/* Questions List */}
      <div className="space-y-4">
        {filteredQuestions.length > 0 ? (
          filteredQuestions.map((q) => {
            const qWarns = warnings.filter((w) => w.question_id === q.id);
            const confPct = Math.round(q.confidence_score * 100);

            return (
              <div
                key={q.id}
                className="bg-slate-900 border border-slate-800 hover:border-slate-700 rounded-xl p-5 shadow-sm transition space-y-3"
              >
                {/* Card Top Row */}
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <div className="flex items-center gap-2">
                    <span className="px-2.5 py-0.5 rounded-md bg-blue-600/15 border border-blue-500/30 text-blue-400 font-bold text-xs">
                      {q.question_number ? `Q${q.question_number}` : 'Unnumbered'}
                    </span>
                    {q.is_reviewed && (
                      <span className="px-2 py-0.5 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-[10px] font-bold uppercase">
                        ✓ Manually Reviewed
                      </span>
                    )}
                  </div>

                  <div className="flex items-center gap-3">
                    <span
                      className={`text-xs font-bold px-2 py-0.5 rounded-full ${
                        confPct >= 80
                          ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                          : confPct >= 50
                          ? 'bg-amber-500/10 text-amber-400 border border-amber-500/20'
                          : 'bg-red-500/10 text-red-400 border border-red-500/20'
                      }`}
                    >
                      {confPct}% Confidence
                    </span>

                    <span className="text-xs font-mono text-slate-400">
                      Page(s): {q.source_pages?.join(', ')}
                    </span>

                    <button
                      onClick={() => setSelectedQuestion(q)}
                      className="inline-flex items-center gap-1.5 px-3 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold transition"
                    >
                      <Edit3 className="w-3.5 h-3.5 text-blue-400" />
                      <span>Review / Source</span>
                    </button>
                  </div>
                </div>

                {/* Question Stem */}
                <p className="text-sm font-semibold text-slate-100 leading-relaxed">
                  {q.question_text}
                </p>

                {/* Options Grid */}
                {q.options && q.options.length > 0 && (
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 pt-1">
                    {q.options.map((opt, idx) => {
                      const isMatch = q.detected_answer && opt.key && q.detected_answer.toUpperCase() === opt.key.toUpperCase();
                      return (
                        <div
                          key={idx}
                          className={`p-2.5 rounded-lg border text-xs flex items-center gap-2.5 transition ${
                            isMatch
                              ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-200 font-semibold'
                              : 'bg-slate-950 border-slate-800 text-slate-300'
                          }`}
                        >
                          <span
                            className={`w-6 h-6 rounded flex items-center justify-center font-bold text-[11px] flex-shrink-0 ${
                              isMatch ? 'bg-emerald-500 text-slate-950' : 'bg-slate-800 text-slate-300'
                            }`}
                          >
                            {opt.key}
                          </span>
                          <span className="flex-1 truncate">{opt.text}</span>
                          {isMatch && (
                            <span className="text-[10px] font-bold text-emerald-400 uppercase tracking-wider">
                              ✓ Answer
                            </span>
                          )}
                        </div>
                      );
                    })}
                  </div>
                )}

                {/* Warning Flags */}
                {qWarns.length > 0 && (
                  <div className="space-y-1.5 pt-1">
                    {qWarns.map((w, idx) => (
                      <div
                        key={idx}
                        className="text-xs text-amber-300/90 bg-amber-500/10 border-l-2 border-amber-400 px-3 py-1.5 rounded-r flex items-center gap-2"
                      >
                        <AlertTriangle className="w-3.5 h-3.5 text-amber-400 flex-shrink-0" />
                        <span>
                          <strong className="font-bold">[{w.warning_code}]</strong> {w.message}
                        </span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            );
          })
        ) : (
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-12 text-center text-slate-500 text-xs">
            No questions found matching the selected filter or search query.
          </div>
        )}
      </div>

      {/* Review Workbench Modal */}
      {selectedQuestion && (
        <ReviewWorkbenchModal
          documentId={documentId}
          question={selectedQuestion}
          warnings={warnings}
          onClose={() => setSelectedQuestion(null)}
          onSaveSuccess={handleReviewSave}
        />
      )}

      {/* Assignment Section 7 Export Modal */}
      {showJsonModal && (
        <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-3xl max-h-[85vh] flex flex-col shadow-2xl">
            <div className="p-4 px-6 border-b border-slate-800 flex items-center justify-between">
              <div>
                <h3 className="text-sm font-bold text-white">Structured Output (Assignment Section 7)</h3>
                <p className="text-[11px] text-slate-400">System-independent machine-readable format</p>
              </div>
              <button
                onClick={() => setShowJsonModal(false)}
                className="text-slate-400 hover:text-white text-lg font-bold"
              >
                &times;
              </button>
            </div>
            <div className="p-6 bg-slate-950 overflow-auto flex-1 font-mono text-xs text-cyan-300">
              <pre>{JSON.stringify(structuredExport, null, 2)}</pre>
            </div>
            <div className="p-4 px-6 border-t border-slate-800 flex justify-end gap-2">
              <button
                onClick={copyExportJson}
                className="inline-flex items-center gap-1.5 px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white text-xs font-bold rounded-lg transition"
              >
                <Copy className="w-3.5 h-3.5" />
                <span>{copied ? 'Copied to Clipboard!' : 'Copy JSON'}</span>
              </button>
              <button
                onClick={() => setShowJsonModal(false)}
                className="px-4 py-2 rounded-lg border border-slate-800 text-xs font-semibold text-slate-400 hover:text-white transition"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
