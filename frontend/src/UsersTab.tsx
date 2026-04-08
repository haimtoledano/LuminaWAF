import React, { useState, useEffect, useCallback } from 'react';
import { Users, Plus, Trash2, Loader2 } from 'lucide-react';

interface User {
  id: string;
  username: string;
  role: 'admin' | 'viewer';
  mfa_enabled: boolean;
}

interface Props {
  authToken: string;
}

const UsersTab: React.FC<Props> = ({ authToken }) => {
  const [users, setUsers] = useState<User[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [newUsername, setNewUsername] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [newRole, setNewRole] = useState<'admin' | 'viewer'>('viewer');
  const [message, setMessage] = useState<{ text: string, type: 'success' | 'error' } | null>(null);

  const API_BASE_URL = 'http://localhost:8555/api/users';

  const fetchUsers = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await fetch(API_BASE_URL, {
        headers: { Authorization: `Bearer ${authToken}` },
      });
      if (!response.ok) throw new Error('Failed to fetch');
      const data = await response.json();
      setUsers(data);
    } catch (err: any) {
      setError('Failed to fetch user data. Please check the API endpoint.');
    } finally {
      setIsLoading(false);
    }
  }, [authToken]);

  useEffect(() => {
    fetchUsers();
  }, [fetchUsers]);

  const handleDeleteUser = async (id: string, username: string) => {
    if (!window.confirm(`Are you sure you want to delete the user "${username}"?`)) return;

    try {
      const response = await fetch(`${API_BASE_URL}/${id}`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${authToken}` },
      });
      if (!response.ok) {
          const err = await response.json();
          throw new Error(err.detail || 'Delete failed');
      }
      setMessage({ text: `${username} successfully deleted.`, type: 'success' });
      fetchUsers();
    } catch (err: any) {
      setMessage({ text: `Error deleting user: ${err.message}`, type: 'error' });
    }
  };

  const handleCreateUser = async (e: React.FormEvent) => {
    e.preventDefault();

    if (newPassword.length < 4) {
      setMessage({ text: 'Password must be at least 4 characters long.', type: 'error' });
      return;
    }

    try {
      const response = await fetch(API_BASE_URL, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${authToken}`,
        },
        body: JSON.stringify({ username: newUsername, password: newPassword, role: newRole })
      });
      
      if (!response.ok) {
          const err = await response.json();
          throw new Error(err.detail || 'Creation failed');
      }
      setMessage({ text: `User ${newUsername} created successfully!`, type: 'success' });
      fetchUsers();
      setNewUsername('');
      setNewPassword('');
      setNewRole('viewer');
    } catch (err: any) {
      setMessage({ text: err.message, type: 'error' });
    }
  };

  const renderMessage = () => {
    if (!message) return null;
    const typeClasses = message.type === 'success'
      ? 'bg-green-100 border-l-4 border-green-500 text-green-700'
      : 'bg-red-100 border-l-4 border-red-500 text-red-700';

    return (
      <div className={`p-3 rounded-md mb-4 flex items-center ${typeClasses}`}>
        <span className="text-sm">{message.text}</span>
      </div>
    );
  };

  return (
    <div className="p-6 bg-slate-800 shadow-lg rounded-xl flex-1 text-slate-200">
      <h1 className="text-3xl font-bold mb-6 flex items-center">
        <Users className="w-8 h-8 mr-3 text-indigo-400" />
        User Management Dashboard
      </h1>

      {renderMessage()}

      <div className="mb-8 p-6 border border-slate-700 rounded-lg bg-slate-900/50">
        <h2 className="text-xl font-semibold mb-4 flex items-center text-indigo-300">
          <Plus className="w-5 h-5 mr-2" /> Create New User
        </h2>
        <form onSubmit={handleCreateUser} className="grid grid-cols-1 md:grid-cols-5 gap-4 items-end">
          <div className="col-span-2">
            <label className="block text-sm font-medium mb-1">Username</label>
            <input
              type="text"
              value={newUsername}
              onChange={(e) => setNewUsername(e.target.value)}
              className="mt-1 block w-full px-3 py-2 border border-slate-600 bg-slate-800 rounded-md focus:outline-none focus:border-indigo-500"
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Password</label>
            <input
              type="password"
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              className="mt-1 block w-full px-3 py-2 border border-slate-600 bg-slate-800 rounded-md focus:outline-none focus:border-indigo-500"
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Role</label>
            <select
              value={newRole}
              onChange={(e) => setNewRole(e.target.value as 'admin' | 'viewer')}
              className="mt-1 block w-full px-3 py-2 border border-slate-600 bg-slate-800 rounded-md focus:outline-none focus:border-indigo-500"
            >
              <option value="viewer">Viewer</option>
              <option value="admin">Admin</option>
            </select>
          </div>
          <button
            type="submit"
            className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm font-medium text-white bg-indigo-600 hover:bg-indigo-500"
          >
            Create
          </button>
        </form>
      </div>

      <div>
        <h2 className="text-2xl font-bold mb-4">Existing Users</h2>
        {isLoading && !error && (
          <div className="flex justify-center h-48 items-center">
            <Loader2 className="w-8 h-8 mr-3 text-indigo-400 animate-spin" />
            <span>Loading...</span>
          </div>
        )}
        {error && <div className="text-red-400 mb-4">{error}</div>}
        {!isLoading && !error && (
          <div className="overflow-x-auto border border-slate-700 rounded-lg">
            <table className="min-w-full divide-y divide-slate-700">
              <thead className="bg-slate-900/50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-slate-400">Username</th>
                  <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-slate-400">Role</th>
                  <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-slate-400">MFA</th>
                  <th className="px-6 py-3 text-right text-xs font-medium uppercase tracking-wider text-slate-400">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-700">
                {users.map((user) => (
                  <tr key={user.id} className="hover:bg-slate-700/30">
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">{user.username}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      <span className={`px-2 py-1 inline-flex text-xs leading-5 font-semibold rounded-full ${user.role === 'admin' ? 'bg-red-900/30 text-red-400 border border-red-500/30' : 'bg-blue-900/30 text-blue-400 border border-blue-500/30'}`}>
                        {user.role}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      {user.mfa_enabled ? <span className="text-green-400">Enabled</span> : <span className="text-slate-500">Disabled</span>}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm">
                      <button onClick={() => handleDeleteUser(user.id, user.username)} className="text-red-400 hover:text-red-300">
                        <Trash2 className="w-5 h-5 inline" />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};
export default UsersTab;
