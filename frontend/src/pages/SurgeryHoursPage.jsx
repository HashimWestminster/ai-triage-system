// SurgeryHoursPage.jsx - lets the superuser configure when the surgery is open
// shows a grid with all 7 days, open/close times, and a "closed" toggle
// patients can only submit cases during these configured hours

import { useState, useEffect } from 'react';
import { getSurgeryHours, updateSurgeryHours } from '../services/api';
import { Clock, Save, CheckCircle } from 'lucide-react';

const DAY_NAMES = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];

const DEFAULT_HOURS = DAY_NAMES.map((_, i) => ({
  day_of_week: i,
  open_time: i < 5 ? '08:00' : i === 5 ? '09:00' : '00:00',
  close_time: i < 5 ? '18:00' : i === 5 ? '12:00' : '00:00',
  is_closed: i === 6,
}));

export default function SurgeryHoursPage() {
  const [hours, setHours] = useState(DEFAULT_HOURS);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    getSurgeryHours()
      .then(({ data }) => {
        if (data.length > 0) {
          // Merge fetched data with defaults so all 7 days are present
          const merged = DEFAULT_HOURS.map(d => {
            const found = data.find(h => h.day_of_week === d.day_of_week);
            return found ? { ...d, ...found } : d;
          });
          setHours(merged);
        }
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  const updateDay = (dayIndex, field, value) => {
    setHours(prev => prev.map(h =>
      h.day_of_week === dayIndex ? { ...h, [field]: value } : h
    ));
    setSaved(false);
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      await updateSurgeryHours(hours);
      setSaved(true);
      setTimeout(() => setSaved(false), 3000);
    } catch (err) {
      alert('Failed to save surgery hours.');
    } finally {
      setSaving(false);
    }
  };

  if (loading) return <div className="text-center py-12 text-gray-400">Loading surgery hours...</div>;

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Surgery Hours</h1>
          <p className="text-sm text-gray-500 mt-0.5">
            Configure when patients can submit triage cases. Outside these hours, the submission form is disabled.
          </p>
        </div>
      </div>

      <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
        <div className="px-5 py-4 border-b border-gray-100 bg-gray-50/50">
          <div className="grid grid-cols-12 gap-4 text-xs font-semibold text-gray-500 uppercase tracking-wider">
            <div className="col-span-3">Day</div>
            <div className="col-span-3">Opens</div>
            <div className="col-span-3">Closes</div>
            <div className="col-span-3">Closed all day</div>
          </div>
        </div>

        <div className="divide-y divide-gray-100">
          {hours.map((h) => (
            <div key={h.day_of_week}
              className={`grid grid-cols-12 gap-4 items-center px-5 py-4 transition ${
                h.is_closed ? 'bg-gray-50/80' : ''
              }`}>
              <div className="col-span-3">
                <span className={`text-sm font-medium ${h.is_closed ? 'text-gray-400' : 'text-gray-900'}`}>
                  {DAY_NAMES[h.day_of_week]}
                </span>
              </div>
              <div className="col-span-3">
                <input
                  type="time"
                  value={h.open_time?.slice(0, 5) || '08:00'}
                  onChange={(e) => updateDay(h.day_of_week, 'open_time', e.target.value)}
                  disabled={h.is_closed}
                  className="px-3 py-2 border border-gray-200 rounded-lg text-sm focus:ring-2 focus:ring-emerald-500 outline-none disabled:opacity-40 disabled:bg-gray-100 w-full"
                />
              </div>
              <div className="col-span-3">
                <input
                  type="time"
                  value={h.close_time?.slice(0, 5) || '18:00'}
                  onChange={(e) => updateDay(h.day_of_week, 'close_time', e.target.value)}
                  disabled={h.is_closed}
                  className="px-3 py-2 border border-gray-200 rounded-lg text-sm focus:ring-2 focus:ring-emerald-500 outline-none disabled:opacity-40 disabled:bg-gray-100 w-full"
                />
              </div>
              <div className="col-span-3">
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={h.is_closed}
                    onChange={(e) => updateDay(h.day_of_week, 'is_closed', e.target.checked)}
                    className="w-4 h-4 rounded border-gray-300 text-emerald-600 focus:ring-emerald-500"
                  />
                  <span className="text-sm text-gray-600">Closed</span>
                </label>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Save button */}
      <div className="mt-4 flex items-center gap-3">
        <button onClick={handleSave} disabled={saving}
          className="flex items-center gap-2 bg-emerald-600 text-white px-6 py-2.5 rounded-xl font-semibold hover:bg-emerald-700 transition disabled:opacity-50">
          {saving ? (
            <>
              <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
              </svg>
              Saving...
            </>
          ) : (
            <>
              <Save className="w-4 h-4" />
              Save Hours
            </>
          )}
        </button>
        {saved && (
          <span className="flex items-center gap-1.5 text-sm text-emerald-600 font-medium">
            <CheckCircle className="w-4 h-4" /> Saved successfully
          </span>
        )}
      </div>

      {/* Explanation */}
      <div className="mt-6 bg-blue-50 border border-blue-100 rounded-xl p-4">
        <p className="text-sm text-blue-700">
          <strong>How this works:</strong> Patients will only be able to submit new triage cases during
          the configured opening hours. If they try to submit outside these times, they will see a
          message telling them when the surgery opens next. Emergency cases should always be directed
          to 999 or A&amp;E regardless of surgery hours.
        </p>
      </div>
    </div>
  );
}
