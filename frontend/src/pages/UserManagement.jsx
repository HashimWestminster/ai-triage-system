// UserManagement.jsx - user list page for navigators and superusers
// shows all registered users with their roles and last login

import { useState, useEffect } from 'react';
import { getUsers } from '../services/api';
import { Search } from 'lucide-react';

const ROLE_LABELS = {
  patient: 'Patient',
  clinician: 'Clinician',
  care_navigator: 'Care Navigator',
  superuser: 'Site Admin',
};

const ROLE_COLORS = {
  superuser: 'bg-purple-50 text-purple-700 ring-1 ring-purple-200',
  care_navigator: 'bg-teal-50 text-teal-700 ring-1 ring-teal-200',
  clinician: 'bg-blue-50 text-blue-700 ring-1 ring-blue-200',
  patient: 'bg-gray-100 text-gray-600',
};

export default function UserManagement() {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [roleFilter, setRoleFilter] = useState('');
  const [search, setSearch] = useState('');

  useEffect(() => {
    setLoading(true);
    getUsers(roleFilter || undefined)
      .then(({ data }) => setUsers(data))
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [roleFilter]);

  const filtered = search
    ? users.filter(u =>
        u.full_name?.toLowerCase().includes(search.toLowerCase()) ||
        u.username?.toLowerCase().includes(search.toLowerCase())
      )
    : users;

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">User Management</h1>
          <p className="text-sm text-gray-500 mt-0.5">{users.length} registered users</p>
        </div>
      </div>

      {/* Filters */}
      <div className="flex items-center gap-3 mb-4">
        <div className="flex items-center gap-2 bg-white border border-gray-200 rounded-xl px-3 py-2">
          <Search className="w-4 h-4 text-gray-400" />
          <input value={search} onChange={(e) => setSearch(e.target.value)}
            placeholder="Search by name..." className="outline-none text-sm w-48 bg-transparent" />
        </div>
        <select value={roleFilter} onChange={(e) => setRoleFilter(e.target.value)}
          className="bg-white border border-gray-200 rounded-xl px-3 py-2 text-sm focus:ring-2 focus:ring-emerald-500 outline-none">
          <option value="">All roles</option>
          <option value="patient">Patients</option>
          <option value="clinician">Clinicians</option>
          <option value="care_navigator">Care Navigators</option>
          <option value="superuser">Site Admins</option>
        </select>
      </div>

      {/* Table */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
        <table className="w-full">
          <thead className="bg-gray-50/80 border-b border-gray-200">
            <tr>
              <th className="text-left px-5 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wider">Name</th>
              <th className="text-left px-5 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wider">Username</th>
              <th className="text-left px-5 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wider">Role</th>
              <th className="text-left px-5 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wider">Status</th>
              <th className="text-left px-5 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wider">Last Login</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {loading ? (
              <tr><td colSpan={5} className="px-5 py-12 text-center text-gray-400">Loading...</td></tr>
            ) : filtered.length === 0 ? (
              <tr><td colSpan={5} className="px-5 py-12 text-center text-gray-400">No users found</td></tr>
            ) : filtered.map(u => (
              <tr key={u.id} className="hover:bg-gray-50/50 transition">
                <td className="px-5 py-3.5 text-sm font-medium text-gray-900">{u.full_name}</td>
                <td className="px-5 py-3.5 text-sm text-gray-500">{u.username}</td>
                <td className="px-5 py-3.5">
                  <span className={`text-xs font-medium px-2.5 py-1 rounded-full ${ROLE_COLORS[u.role] || 'bg-gray-100 text-gray-600'}`}>
                    {ROLE_LABELS[u.role] || u.role}
                  </span>
                </td>
                <td className="px-5 py-3.5">
                  <span className={`inline-flex items-center gap-1.5 text-xs font-medium ${u.is_active ? 'text-green-600' : 'text-red-600'}`}>
                    <span className={`w-1.5 h-1.5 rounded-full ${u.is_active ? 'bg-green-500' : 'bg-red-500'}`} />
                    {u.is_active ? 'Active' : 'Inactive'}
                  </span>
                </td>
                <td className="px-5 py-3.5 text-sm text-gray-500">
                  {u.last_login ? new Date(u.last_login).toLocaleString('en-GB') : 'Never'}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
