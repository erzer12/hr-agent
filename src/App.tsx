import React, { useState } from 'react';
import { Upload, FileText, Calendar, Mail, Check, X, Star, Clock, User, Phone, MapPin, AlertCircle, CheckCircle, Loader2 } from 'lucide-react';

interface Candidate {
  id: string;
  name: string;
  email: string;
  phone?: string;
  score: number;
  summary: string[];
  selected: boolean;
}

interface ProcessingStatus {
  isProcessing: boolean;
  isScheduling: boolean;
  message: string;
  type: 'info' | 'success' | 'error';
}

function App() {
  const [jobDescription, setJobDescription] = useState('');
  const [uploadedFiles, setUploadedFiles] = useState<File[]>([]);
  const [candidates, setCandidates] = useState<Candidate[]>([]);
  const [status, setStatus] = useState<ProcessingStatus>({
    isProcessing: false,
    isScheduling: false,
    message: '',
    type: 'info'
  });

  const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(event.target.files || []);
    const pdfFiles = files.filter(file => file.type === 'application/pdf');
    setUploadedFiles(prev => [...prev, ...pdfFiles]);
  };

  const handleFileDrop = (event: React.DragEvent) => {
    event.preventDefault();
    const files = Array.from(event.dataTransfer.files);
    const pdfFiles = files.filter(file => file.type === 'application/pdf');
    setUploadedFiles(prev => [...prev, ...pdfFiles]);
  };

  const removeFile = (index: number) => {
    setUploadedFiles(prev => prev.filter((_, i) => i !== index));
  };

  const toggleCandidateSelection = (candidateId: string) => {
    setCandidates(prev =>
      prev.map(candidate =>
        candidate.id === candidateId
          ? { ...candidate, selected: !candidate.selected }
          : candidate
      )
    );
  };

  const processResumes = async () => {
    if (!jobDescription.trim() || uploadedFiles.length === 0) {
      setStatus({
        isProcessing: false,
        isScheduling: false,
        message: 'Please provide job description and upload resumes',
        type: 'error'
      });
      return;
    }

    setStatus({
      isProcessing: true,
      isScheduling: false,
      message: 'Analyzing resumes and ranking candidates...',
      type: 'info'
    });

    const formData = new FormData();
    formData.append('job_description', jobDescription);
    uploadedFiles.forEach(file => {
      formData.append('resumes', file);
    });

    try {
      const response = await fetch('/api/process', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error('Failed to process resumes');
      }

      const data = await response.json();
      setCandidates(data.candidates.map((candidate: any, index: number) => ({
        ...candidate,
        id: `candidate-${index}`,
        selected: false
      })));

      setStatus({
        isProcessing: false,
        isScheduling: false,
        message: `Successfully analyzed ${data.candidates.length} candidates`,
        type: 'success'
      });
    } catch (error) {
      setStatus({
        isProcessing: false,
        isScheduling: false,
        message: 'Error processing resumes. Please try again.',
        type: 'error'
      });
    }
  };

  const scheduleInterviews = async () => {
    const selectedCandidates = candidates.filter(c => c.selected);
    
    if (selectedCandidates.length === 0) {
      setStatus({
        isProcessing: false,
        isScheduling: false,
        message: 'Please select at least one candidate',
        type: 'error'
      });
      return;
    }

    setStatus({
      isProcessing: false,
      isScheduling: true,
      message: `Scheduling interviews for ${selectedCandidates.length} candidates...`,
      type: 'info'
    });

    try {
      const response = await fetch('/api/schedule', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          candidates: selectedCandidates.map(c => ({
            name: c.name,
            email: c.email,
            phone: c.phone
          }))
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to schedule interviews');
      }

      const data = await response.json();
      setStatus({
        isProcessing: false,
        isScheduling: false,
        message: data.message || 'Interviews scheduled successfully!',
        type: 'success'
      });
    } catch (error) {
      setStatus({
        isProcessing: false,
        isScheduling: false,
        message: 'Error scheduling interviews. Please try again.',
        type: 'error'
      });
    }
  };

  const selectedCount = candidates.filter(c => c.selected).length;

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50">
      <div className="container mx-auto px-6 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">HR AI Agent Dashboard</h1>
          <p className="text-gray-600">Autonomous resume screening and interview scheduling</p>
        </div>

        {/* Status Bar */}
        {status.message && (
          <div className={`mb-6 p-4 rounded-lg border ${
            status.type === 'success' ? 'bg-green-50 border-green-200 text-green-800' :
            status.type === 'error' ? 'bg-red-50 border-red-200 text-red-800' :
            'bg-blue-50 border-blue-200 text-blue-800'
          }`}>
            <div className="flex items-center">
              {status.type === 'success' && <CheckCircle className="h-5 w-5 mr-2" />}
              {status.type === 'error' && <AlertCircle className="h-5 w-5 mr-2" />}
              {status.type === 'info' && status.isProcessing && <Loader2 className="h-5 w-5 mr-2 animate-spin" />}
              {status.type === 'info' && status.isScheduling && <Calendar className="h-5 w-5 mr-2" />}
              <span className="font-medium">{status.message}</span>
            </div>
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Left Column: Inputs */}
          <div className="space-y-6">
            {/* Job Description */}
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
              <h2 className="text-xl font-semibold text-gray-900 mb-4 flex items-center">
                <FileText className="h-5 w-5 mr-2 text-blue-600" />
                Job Description
              </h2>
              <textarea
                value={jobDescription}
                onChange={(e) => setJobDescription(e.target.value)}
                placeholder="Paste the complete job description here..."
                className="w-full h-40 p-4 border border-gray-300 rounded-lg resize-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                disabled={status.isProcessing}
              />
            </div>

            {/* Resume Upload */}
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
              <h2 className="text-xl font-semibold text-gray-900 mb-4 flex items-center">
                <Upload className="h-5 w-5 mr-2 text-emerald-600" />
                Resume Upload
              </h2>
              
              <div
                className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center hover:border-blue-400 transition-colors"
                onDragOver={(e) => e.preventDefault()}
                onDrop={handleFileDrop}
              >
                <Upload className="h-8 w-8 text-gray-400 mx-auto mb-3" />
                <p className="text-gray-600 mb-2">Drag and drop PDF files here, or</p>
                <label className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 cursor-pointer transition-colors">
                  <span>Choose Files</span>
                  <input
                    type="file"
                    multiple
                    accept=".pdf"
                    onChange={handleFileUpload}
                    className="hidden"
                    disabled={status.isProcessing}
                  />
                </label>
              </div>

              {/* Uploaded Files List */}
              {uploadedFiles.length > 0 && (
                <div className="mt-4 space-y-2">
                  <h3 className="font-medium text-gray-700">Uploaded Files ({uploadedFiles.length})</h3>
                  {uploadedFiles.map((file, index) => (
                    <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                      <div className="flex items-center">
                        <FileText className="h-4 w-4 text-red-500 mr-2" />
                        <span className="text-sm text-gray-700 truncate">{file.name}</span>
                      </div>
                      <button
                        onClick={() => removeFile(index)}
                        className="text-red-500 hover:text-red-700 p-1"
                        disabled={status.isProcessing}
                      >
                        <X className="h-4 w-4" />
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Process Button */}
            <button
              onClick={processResumes}
              disabled={!jobDescription.trim() || uploadedFiles.length === 0 || status.isProcessing}
              className="w-full py-3 px-4 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors flex items-center justify-center"
            >
              {status.isProcessing ? (
                <>
                  <Loader2 className="h-5 w-5 mr-2 animate-spin" />
                  Processing Resumes...
                </>
              ) : (
                <>
                  <Star className="h-5 w-5 mr-2" />
                  Process Resumes
                </>
              )}
            </button>
          </div>

          {/* Right Column: Candidate Review Panel */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4 flex items-center">
              <User className="h-5 w-5 mr-2 text-emerald-600" />
              Candidate Review Panel
              {selectedCount > 0 && (
                <span className="ml-2 px-2 py-1 bg-blue-100 text-blue-800 text-sm rounded-full">
                  {selectedCount} selected
                </span>
              )}
            </h2>

            {candidates.length === 0 ? (
              <div className="text-center py-12">
                <User className="h-12 w-12 text-gray-300 mx-auto mb-4" />
                <p className="text-gray-500">No candidates processed yet.</p>
                <p className="text-sm text-gray-400 mt-1">Upload resumes and process them to see ranked candidates here.</p>
              </div>
            ) : (
              <div className="space-y-4 max-h-96 overflow-y-auto">
                {candidates.map((candidate) => (
                  <div
                    key={candidate.id}
                    className={`border rounded-lg p-4 transition-all ${
                      candidate.selected ? 'border-blue-500 bg-blue-50' : 'border-gray-200 hover:border-gray-300'
                    }`}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center mb-2">
                          <input
                            type="checkbox"
                            checked={candidate.selected}
                            onChange={() => toggleCandidateSelection(candidate.id)}
                            className="h-4 w-4 text-blue-600 mr-3 rounded focus:ring-blue-500"
                          />
                          <h3 className="font-semibold text-gray-900">{candidate.name}</h3>
                        </div>
                        
                        <div className="space-y-1 mb-3">
                          <div className="flex items-center text-sm text-gray-600">
                            <Mail className="h-4 w-4 mr-1" />
                            {candidate.email}
                          </div>
                          {candidate.phone && (
                            <div className="flex items-center text-sm text-gray-600">
                              <Phone className="h-4 w-4 mr-1" />
                              {candidate.phone}
                            </div>
                          )}
                        </div>

                        <div className="mb-3">
                          <div className="flex items-center justify-between mb-1">
                            <span className="text-sm font-medium text-gray-700">Match Score</span>
                            <span className="text-lg font-bold text-blue-600">{candidate.score}/10</span>
                          </div>
                          <div className="w-full bg-gray-200 rounded-full h-2">
                            <div
                              className="bg-blue-600 h-2 rounded-full transition-all"
                              style={{ width: `${(candidate.score / 10) * 100}%` }}
                            ></div>
                          </div>
                        </div>

                        <div>
                          <h4 className="text-sm font-medium text-gray-700 mb-2">Key Highlights:</h4>
                          <ul className="text-sm text-gray-600 space-y-1">
                            {candidate.summary.map((point, index) => (
                              <li key={index} className="flex items-start">
                                <span className="text-blue-500 mr-2">•</span>
                                {point}
                              </li>
                            ))}
                          </ul>
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}

            {/* Schedule Interviews Button */}
            {candidates.length > 0 && (
              <div className="mt-6 pt-4 border-t border-gray-200">
                <button
                  onClick={scheduleInterviews}
                  disabled={selectedCount === 0 || status.isScheduling}
                  className="w-full py-3 px-4 bg-emerald-600 text-white rounded-lg font-medium hover:bg-emerald-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors flex items-center justify-center"
                >
                  {status.isScheduling ? (
                    <>
                      <Loader2 className="h-5 w-5 mr-2 animate-spin" />
                      Scheduling Interviews...
                    </>
                  ) : (
                    <>
                      <Calendar className="h-5 w-5 mr-2" />
                      Schedule Interviews for Selected Candidates ({selectedCount})
                    </>
                  )}
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;