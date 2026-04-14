// CaseDetailPage.jsx - shows the full detail of a triage case
// different sections show depending on the users role:
//   - everyone sees the patient info, symptoms, and AI prediction
//   - clinicians get a form to make their triage decision
//   - navigators/superusers get a form to close the case
// the AI panel shows confidence, rationale, and differential diagnoses

import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { getCaseDetail, clinicianDecide, navigatorCloseCase } from '../services/api';
import { useAuth } from '../context/AuthContext';
import {
  AlertCircle, CheckCircle, Brain,
  User, FileText, Activity, ArrowLeft
} from 'lucide-react';

const urgencyConfig = {
  emergency: { label: 'Emergency (999/A&E)', color: 'bg-red-50 text-red-800 border-red-200', icon: 'bg-red-500', dotClass: 'bg-red-500' },
  urgent: { label: 'Urgent (1-2 days)', color: 'bg-amber-50 text-amber-800 border-amber-200', icon: 'bg-amber-500', dotClass: 'bg-amber-500' },
  routine: { label: 'Routine (2-3 weeks)', color: 'bg-green-50 text-green-800 border-green-200', icon: 'bg-green-500', dotClass: 'bg-green-500' },
  self_care: { label: 'Non-urgent / Self-care', color: 'bg-blue-50 text-blue-800 border-blue-200', icon: 'bg-blue-500', dotClass: 'bg-blue-500' },
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

  const [decision, setDecision] = useState('');
  const [clinicianNotes, setClinicianNotes] = useState('');
  const [closureReason, setClosureReason] = useState('');
  const [closureNotes, setClosureNotes] = useState('');

  const isStaff = user?.role !== 'patient';
  const canDecide = user?.role === 'clinician';
  const canClose = user?.role === 'care_navigator' || user?.role === 'superuser';

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

  const handleClose = async () => {
    if (!closureReason) return alert('Please select a closure reason.');
    try {
      const { data } = await navigatorCloseCase(id, {
        closure_reason: closureReason,
        closure_notes: closureNotes,
      });
      setCaseData(data);
    } catch (err) {
      alert('Failed to close case.');
    }
  };

  if (loading) return <div className="text-center py-12 text-gray-400">Loading case...</div>;
  if (!caseData) return <div className="text-center py-12 text-red-500">Case not found</div>;

  const aiUrg = urgencyConfig[caseData.ai_urgency] || {};
  const clinUrg = urgencyConfig[caseData.clinician_urgency] || {};

  return (
    <div>
      {/* Back */}
      <button onClick={() => navigate(-1)}
        className="flex items-center gap-1.5 text-sm text-gray-400 hover:text-gray-600 mb-4 transition">
        <ArrowLeft className="w-4 h-4" /> Back to cases
      </button>

      {/* Header card */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 mb-4">
        <div className="flex items-start justify-between">
          <div>
            <h1 className="text-xl font-bold text-gray-900">{caseData.visit_type}</h1>
            <p className="text-sm text-gray-500 mt-1">
              Case: {caseData.case_number} &middot; {new Date(caseData.created_at).toLocaleString('en-GB')}
            </p>
          </div>
          <span className={`text-xs font-semibold px-3 py-1.5 rounded-full ${
            caseData.status === 'new' ? 'bg-blue-50 text-blue-700 ring-1 ring-blue-200' :
            caseData.status === 'in_progress' ? 'bg-amber-50 text-amber-700 ring-1 ring-amber-200' :
            caseData.status === 'decided' ? 'bg-purple-50 text-purple-700 ring-1 ring-purple-200' :
            'bg-gray-100 text-gray-600'
          }`}>
            {caseData.status.replace('_', ' ').toUpperCase()}
          </span>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Left: Patient info + symptoms */}
        <div className="lg:col-span-2 space-y-4">
          {/* Patient info - staff only */}
          {isStaff && caseData.patient && (
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-5">
              <h2 className="font-semibold text-gray-900 flex items-center gap-2 mb-3">
                <User className="w-5 h-5 text-emerald-600" /> Patient Information
              </h2>
              <div className="grid grid-cols-2 gap-3 text-sm">
                <div><span className="text-gray-400">Name:</span> <span className="font-medium text-gray-900">{caseData.patient.full_name}</span></div>
                <div><span className="text-gray-400">NHS Number:</span> <span className="font-medium">{caseData.patient.nhs_number || 'N/A'}</span></div>
                <div><span className="text-gray-400">Phone:</span> <span className="font-medium">{caseData.patient.phone_number || 'N/A'}</span></div>
                <div><span className="text-gray-400">Email:</span> <span className="font-medium">{caseData.patient.email}</span></div>
                <div><span className="text-gray-400">DOB:</span> <span className="font-medium">{caseData.patient.date_of_birth || 'N/A'}</span></div>
                <div><span className="text-gray-400">Postal Code:</span> <span className="font-medium">{caseData.patient.postal_code || 'N/A'}</span></div>
              </div>
            </div>
          )}

          {/* Symptoms */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-5">
            <h2 className="font-semibold text-gray-900 flex items-center gap-2 mb-3">
              <FileText className="w-5 h-5 text-emerald-600" /> Symptom Details
            </h2>
            <div className="space-y-3 text-sm">
              {caseData.body_location && (
                <div><span className="text-gray-400 font-medium">Location:</span> <span className="text-gray-700">{caseData.body_location}</span></div>
              )}
              {caseData.symptom_duration && (
                <div><span className="text-gray-400 font-medium">Duration:</span> <span className="text-gray-700">{caseData.symptom_duration}</span></div>
              )}
              {caseData.selected_symptoms?.length > 0 && (
                <div>
                  <span className="text-gray-400 font-medium">Selected Symptoms:</span>
                  <div className="flex flex-wrap gap-1.5 mt-1.5">
                    {caseData.selected_symptoms.map(s => (
                      <span key={s} className="bg-gray-100 text-gray-700 px-2.5 py-1 rounded-full text-xs">{s}</span>
                    ))}
                  </div>
                </div>
              )}
              {caseData.severity_symptoms?.length > 0 && (
                <div>
                  <span className="text-gray-400 font-medium">Severity Indicators:</span>
                  <div className="flex flex-wrap gap-1.5 mt-1.5">
                    {caseData.severity_symptoms.map(s => (
                      <span key={s} className="bg-amber-50 text-amber-700 ring-1 ring-amber-200 px-2.5 py-1 rounded-full text-xs">{s}</span>
                    ))}
                  </div>
                </div>
              )}
              <div>
                <span className="text-gray-400 font-medium">Description:</span>
                <p className="mt-1.5 bg-gray-50 p-3 rounded-lg text-gray-700 leading-relaxed">{caseData.symptoms_text || 'No description provided'}</p>
              </div>
              {caseData.additional_info && (
                <div>
                  <span className="text-gray-400 font-medium">Additional Info:</span>
                  <p className="mt-1 text-gray-700">{caseData.additional_info}</p>
                </div>
              )}
              <div className="flex gap-4 text-gray-600">
                <span>Previous treatment: <strong>{caseData.previous_treatment ? 'Yes' : 'No'}</strong></span>
                <span>Previously seen: <strong>{caseData.previously_seen ? 'Yes' : 'No'}</strong></span>
              </div>
            </div>
          </div>

          {/* Audit trail - staff only */}
          {isStaff && caseData.audit_logs?.length > 0 && (
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-5">
              <h2 className="font-semibold text-gray-900 mb-3">Audit Trail</h2>
              <div className="space-y-3">
                {caseData.audit_logs.map((log, i) => (
                  <div key={i} className="flex gap-3 text-sm">
                    <div className="w-2 h-2 rounded-full bg-emerald-400 mt-1.5 shrink-0" />
                    <div>
                      <div className="font-medium text-gray-700">{log.user_name} &mdash; {log.action.replace('_', ' ')}</div>
                      <div className="text-gray-500">{log.details}</div>
                      <div className="text-xs text-gray-400">{new Date(log.timestamp).toLocaleString('en-GB')}</div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Right column: AI + actions */}
        <div className="space-y-4">
          {/* AI Triage - staff only */}
          {isStaff && (
          <div className="space-y-4">
            <div className={`rounded-xl border p-5 ${aiUrg.color || 'bg-gray-50'}`}>
              <h2 className="font-semibold flex items-center gap-2 mb-3">
                <Brain className="w-5 h-5" /> AI Triage Suggestion
              </h2>
              <div className="flex items-center gap-2 mb-2">
                <span className={`w-3 h-3 rounded-full ${aiUrg.icon}`} />
                <span className="text-lg font-bold">{aiUrg.label}</span>
              </div>
              <div className="text-sm mb-2">
                Confidence: <strong>{Math.round((caseData.ai_confidence || 0) * 100)}%</strong>
              </div>
              <div className="w-full bg-black/10 rounded-full h-2 mb-3">
                <div className="h-2 rounded-full bg-current opacity-60 transition-all"
                  style={{ width: `${Math.round((caseData.ai_confidence || 0) * 100)}%` }} />
              </div>
              <p className="text-sm opacity-90 leading-relaxed">{caseData.ai_rationale}</p>

              {caseData.ai_differential?.length > 0 && (
                <div className="mt-4 pt-3 border-t border-black/10">
                  <span className="text-xs font-semibold uppercase tracking-wide">Possible conditions:</span>
                  <ul className="mt-1.5 space-y-1">
                    {caseData.ai_differential.map(d => (
                      <li key={d} className="text-sm flex items-start gap-1.5">
                        <span className="mt-1 w-1.5 h-1.5 rounded-full bg-current shrink-0 opacity-60" />
                        {d}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>

            {/* How the AI prediction works */}
            <div className="bg-white rounded-xl border border-gray-200 p-5">
              <h3 className="font-semibold text-gray-900 flex items-center gap-2 mb-3 text-sm">
                <AlertCircle className="w-4 h-4 text-emerald-600" /> How the AI Prediction Works
              </h3>
              <div className="text-xs text-gray-600 space-y-2 leading-relaxed">
                <p>
                  The AI triage engine uses a <strong>three-layer hybrid approach</strong> to
                  assess urgency. Each layer adds a level of clinical safety:
                </p>
                <ol className="list-decimal list-inside space-y-1.5 pl-1">
                  <li>
                    <strong>Safety Rules</strong> &mdash; Hard-coded red-flag detection based on
                    NHS Hospital Episode Statistics (HES) 2024-25 data. Symptoms such as
                    chest pain, breathing difficulty, or loss of consciousness are
                    immediately escalated regardless of what the machine-learning model suggests.
                  </li>
                  <li>
                    <strong>NLP Feature Extraction</strong> &mdash; Natural Language Processing
                    identifies symptom keywords, severity modifiers (e.g. &ldquo;severe&rdquo;,
                    &ldquo;sudden&rdquo;), body system affected, and symptom duration from the
                    patient&rsquo;s free-text description.
                  </li>
                  <li>
                    <strong>ML Classification</strong> &mdash; A Random Forest classifier
                    (trained on 291 symptom scenarios mapped to NHS HES admission data)
                    predicts the urgency level. The model uses TF-IDF vectorisation with
                    200 decision trees and class-balanced weighting.
                  </li>
                </ol>
                <p>
                  The three layers are combined: safety rules take highest priority, then
                  NLP severity modifiers adjust the ML prediction up or down. The
                  <strong> confidence score</strong> reflects how certain the model is &mdash;
                  scores below 60% indicate the case may not fit known patterns well.
                </p>
                <p>
                  <strong>Differential diagnoses</strong> are keyword-matched suggestions
                  (mapped to ICD-10 codes) intended to assist clinical reasoning &mdash;
                  they are not a definitive diagnosis.
                </p>
                <p className="text-gray-400 italic pt-1 border-t border-gray-100">
                  This AI assessment is advisory only. A qualified clinician must review
                  all cases before any clinical action is taken.
                </p>
              </div>
            </div>
          </div>
          )}

          {/* Patient sees simple status */}
          {!isStaff && (
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

          {/* Clinician decision display */}
          {caseData.clinician_urgency && (
            <div className={`rounded-xl border p-5 ${clinUrg.color || 'bg-gray-50'}`}>
              <h2 className="font-semibold mb-2">Clinician Decision</h2>
              <div className="flex items-center gap-2">
                <span className={`w-3 h-3 rounded-full ${clinUrg.dotClass}`} />
                <span className="text-lg font-bold">{clinUrg.label}</span>
              </div>
              <div className="text-sm mt-1">By: {caseData.clinician?.full_name}</div>
              {caseData.clinician_notes && <p className="text-sm mt-2 opacity-80">{caseData.clinician_notes}</p>}
            </div>
          )}

          {/* Clinician decision form */}
          {canDecide && caseData.status === 'new' && (
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-5">
              <h2 className="font-semibold mb-3">Make your assessment</h2>
              <p className="text-sm text-gray-500 mb-3">
                AI suggestion: <span className="font-medium text-emerald-600">{aiUrg.label}</span>
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
                className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:ring-2 focus:ring-emerald-500 outline-none mb-3" />
              <button onClick={handleClinicianDecide}
                className="w-full bg-emerald-600 text-white py-2.5 rounded-lg text-sm font-semibold hover:bg-emerald-700 transition">
                Submit Decision
              </button>
            </div>
          )}

          {/* Navigator closure form */}
          {canClose && caseData.status === 'decided' && (
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-5">
              <h2 className="font-semibold mb-3">Close Case</h2>
              <select value={closureReason} onChange={(e) => setClosureReason(e.target.value)}
                className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm mb-3 focus:ring-2 focus:ring-emerald-500 outline-none">
                <option value="">Select outcome...</option>
                {CLOSURE_REASONS.map(r => (
                  <option key={r.value} value={r.value}>{r.label}</option>
                ))}
              </select>
              <textarea value={closureNotes} onChange={(e) => setClosureNotes(e.target.value)}
                placeholder="Closure notes (optional)" rows={3}
                className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:ring-2 focus:ring-emerald-500 outline-none mb-3" />
              <button onClick={handleClose}
                className="w-full bg-emerald-600 text-white py-2.5 rounded-lg text-sm font-semibold hover:bg-emerald-700 transition">
                Close Case
              </button>
            </div>
          )}

          {/* Closed info */}
          {caseData.status === 'closed' && isStaff && (
            <div className="bg-gray-50 rounded-xl border border-gray-200 p-5">
              <h2 className="font-semibold mb-2 flex items-center gap-2">
                <CheckCircle className="w-5 h-5 text-green-600" /> Case Closed
              </h2>
              <div className="text-sm space-y-1 text-gray-600">
                <p><span className="text-gray-400">Outcome:</span> <strong>{caseData.closure_reason?.replace(/_/g, ' ')}</strong></p>
                {caseData.closure_notes && <p><span className="text-gray-400">Notes:</span> {caseData.closure_notes}</p>}
                <p><span className="text-gray-400">Closed by:</span> {caseData.admin_handler?.full_name}</p>
                <p><span className="text-gray-400">Closed at:</span> {new Date(caseData.closed_at).toLocaleString('en-GB')}</p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
