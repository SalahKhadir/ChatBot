import React, { useState, useEffect } from 'react';
import { adminAPI } from '../services/api';
import './AdminPanel.css';

function AdminPanel({ onNavigate, isDarkMode }) {
  const [users, setUsers] = useState([]);
  const [stats, setStats] = useState({});
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');
  const [darkMode, setDarkMode] = useState(isDarkMode);
  const [viewMode, setViewMode] = useState('grid'); // 'grid' or 'list'
  const [messagesOpen, setMessagesOpen] = useState(false);
  const [activeSection, setActiveSection] = useState('overview'); // New state for navigation
  
  // Secure Folders Management state
  const [secureFolders, setSecureFolders] = useState([]);
  const [selectedFiles, setSelectedFiles] = useState([]);
  const [folderPermissions, setFolderPermissions] = useState([]);
  const [uploadModalOpen, setUploadModalOpen] = useState(false);
  const [permissionsModalOpen, setPermissionsModalOpen] = useState(false);
  const [selectedFolderName, setSelectedFolderName] = useState('CVs');

  useEffect(() => {
    loadAdminData();
  }, []);

  const loadAdminData = async () => {
    try {
      setIsLoading(true);
      const [usersData, statsData, foldersData, permissionsData] = await Promise.all([
        adminAPI.getAllUsers(),
        adminAPI.getPlatformStats(),
        adminAPI.getSecureFolders().catch(() => []), // Don't fail if folders endpoint isn't ready
        adminAPI.getSecureFolderPermissions().catch(() => [])
      ]);
      setUsers(usersData);
      setStats(statsData);
      setSecureFolders(foldersData);
      setFolderPermissions(permissionsData);
      setError('');
    } catch (err) {
      setError('Erreur lors du chargement des données admin');
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleRoleChange = async (userId, newRole) => {
    try {
      await adminAPI.updateUserRole(userId, newRole);
      await loadAdminData(); // Reload data
      setError('');
    } catch (err) {
      setError('Erreur lors de la mise à jour du rôle');
      console.error(err);
    }
  };

  const handleStatusChange = async (userId, isActive) => {
    try {
      await adminAPI.updateUserStatus(userId, isActive);
      await loadAdminData(); // Reload data
      setError('');
    } catch (err) {
      setError('Erreur lors de la mise à jour du statut');
      console.error(err);
    }
  };

  const handleDeleteUser = async (userId) => {
    if (window.confirm('Êtes-vous sûr de vouloir supprimer cet utilisateur ? Cette action est irréversible.')) {
      try {
        await adminAPI.deleteUser(userId);
        await loadAdminData(); // Reload data
        setError('');
      } catch (err) {
        setError('Erreur lors de la suppression');
        console.error(err);
      }
    }
  };

  // Secure Folder Management Functions
  const handleFileUpload = (event) => {
    const files = Array.from(event.target.files);
    // Filter to only allow PDF files
    const pdfFiles = files.filter(file => 
      file.type === 'application/pdf' || file.name.toLowerCase().endsWith('.pdf')
    );
    
    if (pdfFiles.length !== files.length) {
      setError('Only PDF files are allowed. Some files were filtered out.');
    }
    
    setSelectedFiles(pdfFiles);
  };

  const handleUploadToSecureFolder = async () => {
    if (selectedFiles.length === 0) {
      setError('Veuillez sélectionner des fichiers à télécharger');
      return;
    }

    try {
      await adminAPI.uploadToSecureFolder(selectedFiles, selectedFolderName);
      setSelectedFiles([]);
      setUploadModalOpen(false);
      await loadAdminData(); // Reload to get updated folder contents
      setError('');
    } catch (err) {
      setError('Erreur lors du téléchargement des fichiers');
      console.error(err);
    }
  };

  const handleDeleteFromSecureFolder = async (filename, folderName) => {
    if (window.confirm(`Êtes-vous sûr de vouloir supprimer ${filename} ?`)) {
      try {
        await adminAPI.deleteFromSecureFolder(filename, folderName);
        await loadAdminData(); // Reload to get updated folder contents
        setError('');
      } catch (err) {
        setError('Erreur lors de la suppression du fichier');
        console.error(err);
      }
    }
  };

  const handlePermissionChange = async (userId, hasAccess) => {
    try {
      await adminAPI.updateSecureFolderPermissions(userId, hasAccess);
      await loadAdminData(); // Reload to get updated permissions
      setError('');
    } catch (err) {
      setError('Erreur lors de la mise à jour des permissions');
      console.error(err);
    }
  };

  const handleNavigationChange = (section) => {
    setActiveSection(section);
  };

  const renderOverviewSection = () => (
    <div className="overview-section">
      <div className="overview-header">
        <h1>General Overview</h1>
        <p className="overview-date">
          {new Date().toLocaleDateString('fr-FR', { 
            month: 'long', 
            day: 'numeric' 
          })}
        </p>
      </div>
      
      <div className="platform-status">
        <h3>Platform Status</h3>
        <p>System is running smoothly</p>
      </div>

      <div className="recent-activity">
        <h3>Recent Activity</h3>
        <ul className="activity-list">
          <li className="activity-item">{stats.daily_queries || 0} queries today</li>
          <li className="activity-item">{stats.active_users || 0} active users</li>
          <li className="activity-item">System uptime: 99.9%</li>
        </ul>
      </div>

      <div className="quick-actions">
        <h3>Quick Actions</h3>
        <div className="actions-grid">
          <button 
            className="action-btn" 
            onClick={() => setActiveSection('users')}
          >
            Manage Users
          </button>
          <button 
            className="action-btn" 
            onClick={() => setActiveSection('stats')}
          >
            View Stats
          </button>
        </div>
      </div>
    </div>
  );

  const renderStatsSection = () => (
    <div className="stats-section">
      <div className="overview-header">
        <h1>Platform Statistics</h1>
        <p className="overview-date">
          {new Date().toLocaleDateString('fr-FR', { 
            month: 'long', 
            day: 'numeric' 
          })}
        </p>
      </div>
      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-icon">👥</div>
          <h3>{stats.total_users || 0}</h3>
          <p>Total Users</p>
        </div>
        <div className="stat-card">
          <div className="stat-icon">✅</div>
          <h3>{stats.active_users || 0}</h3>
          <p>Active Users</p>
        </div>
        <div className="stat-card">
          <div className="stat-icon">👨‍💼</div>
          <h3>{stats.admin_users || 0}</h3>
          <p>Administrators</p>
        </div>
        <div className="stat-card">
          <div className="stat-icon">💬</div>
          <h3>{stats.daily_queries || 0}</h3>
          <p>Daily Queries</p>
        </div>
        <div className="stat-card">
          <div className="stat-icon">⚡</div>
          <h3>{stats.ai_response_time || 0}ms</h3>
          <p>Avg Response Time</p>
        </div>
        <div className="stat-card">
          <div className="stat-icon">🎯</div>
          <h3>{stats.ai_accuracy || 0}%</h3>
          <p>AI Accuracy</p>
        </div>
      </div>
    </div>
  );

  const renderUsersSection = () => (
    <div className="users-section">
      <div className="overview-header">
        <h1>Users Management</h1>
        <div className="header-actions">
          <button className="add-btn-table">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <line x1="12" y1="5" x2="12" y2="19" />
              <line x1="5" y1="12" x2="19" y2="12" />
            </svg>
            Add New
          </button>
          <p className="overview-date">
            {new Date().toLocaleDateString('fr-FR', { 
              month: 'long', 
              day: 'numeric' 
            })}
          </p>
        </div>
      </div>
      
      <div className="table-subtitle">
        You can track your users and manage their roles here
      </div>

      <div className="users-table-container">
        <table className="users-table">
          <thead>
            <tr>
              <th>
                <div className="header-content">
                  User Name
                </div>
              </th>
              <th>
                <div className="header-content">
                  Email Address
                </div>
              </th>
              <th>
                <div className="header-content">
                  Created At
                </div>
              </th>
              <th>Role</th>
              <th>Activity Status</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {users.map((user, index) => (
              <tr key={user.id} className="table-row">
                <td className="user-name-cell">
                  <div className="user-info">
                    <div className="user-avatar">
                      {user.full_name.charAt(0).toUpperCase()}
                    </div>
                    <span>{user.full_name}</span>
                  </div>
                </td>
                <td className="email-cell">{user.email}</td>
                <td className="created-cell">
                  {new Date(user.created_at).toLocaleDateString('fr-FR', {
                    year: 'numeric',
                    month: 'short',
                    day: 'numeric'
                  })}
                </td>
                <td className="role-cell">
                  <span className={`role-badge ${user.role.toLowerCase()}`}>
                    {user.role === 'admin' ? 'Admin' : 'User'}
                  </span>
                </td>
                <td className="status-cell">
                  <div className="status-bar">
                    <div 
                      className={`status-fill ${user.is_active ? 'active' : 'inactive'}`}
                      style={{ 
                        width: user.is_active ? '100%' : '30%'
                      }}
                    ></div>
                  </div>
                </td>
                <td className="actions-cell">
                  <div className="checkbox-wrapper-25">
                    <input 
                      type="checkbox"
                      checked={user.is_active}
                      onChange={() => handleStatusChange(user.id, !user.is_active)}
                      title={user.is_active ? 'Deactivate user' : 'Activate user'}
                    />
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );

  const renderFoldersSection = () => (
    <div className="folders-section">
      <div className="overview-header">
        <h1>Secure CV Folder Management</h1>
        <p className="overview-date">
          {new Date().toLocaleDateString('fr-FR', { 
            month: 'long', 
            day: 'numeric' 
          })}
        </p>
      </div>

      {/* Quick Actions */}
      <div className="quick-actions">
        <h3>Folder Actions</h3>
        <div className="actions-grid">
          <button 
            className="action-btn upload-btn"
            onClick={() => setUploadModalOpen(true)}
          >
            � Upload PDF CVs
          </button>
          <button 
            className="action-btn permissions-btn"
            onClick={() => setPermissionsModalOpen(true)}
          >
            🔐 Manage User Permissions
          </button>
          <button 
            className="action-btn audit-btn"
          >
            � View Activity Log
          </button>
        </div>
      </div>

      {/* Secure Folders Display */}
      <div className="secure-folders-container">
        <h3>Current Folders & Contents</h3>
        {secureFolders.length > 0 ? (
          secureFolders.map((folder, index) => (
            <div key={index} className="secure-folder-card">
              <div className="folder-header">
                <div className="folder-info-header">
                  <span className="folder-icon">📁</span>
                  <div className="folder-details">
                    <h4>{folder.name || 'CVs'}</h4>
                    <p>{folder.files?.length || 0} file(s)</p>
                  </div>
                </div>
                <span className="folder-badge secure">Secure</span>
              </div>
              
              <div className="folder-contents">
                {folder.files && folder.files.length > 0 ? (
                  <div className="files-list">
                    {folder.files.map((file, fileIndex) => (
                      <div key={fileIndex} className="file-item">
                        <div className="file-info">
                          <span className="file-icon">�</span>
                          <div className="file-details">
                            <span className="file-name">{file.filename}</span>
                            <span className="file-size">{(file.size / 1024).toFixed(1)} KB</span>
                          </div>
                        </div>
                        <div className="file-actions">
                          <span className="file-date">
                            {new Date(file.uploaded_at).toLocaleDateString('fr-FR')}
                          </span>
                          <button 
                            className="delete-file-btn"
                            onClick={() => handleDeleteFromSecureFolder(file.filename, folder.name)}
                            title="Delete file"
                          >
                            🗑️
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="empty-folder">
                    <p>No files uploaded yet</p>
                  </div>
                )}
              </div>
            </div>
          ))
        ) : (
          <div className="no-folders">
            <p>No CV files uploaded yet. Upload PDF CVs to get started.</p>
          </div>
        )}
      </div>

      {/* User Permissions Overview */}
      <div className="permissions-overview">
        <h3>Access Permissions</h3>
        <div className="permissions-grid">
          {users.map(user => {
            const userPermission = folderPermissions.find(p => p.user_id === user.id);
            const hasAccess = userPermission ? userPermission.has_access : false;
            
            return (
              <div key={user.id} className="permission-item">
                <div className="user-info-permission">
                  <div className="user-avatar">{user.email[0].toUpperCase()}</div>
                  <div className="user-details">
                    <span className="user-name">{user.email}</span>
                    <span className="user-role">{user.role}</span>
                  </div>
                </div>
                <div className="permission-toggle">
                  <div className="checkbox-wrapper-25">
                    <input 
                      type="checkbox"
                      checked={hasAccess}
                      onChange={() => handlePermissionChange(user.id, !hasAccess)}
                      title={hasAccess ? 'Revoke access' : 'Grant access'}
                    />
                  </div>
                  <span className="permission-status">
                    {hasAccess ? 'Granted' : 'Denied'}
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Upload Modal */}
      {uploadModalOpen && (
        <div className="modal-overlay" onClick={() => setUploadModalOpen(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Upload PDF CVs to Secure Folder</h3>
              <button 
                className="modal-close"
                onClick={() => setUploadModalOpen(false)}
              >
                ×
              </button>
            </div>
            <div className="modal-body">
              <div className="folder-select">
                <label>Secure CV Folder:</label>
              </div>
              
              <div className="file-upload-area">
                <input
                  type="file"
                  id="secureFileInput"
                  multiple
                  accept=".pdf"
                  onChange={handleFileUpload}
                  style={{ display: 'none' }}
                />
                <label htmlFor="secureFileInput" className="upload-area">
                  <div className="upload-content">
                    <span className="upload-icon">�</span>
                    <p>Click to select PDF files or drag and drop</p>
                    <p className="upload-hint">Only PDF files are supported</p>
                  </div>
                </label>
                
                {selectedFiles.length > 0 && (
                  <div className="selected-files-preview">
                    <h4>Selected Files ({selectedFiles.length}):</h4>
                    {selectedFiles.map((file, index) => (
                      <div key={index} className="selected-file">
                        <span>{file.name}</span>
                        <span>{(file.size / 1024).toFixed(1)} KB</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
            <div className="modal-footer">
              <button 
                className="btn-secondary"
                onClick={() => setUploadModalOpen(false)}
              >
                Cancel
              </button>
              <button 
                className="btn-primary"
                onClick={handleUploadToSecureFolder}
                disabled={selectedFiles.length === 0}
              >
                Upload {selectedFiles.length} file(s)
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Permissions Modal */}
      {permissionsModalOpen && (
        <div className="modal-overlay" onClick={() => setPermissionsModalOpen(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Manage CV Analysis Permissions</h3>
              <button 
                className="modal-close"
                onClick={() => setPermissionsModalOpen(false)}
              >
                ×
              </button>
            </div>
            <div className="modal-body">
              <p>Grant or revoke access to CV analysis for each user:</p>
              <div className="permissions-list">
                {users.map(user => {
                  const userPermission = folderPermissions.find(p => p.user_id === user.id);
                  const hasAccess = userPermission ? userPermission.has_access : false;
                  
                  return (
                    <div key={user.id} className="permission-row">
                      <div className="user-info-modal">
                        <div className="user-avatar">{user.email[0].toUpperCase()}</div>
                        <div className="user-details-modal">
                          <span className="user-name">{user.email}</span>
                          <span className="user-role-badge role-{user.role}">{user.role}</span>
                        </div>
                      </div>
                      <div className="permission-control">
                        <div className="checkbox-wrapper-25">
                          <input 
                            type="checkbox"
                            checked={hasAccess}
                            onChange={() => handlePermissionChange(user.id, !hasAccess)}
                          />
                        </div>
                        <span className={`permission-label ${hasAccess ? 'granted' : 'denied'}`}>
                          {hasAccess ? '✅ Access Granted' : '❌ Access Denied'}
                        </span>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
            <div className="modal-footer">
              <button 
                className="btn-primary"
                onClick={() => setPermissionsModalOpen(false)}
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );

  const renderCurrentSection = () => {
    switch(activeSection) {
      case 'overview':
        return renderOverviewSection();
      case 'stats':
        return renderStatsSection();
      case 'users':
        return renderUsersSection();
      case 'folders':
        return renderFoldersSection();
      default:
        return renderOverviewSection();
    }
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('fr-FR', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const toggleDarkMode = () => {
    setDarkMode(!darkMode);
  };

  if (isLoading) {
    return (
      <div className={`app-container ${darkMode ? 'dark' : ''}`}>
        <div className="loading-spinner">
          <div className="spinner"></div>
          <p>Chargement des données admin...</p>
        </div>
      </div>
    );
  }

  return (
    <div className={`admin-panel-wrapper ${darkMode ? 'dark' : ''}`}>
      <div className={`app-container ${darkMode ? 'dark' : ''}`}>
      {/* App Header */}
      <div className="app-header">
        <div className="app-header-left">
          <span className="app-icon"></span>
          <p className="app-name">Admin Panel</p>
        </div>
        <div className="app-header-right">
          <button className={`mode-switch ${darkMode ? 'active' : ''}`} title="Switch Theme" onClick={toggleDarkMode}>
            <svg className="moon" fill="none" stroke="currentColor" strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" width="24" height="24" viewBox="0 0 24 24">
              <path d="M21 12.79A9 9 0 1111.21 3 7 7 0 0021 12.79z"></path>
            </svg>
          </button>
          <button className="notification-btn">
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="feather feather-bell">
              <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9" />
              <path d="M13.73 21a2 2 0 0 1-3.46 0" />
            </svg>
          </button>
          <button className="profile-btn" onClick={() => onNavigate && onNavigate('home')}>
            <span>Chat</span>
          </button>
        </div>
        <button className="messages-btn" onClick={() => setMessagesOpen(true)}>
          <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="feather feather-message-circle">
            <path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5z" />
          </svg>
        </button>
      </div>

      {/* App Content */}
      <div className="app-content">
        {/* Sidebar */}
        <div className="app-sidebar">
          <button 
            onClick={() => handleNavigationChange('overview')} 
            className={`app-sidebar-link ${activeSection === 'overview' ? 'active' : ''}`}
            title="General Overview"
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="feather feather-home">
              <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z" />
              <polyline points="9 22 9 12 15 12 15 22" />
            </svg>
          </button>
          <button 
            onClick={() => handleNavigationChange('stats')} 
            className={`app-sidebar-link ${activeSection === 'stats' ? 'active' : ''}`}
            title="Statistics"
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" fill="none" stroke="currentColor" strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" className="feather feather-pie-chart" viewBox="0 0 24 24">
              <path d="M21.21 15.89A10 10 0 118 2.83M22 12A10 10 0 0012 2v10z" />
            </svg>
          </button>
          <button 
            onClick={() => handleNavigationChange('users')} 
            className={`app-sidebar-link ${activeSection === 'users' ? 'active' : ''}`}
            title="Users Management"
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="feather feather-users">
              <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path>
              <circle cx="9" cy="7" r="4"></circle>
              <path d="m22 21-3-3m0 0-3-3m3 3 3 3m-3-3 3-3"></path>
            </svg>
          </button>
          <button 
            onClick={() => handleNavigationChange('folders')} 
            className={`app-sidebar-link ${activeSection === 'folders' ? 'active' : ''}`}
            title="Secure Folders"
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" fill="none" stroke="currentColor" strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" className="feather feather-folder" viewBox="0 0 24 24">
              <path d="M22 19a2 2 0 01-2 2H4a2 2 0 01-2-2V5a2 2 0 012-2h5l2 3h9a2 2 0 012 2z" />
            </svg>
          </button>
        </div>

        {/* Dynamic Content Section */}
        {renderCurrentSection()}
      </div>

      {error && (
        <div className="error-toast">
          {error}
        </div>
      )}
      </div>
    </div>
  );
}

export default AdminPanel;
