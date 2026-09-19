import React, { useState } from 'react';
import { documentAPI } from '../services/api';
import { UploadCloud, FileText, CheckCircle, AlertCircle, Sparkles, Key, Loader2 } from 'lucide-react';

const SAMPLES = [
  { file: 'sample_01_clean.pdf', type: 'QUESTION_PAPER', label: 'Clean PDF (4 Qs)', desc: 'Standard 4-option MCQs with answer table' },
  { file: 'sample_04_multi_page_question.pdf', type: 'QUESTION_PAPER', label: 'Multi-Page Q2 Test', desc: 'Question spanning across page boundaries' },
  { file: 'sample_03_low_quality.png', type: 'QUESTION_PAPER', label: 'Scan Image (PNG)', desc: 'Raster image of exam paper for OCR' },
  { file: 'sample_05_question_paper.pdf', type: 'QUESTION_PAPER', label: 'Unanswered Paper', desc: 'Question paper without answer key' },
  { file: 'sample_06_separate_answer_key.pdf', type: 'ANSWER_KEY', label: '+ Attach Separate Key', desc: 'Standalone answer key PDF' },
];

export default function NewJobPage({ onJobCreated }) {
  const [jobName, setJobName] = useState('');
  const [documentType, setDocumentType] = useState('QUESTION_PAPER');
  const [paperFile, setPaperFile] = useState(null);
  const [answerKeyFile, setAnswerKeyFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');
  const [successBanner, setSuccessBanner] = useState('');
  const [loadingSample, setLoadingSample] = useState('');

  const handlePaperDrop = (e) => {
    e.preventDefault();
    if (e.dataTransfer?.files?.length > 0) {
      setPaperFile(e.dataTransfer.files[0]);
      setSuccessBanner(`Selected: ${e.dataTransfer.files[0].name}`);
    }
  };

  const handleKeyDrop = (e) => {
    e.preventDefault();
    if (e.dataTransfer?.files?.length > 0) {
      setAnswerKeyFile(e.dataTransfer.files[0]);
      setSuccessBanner(`Attached Answer Key: ${e.dataTransfer.files[0].name}`);
    }
  };

  const loadSample = async (filename, type, label) => {
    setErrorMsg('');
    setLoadingSample(filename);
    try {
      const blob = await documentAPI.getSampleBlob(filename);
      const mime = filename.endsWith('.png') ? 'image/png' : 'application/pdf';
      const file = new File([blob], filename, { type: mime });

      if (type === 'ANSWER_KEY') {
        setAnswerKeyFile(file);
        setSuccessBanner(`✓ Attached Separate Answer Key: ${filename}`);
      } else {
        setPaperFile(file);
        setDocumentType('QUESTION_PAPER');
        setJobName(label);
        setSuccessBanner(`✓ Loaded ${filename} (${label}) into Question Paper slot!`);
      }
    } catch (err) {
      console.error(err);
      setErrorMsg(`Failed to load sample ${filename}. Please make sure the API server is active.`);
    } finally {
      setLoadingSample('');
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!paperFile) {
      setErrorMsg('Please select or load a Question Paper document first.');
      return;
    }

    setErrorMsg('');
    setLoading(true);

    try {
      // 1. Upload Question Paper
      const paperRes = await documentAPI.upload(paperFile, documentType);
      const questionDocId = paperRes.document_id;
      const jobId = paperRes.job_id;

      // 2. If separate answer key file is provided, upload and associate it
      if (answerKeyFile) {
        const keyRes = await documentAPI.upload(answerKeyFile, 'ANSWER_KEY');
        const keyDocId = keyRes.document_id;
        await documentAPI.createRelationship(keyDocId, questionDocId, 'ANSWER_KEY_FOR');
      }

      onJobCreated({
        documentId: questionDocId,
        jobId: jobId,
        jobName: jobName || paperFile.name,
        originalFilename: paperFile.name,
      });
    } catch (err) {
      const msg = err.response?.data?.detail || err.response?.data?.error?.message || 'Failed to submit job';
      setErrorMsg(typeof msg === 'string' ? msg : JSON.stringify(msg));
      setLoading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-extrabold text-white tracking-tight">Create Processing Job</h1>
        <p className="text-xs text-slate-400 mt-1">
          Upload an examination paper and optional answer key for automated question boundary detection and option parsing
        </p>
      </div>

      {errorMsg && (
        <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400 text-xs font-medium flex items-center gap-2">
          <AlertCircle className="w-4 h-4 flex-shrink-0" />
          <span>{errorMsg}</span>
        </div>
      )}

      {successBanner && (
        <div className="p-3.5 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 text-xs font-semibold flex items-center justify-between">
          <div className="flex items-center gap-2">
            <CheckCircle className="w-4 h-4 text-emerald-400 flex-shrink-0" />
            <span>{successBanner}</span>
          </div>
          <span className="text-[10px] text-emerald-400 font-mono">Ready to process</span>
        </div>
      )}

      {/* Curated Sample Loaders */}
      <div className="p-5 rounded-xl bg-slate-900 border border-slate-800 shadow-sm">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2 text-xs font-bold text-slate-300 uppercase tracking-wider">
            <Sparkles className="w-4 h-4 text-cyan-400" />
            <span>1-Click Curated Test Samples (Instant Evaluation)</span>
          </div>
          <span className="text-[11px] text-slate-400">Click any button below to auto-load</span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2.5">
          {SAMPLES.map((s) => {
            const isSelected =
              s.type === 'ANSWER_KEY'
                ? answerKeyFile?.name === s.file
                : paperFile?.name === s.file;
            const isLoading = loadingSample === s.file;

            return (
              <button
                key={s.file}
                type="button"
                disabled={isLoading}
                onClick={() => loadSample(s.file, s.type, s.label)}
                className={`p-3 rounded-xl border text-left transition flex flex-col justify-between ${
                  isSelected
                    ? 'bg-blue-600/15 border-blue-500 text-white shadow-md shadow-blue-500/10'
                    : 'bg-slate-950 hover:bg-slate-800/80 border-slate-800 text-slate-300 hover:text-white'
                }`}
              >
                <div className="flex items-center justify-between w-full mb-1">
                  <span className="text-xs font-bold flex items-center gap-1.5">
                    {s.type === 'ANSWER_KEY' ? (
                      <Key className="w-3.5 h-3.5 text-cyan-400" />
                    ) : (
                      <FileText className="w-3.5 h-3.5 text-blue-400" />
                    )}
                    {s.label}
                  </span>
                  {isLoading ? (
                    <Loader2 className="w-3.5 h-3.5 text-cyan-400 animate-spin" />
                  ) : isSelected ? (
                    <span className="text-[10px] font-bold text-emerald-400 bg-emerald-500/15 px-1.5 py-0.5 rounded">
                      ✓ Loaded
                    </span>
                  ) : null}
                </div>
                <p className="text-[10px] text-slate-400">{s.desc}</p>
              </button>
            );
          })}
        </div>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-sm space-y-5">
          {/* Job Name */}
          <div>
            <label className="block text-xs font-bold text-slate-300 uppercase tracking-wider mb-2">
              Job / Assessment Name
            </label>
            <input
              type="text"
              value={jobName}
              onChange={(e) => setJobName(e.target.value)}
              placeholder="e.g. Physics Mock Examination 2026"
              className="w-full px-3.5 py-2.5 bg-slate-950 border border-slate-800 rounded-lg text-xs text-white placeholder-slate-500 focus:outline-none focus:border-blue-500 transition"
            />
          </div>

          {/* Primary Dropzone: Question Paper */}
          <div>
            <label className="block text-xs font-bold text-slate-300 uppercase tracking-wider mb-2">
              Question Paper Document <span className="text-red-400">*</span>
            </label>
            <div
              onDragOver={(e) => e.preventDefault()}
              onDrop={handlePaperDrop}
              className={`border-2 border-dashed rounded-xl p-8 text-center transition cursor-pointer relative ${
                paperFile
                  ? 'border-emerald-500/50 bg-emerald-500/5'
                  : 'border-slate-800 hover:border-slate-700 bg-slate-950/50'
              }`}
            >
              <input
                type="file"
                accept=".pdf,.png,.jpg,.jpeg"
                onChange={(e) => {
                  if (e.target.files?.length) {
                    setPaperFile(e.target.files[0]);
                    setSuccessBanner(`Selected: ${e.target.files[0].name}`);
                  }
                }}
                className="absolute inset-0 opacity-0 cursor-pointer w-full h-full"
              />
              <UploadCloud className={`w-10 h-10 mx-auto mb-3 ${paperFile ? 'text-emerald-400' : 'text-blue-500'}`} />
              {paperFile ? (
                <div>
                  <p className="text-sm font-bold text-white">{paperFile.name}</p>
                  <p className="text-xs text-emerald-400 mt-1">
                    {(paperFile.size / 1024 / 1024).toFixed(2)} MB • Ready to process
                  </p>
                  <button
                    type="button"
                    onClick={(e) => { e.stopPropagation(); setPaperFile(null); }}
                    className="text-[11px] text-red-400 hover:underline mt-2 inline-block font-semibold"
                  >
                    Remove File
                  </button>
                </div>
              ) : (
                <div>
                  <p className="text-xs font-bold text-white">Click to browse or drag question paper here</p>
                  <p className="text-[11px] text-slate-500 mt-1">Supported: Digital PDF, Scan PDF, PNG, JPG (Max 25MB)</p>
                </div>
              )}
            </div>
          </div>

          {/* Secondary Dropzone: Optional Separate Answer Key */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <label className="text-xs font-bold text-slate-300 uppercase tracking-wider flex items-center gap-1.5">
                <Key className="w-3.5 h-3.5 text-cyan-400" />
                <span>Separate Answer Key (Optional)</span>
              </label>
              <span className="text-[11px] text-slate-500">Cross-document answer linking</span>
            </div>
            <div
              onDragOver={(e) => e.preventDefault()}
              onDrop={handleKeyDrop}
              className={`border-2 border-dashed rounded-xl p-5 text-center transition cursor-pointer relative ${
                answerKeyFile
                  ? 'border-cyan-500/50 bg-cyan-500/5'
                  : 'border-slate-800 hover:border-slate-700 bg-slate-950/50'
              }`}
            >
              <input
                type="file"
                accept=".pdf,.png,.jpg,.jpeg"
                onChange={(e) => {
                  if (e.target.files?.length) {
                    setAnswerKeyFile(e.target.files[0]);
                    setSuccessBanner(`Attached Answer Key: ${e.target.files[0].name}`);
                  }
                }}
                className="absolute inset-0 opacity-0 cursor-pointer w-full h-full"
              />
              {answerKeyFile ? (
                <div className="flex items-center justify-center gap-2">
                  <CheckCircle className="w-4 h-4 text-cyan-400" />
                  <span className="text-xs font-bold text-white">{answerKeyFile.name}</span>
                  <button
                    type="button"
                    onClick={(e) => { e.stopPropagation(); setAnswerKeyFile(null); }}
                    className="text-[10px] text-red-400 hover:underline ml-2"
                  >
                    Remove
                  </button>
                </div>
              ) : (
                <p className="text-xs text-slate-400">
                  Optional: Drop a separate AnswerKey.pdf to automatically link questions to answers
                </p>
              )}
            </div>
          </div>
        </div>

        {/* Submit */}
        <button
          type="submit"
          disabled={loading || !paperFile}
          className="w-full py-3 px-6 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white font-bold text-xs rounded-xl shadow-lg shadow-blue-500/25 disabled:opacity-50 transition flex items-center justify-center gap-2"
        >
          {loading ? (
            <span>Uploading & Queueing Processing Job...</span>
          ) : (
            <>
              <UploadCloud className="w-4 h-4" />
              <span>Start Asynchronous Processing Pipeline</span>
            </>
          )}
        </button>
      </form>
    </div>
  );
}
