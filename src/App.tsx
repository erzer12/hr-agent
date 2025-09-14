import React, { useState, useEffect, useMemo } from 'react';
import DatePicker from 'react-datepicker';
import 'react-datepicker/dist/react-datepicker.css';
import { Upload, FileText, Calendar, Mail, Check, X, Star, Clock, User, Phone, MapPin, AlertCircle, CheckCircle, Loader2 } from 'lucide-react';

// Define a type for availability slots for better type safety
interface AvailabilitySlot {
  date: string; // e.g., "2025-09-15"
  slots: string[]; // e.g., ["09:00", "10:00"]
}

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
  const [calendarUrl, setCalendarUrl] = useState('');
  const [availability, setAvailability] = useState<AvailabilitySlot[]>([]);
  const [selectedCandidate, setSelectedCandidate] = useState<Candidate | null>(null);
  const [isSchedulingModalOpen, setIsSchedulingModalOpen] = useState(false);
  const [draftEmail, setDraftEmail] = useState('');
  const [selectedSlot, setSelectedSlot] = useState<string | null>(null);
  const [emailTemplate, setEmailTemplate] = useState('professional');
  const [selectedDate, setSelectedDate] = useState<Date | null>(null);
  const [selectedTime, setSelectedTime] = useState<string>('');

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [calendarResponse, availabilityResponse] = await Promise.all([
          fetch('/api/calendar'),
          fetch('/api/availability'),
        ]);
        
        if (!calendarResponse.ok || !availabilityResponse.ok) {
          throw new Error('Failed to fetch initial data');
        }
        
        const calendarData = await calendarResponse.json();
        const availabilityData = await availabilityResponse.json();
        setCalendarUrl(calendarData.calendar_url);
        setAvailability(availabilityData);
      } catch (error) {
        console.error("Error fetching initial data:", error);
        setStatus({
          isProcessing: false,
          isScheduling: false,
          message: 'Failed to load calendar data. Some features may not work.',
          type: 'error'
        });
      }
    };
    fetchData();
  }, []);

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

  const openSchedulingModal = async (candidate: Candidate) => {
    setSelectedCandidate(candidate);
    setIsSchedulingModalOpen(true);
    try {
      const response = await fetch('/api/availability');
      const data = await response.json();
      setAvailability(data);
    } catch (error) {
      console.error("Error fetching availability:", error);
    }
  };

  const handleScheduleInterview = async () => {
    if (!selectedCandidate || !selectedDate || !selectedTime) {
      setStatus({
        isProcessing: false,
        isScheduling: false,
        message: 'Please select a candidate, date and time',
        type: 'error'
      });
      return;
    }

    setStatus({
      isProcessing: false,
      isScheduling: true,
      message: `Scheduling interview for ${selectedCandidate.name}...`,
      type: 'info'
    });

    try {
      const startDateTime = new Date(selectedDate);
      const [hours, minutes] = selectedTime.split(':').map(Number);
      startDateTime.setHours(hours, minutes, 0, 0);
      const endDateTime = new Date(startDateTime);
      endDateTime.setMinutes(endDateTime.getMinutes() + 30);

      const response = await fetch('/api/schedule', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          candidate: selectedCandidate,
          start_time: startDateTime.toISOString(),
          end_time: endDateTime.toISOString(),
          template: emailTemplate,
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to schedule interview');
      }

      const data = await response.json();
      setStatus({
        isProcessing: false,
        isScheduling: false,
        message: data.message || 'Interview scheduled successfully!',
        type: 'success'
      });
      setIsSchedulingModalOpen(false);
      setSelectedCandidate(null);
      setSelectedSlot(null);
      setSelectedDate(null);
      setSelectedTime('');
      setDraftEmail('');
    } catch (error) {
      setStatus({
        isProcessing: false,
        isScheduling: false,
        message: 'Error scheduling interview. Please try again.',
        type: 'error'
      });
    }
  };
  
  // Memoize available slots for the selected date to prevent re-calculation
  const availableSlotsForSelectedDate = useMemo(() => {
    if (!selectedDate) return [];
    // Format the selected date to YYYY-MM-DD for comparison
    const dateString = selectedDate.toISOString().split('T')[0];
    const dayAvailability = availability.find(day => day.date === dateString);
    return dayAvailability ? dayAvailability.slots : [];
  }, [selectedDate, availability]);


  useEffect(() => {
    if (selectedDate && selectedTime && selectedCandidate) {
      const fetchDraft = async () => {
        try {
          const startDateTime = new Date(selectedDate);
          const [hours, minutes] = selectedTime.split(':').map(Number);
          startDateTime.setHours(hours, minutes, 0, 0);

          const response = await fetch('/api/draft_email', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({
              candidate: selectedCandidate,
              interview_details: {
                date: selectedDate.toLocaleDateString(),
                time: startDateTime.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
                timezone: 'EST',
                location: 'Remote via Google Meet', // Added location for MapPin
                meeting_link: 'TBD'
              },
              template: emailTemplate
            }),
          });
          const data = await response.json();
          setDraftEmail(data.draft);
        } catch (error) {
          console.error("Error fetching email draft:", error);
        }
      };
      fetchDraft();
    }
  }, [selectedDate, selectedTime, selectedCandidate, emailTemplate]);


  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50">
      <div className="container mx-auto px-6 py-8">
        {/* Header and Status Bar remain the same */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">HR AI Agent Dashboard</h1>
          <p className="text-gray-600">Autonomous resume screening and interview scheduling</p>
        </div>

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
          {/* Inputs Section remains the same */}
          <div className="space-y-6">
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

              {uploadedFiles.length > 0 && (
                <div className="mt-4 space-y-2">
                  <h3 className="font-medium text-gray-700">Uploaded Files ({uploadedFiles.length})</h3>
                  {uploadedFiles.map((file, index) => (
                    <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                      <div className="flex items-center min-w-0">
                        <FileText className="h-4 w-4 text-red-500 mr-2 flex-shrink-0" />
                        <span className="text-sm text-gray-700 truncate">{file.name}</span>
                      </div>
                      <button
                        onClick={() => removeFile(index)}
                        className="text-red-500 hover:text-red-700 p-1 ml-2"
                        disabled={status.isProcessing}
                      >
                        <X className="h-4 w-4" />
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </div>

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
            </h2>

            {candidates.length === 0 ? (
              <div className="text-center py-12">
                <User className="h-12 w-12 text-gray-300 mx-auto mb-4" />
                <p className="text-gray-500">No candidates processed yet.</p>
                <p className="text-sm text-gray-400 mt-1">Upload resumes and process them to see ranked candidates here.</p>
              </div>
            ) : (
              <div className="space-y-4 max-h-[500px] overflow-y-auto pr-2">
                {candidates.map((candidate) => (
                  <div
                    key={candidate.id}
                    // Card style changes when selected
                    className={`border rounded-lg p-4 transition-all ${
                        candidate.selected ? 'border-blue-500 bg-blue-50 shadow-md' : 'border-gray-200 hover:border-gray-300'
                    }`}
                  >
                    <div className="flex items-start justify-between">
                       <div className="flex items-start flex-1 min-w-0">
                          {/* Added selection button with Check icon */}
                          <button onClick={() => toggleCandidateSelection(candidate.id)} className={`mr-4 mt-1 flex-shrink-0 h-6 w-6 border-2 rounded ${candidate.selected ? 'bg-blue-600 border-blue-600 text-white' : 'border-gray-300 text-transparent'} flex items-center justify-center transition-colors`}>
                              <Check className="h-4 w-4" />
                          </button>
                          <div className="flex-1">
                            <h3 className="font-semibold text-gray-900">{candidate.name}</h3>
                            <div className="space-y-1 mt-2 mb-3">
                              <div className="flex items-center text-sm text-gray-600">
                                <Mail className="h-4 w-4 mr-2" />
                                <span className="truncate">{candidate.email}</span>
                              </div>
                              {candidate.phone && (
                                <div className="flex items-center text-sm text-gray-600">
                                  <Phone className="h-4 w-4 mr-2" />
                                  {candidate.phone}
                                </div>
                              )}
                            </div>

                            <div className="mb-3">
                              <div className="flex items-center justify-between mb-1">
                                <span className="text-sm font-medium text-gray-700">Match Score</span>
                                <span className="text-lg font-bold text-blue-600">{candidate.score}/100</span>
                              </div>
                              <div className="w-full bg-gray-200 rounded-full h-2">
                                <div
                                  className="bg-blue-600 h-2 rounded-full transition-all"
                                  style={{ width: `${candidate.score}%` }}
                                ></div>
                              </div>
                            </div>

                            <div>
                              <h4 className="text-sm font-medium text-gray-700 mb-2">Key Highlights:</h4>
                              <ul className="text-sm text-gray-600 space-y-1">
                                {candidate.summary.map((point, index) => (
                                  <li key={index} className="flex items-start">
                                    <span className="text-blue-500 mr-2 mt-1 flex-shrink-0">•</span>
                                    <span>{point}</span>
                                  </li>
                                ))}
                              </ul>
                            </div>
                          </div>
                       </div>
                      <button
                        onClick={() => openSchedulingModal(candidate)}
                        className="ml-4 flex-shrink-0 py-2 px-4 bg-emerald-600 text-white rounded-lg font-medium hover:bg-emerald-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors flex items-center justify-center"
                      >
                        <Calendar className="h-5 w-5 mr-2" />
                        Schedule
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {calendarUrl && (
          <div className="mt-8">
            <h2 className="text-xl font-semibold text-gray-900 mb-4 flex items-center">
              <Calendar className="h-5 w-5 mr-2 text-blue-600" />
              Interview Schedule
            </h2>
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
              <iframe
                src={calendarUrl}
                style={{ border: 0 }}
                width="100%"
                height="600"
                frameBorder="0"
                scrolling="no"
              ></iframe>
            </div>
          </div>
        )}

        {/* UPDATED Scheduling Modal */}
        {isSchedulingModalOpen && selectedCandidate && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
            <div className="bg-white rounded-xl shadow-2xl p-8 max-w-4xl w-full max-h-[90vh] overflow-y-auto">
              <h2 className="text-2xl font-bold text-gray-900 mb-6">Schedule Interview for {selectedCandidate.name}</h2>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                {/* Left side: Date, Time, Location */}
                <div>
                  <h3 className="font-semibold text-lg mb-4">1. Select Date & Time</h3>
                  <div className="mb-4">
                    <label className="block text-sm font-medium text-gray-700 mb-2">Date</label>
                    <DatePicker
                      selected={selectedDate}
                      onChange={(date) => {
                          setSelectedDate(date);
                          setSelectedTime(''); // Reset time when date changes
                          setSelectedSlot(null);
                      }}
                      minDate={new Date()}
                      highlightDates={availability.map(item => new Date(item.date))}
                      className="w-full p-2 border border-gray-300 rounded-lg"
                      placeholderText="Select interview date"
                      inline
                    />
                  </div>

                  <div className="mb-4">
                    <label className="block text-sm font-medium text-gray-700 mb-2 flex items-center">
                        <Clock className="h-4 w-4 mr-2" />
                        Available Times
                    </label>
                    <div className="grid grid-cols-3 gap-2 mt-2">
                        {availableSlotsForSelectedDate.length > 0 ? (
                            availableSlotsForSelectedDate.map(time => (
                                <button
                                    key={time}
                                    onClick={() => {
                                        setSelectedTime(time);
                                        setSelectedSlot(time);
                                    }}
                                    className={`p-2 border rounded-lg text-sm transition-colors ${
                                        selectedSlot === time ? 'bg-blue-600 text-white border-blue-600' : 'bg-gray-50 hover:bg-gray-100'
                                    }`}
                                >
                                    {new Date(`1970-01-01T${time}`).toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' })}
                                </button>
                            ))
                        ) : (
                            <p className="col-span-3 text-sm text-gray-500">{selectedDate ? 'No available slots for this date.' : 'Select a date to see times.'}</p>
                        )}
                    </div>
                  </div>
                   <div className="flex items-center text-sm text-gray-600 mt-6 p-3 bg-slate-50 rounded-lg">
                      <MapPin className="h-5 w-5 mr-3 text-gray-400 flex-shrink-0" />
                      <div>
                          <span className="font-medium">Interview Location:</span> Remote via Google Meet
                      </div>
                   </div>
                </div>
                {/* Right side: Email Template and Preview */}
                <div>
                  <h3 className="font-semibold text-lg mb-4">2. Review Invitation Email</h3>
                  <select
                    value={emailTemplate}
                    onChange={(e) => setEmailTemplate(e.target.value)}
                    className="w-full p-2 border border-gray-300 rounded-lg mb-4"
                  >
                    <option value="professional">Professional</option>
                    <option value="casual">Casual</option>
                    <option value="technical">Technical</option>
                  </select>
                  <textarea
                    value={draftEmail || 'Select a date and time to generate the email preview...'}
                    readOnly
                    className="w-full h-72 p-4 border border-gray-300 rounded-lg resize-none bg-gray-50 text-sm"
                  />
                </div>
              </div>
              <div className="mt-8 flex justify-end space-x-4">
                <button
                  onClick={() => setIsSchedulingModalOpen(false)}
                  className="py-2 px-4 bg-gray-200 text-gray-800 rounded-lg hover:bg-gray-300 transition-colors"
                >
                  Cancel
                </button>
                <button
                  onClick={handleScheduleInterview}
                  disabled={!selectedDate || !selectedTime || status.isScheduling}
                  className="py-2 px-6 bg-emerald-600 text-white rounded-lg font-medium hover:bg-emerald-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors flex items-center justify-center"
                >
                  {status.isScheduling ? (
                    <Loader2 className="h-5 w-5 mr-2 animate-spin" />
                  ) : (
                    <Mail className="h-5 w-5 mr-2" />
                  )}
                  {status.isScheduling ? 'Scheduling...' : 'Schedule & Send Invitation'}
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;