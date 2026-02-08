import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { getCaseDetail, clinicianDecide, adminCloseCase } from '../services/api';
import { useAuth } from '../context/AuthContext';
import {
  AlertCircle, AlertTriangle, CheckCircle, Clock, Brain,
  User, FileText, Activity, ArrowLeft
} from 'lucide-react';

const urgencyConfig = {
  emergency: { label: 'Emergency (999/A&E)', color: 'bg-red-100 text-red-800 border-red-200', icon: '🔴', dotClass: 'bg-red-500' },
  urgent: { label: 'Urgent (1-2 days)', color: 'bg-amber-100 text-amber-800 border-amber-200', icon: '🟠', dotClass: 'bg-amber-500' },
  routine: { label: 'Routine (2-3 weeks)', color: 'bg-green-100 text-green-800 border-green-200', icon: '🟢', dotClass: 'bg-green-500' },
  self_care: { label: 'Non-urgent / Self-care', color: 'bg-blue-100 text-blue-800 border-blue-200', icon: '🔵', dotClass: 'bg-blue-500' },
};

const CLOSURE_REASONS = [
  { value: 'appointment_booked', label: 'Appointment Booked' },
  { value: 'urgent_referral', label: 'Urgent Referral (A&E/999)' },
  { value: 'follow_up', label: 'Follow-up Appointment' },
  { value: 'self_care_advised', label: 'Self-care Advised' },
  { value: 'referred_111', label: '111 Referral' },
  { value: 'extended_access', label: 'Extended Access' },
  { value: 'no_contact_required', label: 'No Contact Required' },
  { value: 'message_sent', label: 'Message Sent to Patient' },
  { value: 'other', label: 'Other' },
];

export default function CaseDetailPage() {
  const { id } = useParams();
  const { user } = useAuth();
  const navigate = useNavigate();
  const [caseData, setCaseData] = useState(null);
  const [loading, setLoading] = useState(true);

  // Clinician form
  const [decision, setDecision] = useState('');
  const [clinicianNotes, setClinicianNotes] = useState('');

  // Admin form
  const [closureReason, setClosureReason] = useState('');
  const [closureNotes, setClosureNotes] = useState('');

  useEffect(() => {
    getCaseDetail(id)
      .then(({ data }) => setCaseData(data))
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [id]);

  const handleClinicianDecide = async () => {
    if (!decision) return alert('Please select an urgency level.');
    try {
      const { data } = await clinicianDecide(id, {
        clinician_urgency: decision,
        clinician_notes: clinicianNotes,
      });
      setCaseData(data);
    } catch (err) {
      alert('Failed to submit decision.');
    }
  };

  const handleAdminClose = async () => {
    if (!closureReason) return alert('Please select a closure reason.');
    try {
      const { data } = await adminCloseCase(id, {
        closure_reason: closureReason,
        closure_notes: closureNotes,
      });
      setCaseData(data);
    } catch (err) {
      alert('Failed to close case.');
    }
  };

  if (loading) return <div className="text-center py-12 text-gray-500">Loading case...</div>;
  if (!caseData) return <div className="text-center py-12 text-red-500">Case not found</div>;

  const aiUrg = urgencyConfig[caseData.ai_urgency] || {};
  const clinUrg = urgencyConfig[caseData.clinician_urgency] || {};

  return (
    <div>
      {/* Back button */}
      <button onClick={() => navigate(-1)}
        className="flex items-center gap-1 text-sm text-gray-500 hover:text-gray-700 mb-4">
        <ArrowLeft className="w-4 h-4" /> Back to cases
      </button>

      {/* Header */}
      <div className="bg-white rounded-xl shadow-sm border p-6 mb-4">
        <div className="flex items-start justify-between">
          <div>
            <h1 className="text-xl font-bold text-gray-900">
              {caseData.visit_type}
            </h1>
            <p className="text-sm text-gray-500 mt-1">
              Case: {caseData.case_number} · Created: {new Date(caseData.created_at).toLocaleString('en-GB')}
            </p>
          </div>
          <span className={`text-xs font-medium px-3 py-1.5 rounded-full ${
            caseData.status === 'new' ? 'bg-blue-100 text-blue-800' :
            caseData.status === 'in_progress' ? 'bg-amber-100 text-amber-800' :
            caseData.status === 'decided' ? 'bg-purple-100 text-purple-800' :
            'bg-gray-100 text-gray-800'
          }`}>
            {caseData.status.replace('_', ' ').toUpperCase()}
          </span>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Left column: Patient info + symptoms */}
        <div className="lg:col-span-2 space-y-4">
          {/* Patient info */}
          {user?.role !== 'patient' && caseData.patient && (
            <div className="bg-white rounded-xl shadow-sm border p-5">
              <h2 className="font-semibold text-gray-900 flex items-center gap-2 mb-3">
                <User className="w-5 h-5 text-emerald-600" /> Patient Information
              </h2>
              <div className="grid grid-cols-2 gap-3 text-sm">
                <div><span className="text-gray-500">Name:</span> <span className="font-medium">{caseData.patient.full_name}</span></div>
                <div><span className="text-gray-500">NHS Number:</span> <span className="font-medium">{caseData.patient.nhs_number || 'N/A'}</span></div>
                <div><span className="text-gray-500">Phone:</span> <span className="font-medium">{caseData.patient.phone_number || 'N/A'}</span></div>
                <div><span className="text-gray-500">Email:</span> <span className="font-medium">{caseData.patient.email}</span></div>
                <div><span className="text-gray-500">DOB:</span> <span className="font-medium">{caseData.patient.date_of_birth || 'N/A'}</span></div>
                <div><span className="text-gray-500">Postal Code:</span> <span className="font-medium">{caseData.patient.postal_code || 'N/A'}</span></div>
              </div>
            </div>
          )}

          {/* Symptoms */}
          <div className="bg-white rounded-xl shadow-sm border p-5">
            <h2 className="font-semibold text-gray-900 flex items-center gap-2 mb-3">
              <FileText className="w-5 h-5 text-emerald-600" /> Symptom Details
            </h2>
            <div className="space-y-3 text-sm">
              {caseData.body_location && (
                <div><span className="text-gray-500 font-medium">Location:</span> {caseData.body_location}</div>
              )}
              {caseData.symptom_duration && (
                <div><span className="text-gray-500 font-medium">Duration:</span> {caseData.symptom_duration}</div>
              )}
              {caseData.selected_symptoms?.length > 0 && (
                <div>
                  <span className="text-gray-500 font-medium">Selected Symptoms:</span>
                  <div className="flex flex-wrap gap-1.5 mt-1">
                    {caseData.selected_symptoms.map(s => (
                      <span key={s} className="bg-gray-100 px-2.5 py-1 rounded-full text-xs">{s}</span>
                    ))}
                  </div>
                </div>
              )}
              {caseData.severity_symptoms?.length > 0 && (
                <div>
                  <span className="text-gray-500 font-medium">Severity Indicators:</span>
                  <div className="flex flex-wrap gap-1.5 mt-1">
                    {caseData.severity_symptoms.map(s => (
                      <span key={s} className="bg-amber-50 text-amber-700 px-2.5 py-1 rounded-full text-xs">{s}</span>
                    ))}
                  </div>
                </div>
              )}
              <div>
                <span className="text-gray-500 font-medium">Description:</span>
                <p className="mt-1 bg-gray-50 p-3 rounded-lg">{caseData.symptoms_text || 'No description provided'}</p>
              </div>
              {caseData.additional_info && (
                <div>
                  <span className="text-gray-500 font-medium">Additional Info:</span>
                  <p className="mt-1">{caseData.additional_info}</p>
                </div>
              )}
              <div className="flex gap-4">
                <span>Previous treatment: <strong>{caseData.previous_treatment ? 'Yes' : 'No'}</strong></span>
                <span>Previously seen: <strong>{caseData.previously_seen ? 'Yes' : 'No'}</strong></span>
              </div>
            </div>
          </div>

          {/* Audit trail */}
          {user?.role !== 'patient' && caseData.audit_logs?.length > 0 && (
            <div className="bg-white rounded-xl shadow-sm border p-5">
              <h2 className="font-semibold text-gray-900 mb-3">Audit Trail</h2>
              <div className="space-y-3">
                {caseData.audit_logs.map((log, i) => (
                  <div key={i} className="flex gap-3 text-sm">
                    <div className="w-2 h-2 rounded-full bg-emerald-400 mt-1.5 shrink-0" />
                    <div>
                      <div className="font-medium text-gray-700">{log.user_name} — {log.action.replace('_', ' ')}</div>
                      <div className="text-gray-500">{log.details}</div>
                      <div className="text-xs text-gray-400">{new Date(log.timestamp).toLocaleString('en-GB')}</div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Right column: AI suggestion + Actions */}
        <div className="space-y-4">
          {/* AI Triage Suggestion — only visible to clinicians and admins */}
          {user?.role !== 'patient' && (
          <div className={`rounded-xl border p-5 ${aiUrg.color || 'bg-gray-50'}`}>
            <h2 className="font-semibold flex items-center gap-2 mb-3">
              <Brain className="w-5 h-5" /> AI Triage Suggestion
            </h2>
            <div className="text-2xl font-bold mb-2">{aiUrg.icon} {aiUrg.label}</div>
            <div className="text-sm mb-2">Confidence: <strong>{Math.round((caseData.ai_confidence || 0) * 100)}%</strong></div>
            <p className="text-sm opacity-90">{caseData.ai_rationale}</p>
            {caseData.ai_differential?.length > 0 && (
              <div className="mt-3">
                <span className="text-xs font-semibold uppercase">Possible conditions:</span>
                <ul className="mt-1 space-y-0.5">
                  {caseData.ai_differential.map(d => (
                    <li key={d} className="text-sm">• {d}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
          )}

          {/* Patient sees a simple status message instead */}
          {user?.role === 'patient' && (
          <div className="bg-emerald-50 rounded-xl border border-emerald-200 p-5">
            <h2 className="font-semibold flex items-center gap-2 mb-3 text-emerald-800">
              <Activity className="w-5 h-5" /> Case Status
            </h2>
            {caseData.status === 'new' && (
              <p className="text-sm text-emerald-700">Your case has been submitted and is awaiting review by a clinician. You will be contacted if further information is needed.</p>
            )}
            {caseData.status === 'in_progress' && (
              <p className="text-sm text-emerald-700">Your case is currently being reviewed by a clinician.</p>
            )}
            {caseData.status === 'decided' && (
              <p className="text-sm text-emerald-700">A clinician has reviewed your case. The practice will be in touch with next steps.</p>
            )}
            {caseData.status === 'closed' && (
              <p className="text-sm text-emerald-700">Your case has been closed. If you have further concerns, please submit a new case or contact the surgery.</p>
            )}
          </div>
          )}

          {/* Clinician decision */}
          {caseData.clinician_urgency && (
            <div className={`rounded-xl border p-5 ${clinUrg.color || 'bg-gray-50'}`}>
              <h2 className="font-semibold mb-2">Clinician Decision</h2>
              <div className="text-lg font-bold">{clinUrg.icon} {clinUrg.label}</div>
              <div className="text-sm mt-1">By: {caseData.clinician?.full_name}</div>
              {caseData.clinician_notes && <p className="text-sm mt-2">{caseData.clinician_notes}</p>}
            </div>
          )}

          {/* Clinician action form */}
          {user?.role === 'clinician' && caseData.status === 'new' && (
            <div className="bg-white rounded-xl shadow-sm border p-5">
              <h2 className="font-semibold mb-3">Give your estimate</h2>
              <p className="text-sm text-gray-500 mb-3">
                AI evaluation: <span className="font-medium text-emerald-600">{aiUrg.label}</span>
              </p>
              <div className="space-y-2 mb-4">
                {Object.entries(urgencyConfig).map(([key, cfg]) => (
                  <label key={key}
                    className={`flex items-center gap-3 p-3 rounded-lg border cursor-pointer transition ${
                      decision === key ? 'border-emerald-500 bg-emerald-50' : 'border-gray-200 hover:border-gray-300'
                    }`}>
                    <input type="radio" name="urgency" value={key}
                      checked={decision === key} onChange={() => setDecision(key)}
                      className="sr-only" />
                    <span className={`w-3 h-3 rounded-full ${cfg.dotClass}`} />
                    <span className="text-sm font-medium">{cfg.label}</span>
                  </label>
                ))}
              </div>
              <textarea value={clinicianNotes} onChange={(e) => setClinicianNotes(e.target.value)}
                placeholder="Clinical notes (optional)" rows={3}
                className="w-full px-3 py-2 border rounded-lg text-sm focus:ring-2 focus:ring-emerald-500 outline-none mb-3" />
              <button onClick={handleClinicianDecide}
                className="w-full bg-emerald-600 text-white py-2 rounded-lg text-sm font-medium hover:bg-emerald-700 transition">
                Submit Decision
              </button>
            </div>
          )}

          {/* Admin closure form */}
          {user?.role === 'admin' && caseData.status === 'decided' && (
            <div className="bg-white rounded-xl shadow-sm border p-5">
              <h2 className="font-semibold mb-3">Close Case</h2>
              <select value={closureReason} onChange={(e) => setClosureReason(e.target.value)}
                className="w-full px-3 py-2 border rounded-lg text-sm mb-3 focus:ring-2 focus:ring-emerald-500 outline-none">
                <option value="">Select outcome...</option>
                {CLOSURE_REASONS.map(r => (
                  <option key={r.value} value={r.value}>{r.label}</option>
                ))}
              </select>
              <textarea value={closureNotes} onChange={(e) => setClosureNotes(e.target.value)}
                placeholder="Closure notes (optional)" rows={3}
                className="w-full px-3 py-2 border rounded-lg text-sm focus:ring-2 focus:ring-emerald-500 outline-none mb-3" />
              <button onClick={handleAdminClose}
                className="w-full bg-emerald-600 text-white py-2 rounded-lg text-sm font-medium hover:bg-emerald-700 transition">
                Close Case
              </button>
            </div>
          )}

          {/* Closed info */}
          {caseData.status === 'closed' && (
            <div className="bg-gray-50 rounded-xl border p-5">
              <h2 className="font-semibold mb-2 flex items-center gap-2">
                <CheckCircle className="w-5 h-5 text-green-600" /> Case Closed
              </h2>
              <div className="text-sm space-y-1">
                <p><span className="text-gray-500">Outcome:</span> <strong>{caseData.closure_reason?.replace(/_/g, ' ')}</strong></p>
                {caseData.closure_notes && <p><span className="text-gray-500">Notes:</span> {caseData.closure_notes}</p>}
                <p><span className="text-gray-500">Closed by:</span> {caseData.admin_handler?.full_name}</p>
                <p><span className="text-gray-500">Closed at:</span> {new Date(caseData.closed_at).toLocaleString('en-GB')}</p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
