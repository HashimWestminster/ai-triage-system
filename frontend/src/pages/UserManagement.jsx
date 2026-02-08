import { useState, useEffect } from 'react';
import { getUsers } from '../services/api';
import { Search, UserPlus } from 'lucide-react';

export default function UserManagement() {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [roleFilter, setRoleFilter] = useState('');
  const [search, setSearch] = useState('');

  useEffect(() => {
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
        <h1 className="text-2xl font-bold text-gray-900">User Administration</h1>
        <span className="text-sm text-gray-500">{users.length} users total</span>
      </div>

      {/* Filters */}
      <div className="flex items-center gap-3 mb-4">
        <div className="flex items-center gap-2 bg-white border rounded-lg px-3 py-2">
          <Search className="w-4 h-4 text-gray-400" />
          <input value={search} onChange={(e) => setSearch(e.target.value)}
            placeholder="Search by name..." className="outline-none text-sm w-48" />
        </div>
        <select value={roleFilter} onChange={(e) => setRoleFilter(e.target.value)}
          className="bg-white border rounded-lg px-3 py-2 text-sm">
          <option value="">All roles</option>
          <option value="patient">Patients</option>
          <option value="clinician">Clinicians</option>
          <option value="admin">Administrators</option>
        </select>
      </div>

      {/* Users table - mimicking Klinik user admin */}
      <div className="bg-white rounded-xl shadow-sm border overflow-hidden">
        <table className="w-full">
          <thead className="bg-gray-50 border-b">
            <tr>
              <th className="text-left px-4 py-3 text-xs font-semibold text-emerald-600 uppercase">First name</th>
              <th className="text-left px-4 py-3 text-xs font-semibold text-emerald-600 uppercase">Username</th>
              <th className="text-left px-4 py-3 text-xs font-semibold text-emerald-600 uppercase">Role</th>
              <th className="text-left px-4 py-3 text-xs font-semibold text-emerald-600 uppercase">Status</th>
              <th className="text-left px-4 py-3 text-xs font-semibold text-emerald-600 uppercase">Last Login</th>
            </tr>
          </thead>
          <tbody className="divide-y">
            {loading ? (
              <tr><td colSpan={5} className="px-4 py-8 text-center text-gray-500">Loading...</td></tr>
            ) : filtered.map(u => (
              <tr key={u.id} className="hover:bg-gray-50">
                <td className="px-4 py-3 text-sm font-medium text-gray-900">{u.full_name}</td>
                <td className="px-4 py-3 text-sm text-gray-600">{u.username}</td>
                <td className="px-4 py-3">
                  <span className={`text-xs font-medium px-2.5 py-1 rounded-full ${
                    u.role === 'admin' ? 'bg-purple-100 text-purple-800' :
                    u.role === 'clinician' ? 'bg-blue-100 text-blue-800' :
                    'bg-gray-100 text-gray-800'
                  }`}>
                    {u.role}
                  </span>
                </td>
                <td className="px-4 py-3">
                  <span className={`text-xs font-medium ${u.is_active ? 'text-green-600' : 'text-red-600'}`}>
                    {u.is_active ? 'Active' : 'Inactive'}
                  </span>
                </td>
                <td className="px-4 py-3 text-sm text-gray-500">
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
