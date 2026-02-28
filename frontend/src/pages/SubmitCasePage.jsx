import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { submitCase, getSurgeryStatus } from '../services/api';
import { CheckCircle, ChevronRight, ChevronLeft, AlertCircle } from 'lucide-react';

const VISIT_TYPES = [
  'New medical issue', 'New back, bone, joint or muscle pain',
  'I have a routine update to an ongoing health problem',
  'Health problem - aged 5 years and under', 'Sick notes',
  'Mental health', "Women's health and contraception",
  'Medication', 'Test results - requested by the practice',
];

const BODY_LOCATIONS = [
  'Head', 'Neck', 'Chest', 'Abdomen', 'Back', 'Arms', 'Hands',
  'Legs', 'Feet', 'Skin (general)', 'No specific location',
];

const SYMPTOMS_BY_LOCATION = {
  Head: ['Headache', 'Dizziness', 'Vision changes', 'Ear pain', 'Sore throat', 'Difficulty swallowing', 'Nasal congestion', 'Nosebleed'],
  Chest: ['Chest pain', 'Shortness of breath', 'Cough', 'Palpitations', 'Wheezing'],
  Abdomen: ['Stomach pain', 'Nausea', 'Vomiting', 'Diarrhoea', 'Constipation', 'Bloating', 'Heartburn', 'Blood in stool'],
  Back: ['Lower back pain', 'Upper back pain', 'Stiffness', 'Numbness', 'Tingling'],
  Skin: ['Rash', 'Itching', 'Lump', 'Mole change', 'Wound', 'Swelling', 'Redness'],
  default: ['Pain', 'Swelling', 'Numbness', 'Weakness', 'Stiffness', 'Redness', 'Bruising'],
};

const SEVERITY_SYMPTOMS = [
  'Constant or frequently recurring intense pain',
  'Difficulty standing or severe weakness',
  'High fever (> 38\u00B0C)',
  'New ongoing confusion or decline in consciousness',
  'New weakness or paralysis of limb',
  'Painkiller does not help',
  'Self-care is not helping',
  'Severe headache',
  'Severe, constant feeling of nausea',
  'Sudden, constant dizziness',
  'Need for sick leave',
  'None of these',
];

const DURATIONS = ['Hours', '1-2 days', '3-7 days', '1-2 weeks', '2-4 weeks', '1-3 months', '3+ months'];

export default function SubmitCasePage() {
  const navigate = useNavigate();
  const [step, setStep] = useState(1);
  const [submitting, setSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [caseId, setCaseId] = useState(null);
  const [submitError, setSubmitError] = useState('');

  const [form, setForm] = useState({
    visit_type: '',
    body_location: '',
    symptom_duration: '',
    selected_symptoms: [],
    severity_symptoms: [],
    symptoms_text: '',
    additional_info: '',
    previous_treatment: false,
    previously_seen: false,
  });

  const toggleSymptom = (symptom) => {
    setForm(prev => ({
      ...prev,
      selected_symptoms: prev.selected_symptoms.includes(symptom)
        ? prev.selected_symptoms.filter(s => s !== symptom)
        : [...prev.selected_symptoms, symptom]
    }));
  };

  const toggleSeverity = (symptom) => {
    if (symptom === 'None of these') {
      setForm(prev => ({ ...prev, severity_symptoms: ['None of these'] }));
      return;
    }
    setForm(prev => ({
      ...prev,
      severity_symptoms: prev.severity_symptoms.includes(symptom)
        ? prev.severity_symptoms.filter(s => s !== symptom)
        : [...prev.severity_symptoms.filter(s => s !== 'None of these'), symptom]
    }));
  };

  const handleSubmit = async () => {
    setSubmitting(true);
    setSubmitError('');
    try {
      const { data } = await submitCase(form);
      setCaseId(data.id);
      setSubmitted(true);
    } catch (err) {
      const detail = err.response?.data?.detail;
      if (detail) {
        setSubmitError(detail);
      } else {
        setSubmitError('Failed to submit case. Please try again.');
      }
    } finally {
      setSubmitting(false);
    }
  };

  if (submitted) {
    return (
      <div className="max-w-lg mx-auto text-center py-12">
        <CheckCircle className="w-16 h-16 text-emerald-500 mx-auto mb-4" />
        <h2 className="text-2xl font-bold text-gray-900 mb-2">Case Submitted Successfully</h2>
        <p className="text-gray-500 mb-6">
          Your case has been received and triaged by our AI system.
          A clinician will review it shortly.
        </p>
        <div className="flex gap-3 justify-center">
          <button onClick={() => navigate('/patient')}
            className="px-6 py-2.5 bg-emerald-600 text-white rounded-xl font-semibold hover:bg-emerald-700 transition">
            View My Cases
          </button>
          <button onClick={() => navigate(`/patient/case/${caseId}`)}
            className="px-6 py-2.5 border border-gray-200 text-gray-700 rounded-xl font-semibold hover:bg-gray-50 transition">
            View This Case
          </button>
        </div>
      </div>
    );
  }

  const totalSteps = 6;
  const availableSymptoms = SYMPTOMS_BY_LOCATION[form.body_location] || SYMPTOMS_BY_LOCATION.default;

  return (
    <div className="max-w-2xl mx-auto">
      {/* Progress */}
      <div className="mb-6">
        <div className="flex justify-between text-sm text-gray-500 mb-2">
          <span>Step {step} of {totalSteps}</span>
          <span>{Math.round((step / totalSteps) * 100)}%</span>
        </div>
        <div className="h-2 bg-gray-200 rounded-full">
          <div className="h-2 bg-emerald-500 rounded-full transition-all"
            style={{ width: `${(step / totalSteps) * 100}%` }} />
        </div>
      </div>

      {/* Submit error banner */}
      {submitError && (
        <div className="flex items-start gap-3 bg-amber-50 border border-amber-200 text-amber-800 p-4 rounded-xl mb-4 text-sm">
          <AlertCircle className="w-5 h-5 shrink-0 mt-0.5" />
          <div>
            <p className="font-medium">Unable to submit</p>
            <p className="mt-0.5">{submitError}</p>
          </div>
        </div>
      )}

      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        {/* Step 1 */}
        {step === 1 && (
          <div>
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Select the nature of your visit</h2>
            <div className="grid grid-cols-2 gap-3">
              {VISIT_TYPES.map(type => (
                <button key={type} onClick={() => setForm(prev => ({ ...prev, visit_type: type }))}
                  className={`p-4 rounded-xl border text-sm text-left transition ${
                    form.visit_type === type
                      ? 'border-emerald-500 bg-emerald-50 text-emerald-700 ring-1 ring-emerald-200'
                      : 'border-gray-200 hover:border-gray-300 text-gray-700'
                  }`}>
                  {type}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Step 2 */}
        {step === 2 && (
          <div>
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Where is the problem located?</h2>
            <div className="grid grid-cols-3 gap-3 mb-6">
              {BODY_LOCATIONS.map(loc => (
                <button key={loc} onClick={() => setForm(prev => ({ ...prev, body_location: loc }))}
                  className={`p-3 rounded-xl border text-sm transition ${
                    form.body_location === loc
                      ? 'border-emerald-500 bg-emerald-50 text-emerald-700 ring-1 ring-emerald-200'
                      : 'border-gray-200 hover:border-gray-300 text-gray-700'
                  }`}>
                  {loc}
                </button>
              ))}
            </div>
            <h3 className="font-medium text-gray-900 mb-3">Duration of symptoms</h3>
            <div className="flex flex-wrap gap-2">
              {DURATIONS.map(d => (
                <button key={d} onClick={() => setForm(prev => ({ ...prev, symptom_duration: d }))}
                  className={`px-4 py-2 rounded-full text-sm transition ${
                    form.symptom_duration === d
                      ? 'bg-emerald-600 text-white'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}>
                  {d}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Step 3 */}
        {step === 3 && (
          <div>
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Select your symptoms</h2>
            <div className="flex flex-wrap gap-2">
              {availableSymptoms.map(s => (
                <button key={s} onClick={() => toggleSymptom(s)}
                  className={`px-4 py-2 rounded-full text-sm transition ${
                    form.selected_symptoms.includes(s)
                      ? 'bg-emerald-600 text-white'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}>
                  {s}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Step 4 */}
        {step === 4 && (
          <div>
            <h2 className="text-lg font-semibold text-gray-900 mb-2">Do any of these describe your current state?</h2>
            <p className="text-sm text-gray-500 mb-4">These help us assess urgency</p>
            <div className="flex flex-wrap gap-2">
              {SEVERITY_SYMPTOMS.map(s => (
                <button key={s} onClick={() => toggleSeverity(s)}
                  className={`px-4 py-2 rounded-full text-sm transition ${
                    form.severity_symptoms.includes(s)
                      ? s === 'None of these' ? 'bg-gray-500 text-white' : 'bg-amber-500 text-white'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}>
                  {s}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Step 5 */}
        {step === 5 && (
          <div>
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Describe your symptoms in detail</h2>
            <textarea value={form.symptoms_text}
              onChange={(e) => setForm(prev => ({ ...prev, symptoms_text: e.target.value }))}
              rows={5} placeholder="Please describe what you are experiencing..."
              className="w-full px-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-emerald-500 outline-none resize-none text-sm" />
            <p className="text-xs text-gray-400 mt-1">{form.symptoms_text.length} / 2000</p>

            <div className="mt-4">
              <label className="block text-sm font-medium text-gray-700 mb-2">Any additional information?</label>
              <textarea value={form.additional_info}
                onChange={(e) => setForm(prev => ({ ...prev, additional_info: e.target.value }))}
                rows={3} placeholder="Allergies, current medications, etc."
                className="w-full px-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-emerald-500 outline-none resize-none text-sm" />
            </div>
          </div>
        )}

        {/* Step 6 */}
        {step === 6 && (
          <div>
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Previous treatment</h2>
            <div className="space-y-4">
              <div>
                <p className="font-medium text-gray-700 mb-2">Have you used any medication or treatment for this?</p>
                <div className="flex gap-3">
                  <button onClick={() => setForm(prev => ({ ...prev, previous_treatment: true }))}
                    className={`px-6 py-2 rounded-lg border transition text-sm ${form.previous_treatment ? 'bg-emerald-600 text-white border-emerald-600' : 'border-gray-200 text-gray-700 hover:border-gray-300'}`}>
                    Yes
                  </button>
                  <button onClick={() => setForm(prev => ({ ...prev, previous_treatment: false }))}
                    className={`px-6 py-2 rounded-lg border transition text-sm ${!form.previous_treatment ? 'bg-emerald-600 text-white border-emerald-600' : 'border-gray-200 text-gray-700 hover:border-gray-300'}`}>
                    No
                  </button>
                </div>
              </div>
              <div>
                <p className="font-medium text-gray-700 mb-2">Have clinical staff already seen you for this?</p>
                <div className="flex gap-3">
                  <button onClick={() => setForm(prev => ({ ...prev, previously_seen: true }))}
                    className={`px-6 py-2 rounded-lg border transition text-sm ${form.previously_seen ? 'bg-emerald-600 text-white border-emerald-600' : 'border-gray-200 text-gray-700 hover:border-gray-300'}`}>
                    Yes
                  </button>
                  <button onClick={() => setForm(prev => ({ ...prev, previously_seen: false }))}
                    className={`px-6 py-2 rounded-lg border transition text-sm ${!form.previously_seen ? 'bg-emerald-600 text-white border-emerald-600' : 'border-gray-200 text-gray-700 hover:border-gray-300'}`}>
                    No
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Navigation */}
        <div className="flex justify-between mt-6 pt-4 border-t border-gray-100">
          <button onClick={() => setStep(s => Math.max(1, s - 1))} disabled={step === 1}
            className="flex items-center gap-1 px-4 py-2 text-sm text-gray-500 hover:text-gray-700 disabled:opacity-30 disabled:cursor-not-allowed transition">
            <ChevronLeft className="w-4 h-4" /> Previous
          </button>

          {step < totalSteps ? (
            <button onClick={() => setStep(s => s + 1)}
              className="flex items-center gap-1 px-6 py-2 bg-emerald-600 text-white rounded-xl text-sm font-semibold hover:bg-emerald-700 transition">
              Continue <ChevronRight className="w-4 h-4" />
            </button>
          ) : (
            <button onClick={handleSubmit} disabled={submitting || !form.symptoms_text}
              className="px-6 py-2 bg-emerald-600 text-white rounded-xl text-sm font-semibold hover:bg-emerald-700 transition disabled:opacity-50">
              {submitting ? 'Submitting...' : 'Submit Case'}
            </button>
          )}
        </div>
      </div>

      {/* Summary */}
      {step > 1 && (
        <div className="mt-4 bg-gray-50 rounded-xl border border-gray-200 p-4">
          <h3 className="text-sm font-semibold text-gray-700 mb-2">Summary</h3>
          <div className="text-sm text-gray-600 space-y-1">
            {form.visit_type && <p><span className="font-medium">Type:</span> {form.visit_type}</p>}
            {form.body_location && <p><span className="font-medium">Location:</span> {form.body_location}</p>}
            {form.symptom_duration && <p><span className="font-medium">Duration:</span> {form.symptom_duration}</p>}
            {form.selected_symptoms.length > 0 && (
              <p><span className="font-medium">Symptoms:</span> {form.selected_symptoms.join(', ')}</p>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
