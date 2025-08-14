import React, { useState, useEffect } from 'react';
import { adminAPI, authService } from '../services/api';
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
  
  // Platform Statistics state
  const [platformStats, setPlatformStats] = useState({});
  const [apiUsageStats, setApiUsageStats] = useState({});
  const [errorLogs, setErrorLogs] = useState([]);
  const [rateLimitData, setRateLimitData] = useState({});
  const [hourlyData, setHourlyData] = useState([]);
  const [statsTimeframe, setStatsTimeframe] = useState(24); // hours
  const [statsLoading, setStatsLoading] = useState(false);
  
  // Advanced User Management state
  const [searchQuery, setSearchQuery] = useState('');
  const [roleFilter, setRoleFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [selectedUser, setSelectedUser] = useState(null);
  const [userActivityOpen, setUserActivityOpen] = useState(false);
  const [userActivity, setUserActivity] = useState(null);
  const [filteredUsers, setFilteredUsers] = useState([]);
  
  // New User Modal state
  const [newUserOpen, setNewUserOpen] = useState(false);
  const [newUserData, setNewUserData] = useState({
    email: '',
    full_name: '',
    password: '',
    role: 'user'
  });
  
  // Notification state
  const [notification, setNotification] = useState({
    show: false,
    type: '', // 'success', 'error', 'info'
    title: '',
    message: ''
  });
  
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

  // Load statistics when stats section is active
  useEffect(() => {
    if (activeSection === 'stats') {
      loadStatisticsData(statsTimeframe);
    }
  }, [activeSection, statsTimeframe]);

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

  const loadStatisticsData = async (hours = 24) => {
    try {
      setStatsLoading(true);
      const [
        platformOverview,
        apiUsage,
        errors,
        rateLimits,
        hourlyRequests
      ] = await Promise.all([
        adminAPI.getPlatformOverview(),
        adminAPI.getApiUsageStats(hours),
        adminAPI.getErrorLogs(hours),
        adminAPI.getRateLimitData(hours),
        adminAPI.getHourlyRequestData(hours)
      ]);
      
      setPlatformStats(platformOverview);
      setApiUsageStats(apiUsage);
      setErrorLogs(errors);
      setRateLimitData(rateLimits);
      setHourlyData(hourlyRequests);
    } catch (err) {
      console.error('Failed to load statistics:', err);
      showNotification('error', 'Error', 'Failed to load statistics data');
    } finally {
      setStatsLoading(false);
    }
  };

  const generateSampleData = async () => {
    try {
      setStatsLoading(true);
      showNotification('info', 'Info', 'Generating sample data...');
      
      const response = await fetch(`http://localhost:8000/admin/statistics/generate-sample-data`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('authToken')}`,
          'Content-Type': 'application/json',
        },
      });
      
      if (response.ok) {
        showNotification('success', 'Success', 'Sample data generated successfully');
        // Reload statistics after generating sample data
        await loadStatisticsData(statsTimeframe);
      } else {
        throw new Error('Failed to generate sample data');
      }
    } catch (err) {
      console.error('Failed to generate sample data:', err);
      showNotification('error', 'Error', 'Failed to generate sample data');
    } finally {
      setStatsLoading(false);
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

  // Advanced User Management Functions
  const handleSearch = async () => {
    try {
      setIsLoading(true);
      const searchResults = await adminAPI.searchUsers(
        searchQuery.trim(),
        roleFilter || null,
        statusFilter || null,
        100
      );
      setFilteredUsers(searchResults);
      setError('');
    } catch (err) {
      setError('Erreur lors de la recherche');
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  const clearSearch = () => {
    setSearchQuery('');
    setRoleFilter('');
    setStatusFilter('');
    setFilteredUsers([]);
  };

  // Notification helper function
  const showNotification = (type, title, message) => {
    setNotification({
      show: true,
      type,
      title,
      message
    });
    
    // Auto-hide notification after 5 seconds
    setTimeout(() => {
      setNotification(prev => ({ ...prev, show: false }));
    }, 5000);
  };

  const handleViewActivity = async (userId) => {
    try {
      setIsLoading(true);
      const activityData = await adminAPI.getUserActivity(userId, 30);
      setUserActivity(activityData);
      setSelectedUser(users.find(u => u.id === userId));
      setUserActivityOpen(true);
      setError('');
    } catch (err) {
      setError('Erreur lors du chargement de l\'activité');
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleCreateUser = async () => {
    if (!newUserData.email || !newUserData.full_name || !newUserData.password) {
      setError('Veuillez remplir tous les champs requis');
      return;
    }

    if (newUserData.password.length < 6) {
      setError('Le mot de passe doit contenir au moins 6 caractères');
      return;
    }

    try {
      await authService.register(newUserData);
      setNewUserData({ email: '', full_name: '', password: '', role: 'user' });
      setNewUserOpen(false);
      await loadAdminData(); // Reload data to show new user
      setError('');
      showNotification('success', 'Success!', 'User created successfully');
    } catch (err) {
      showNotification('error', 'Error', 'Failed to create user: ' + err.message);
      console.error(err);
    }
  };

  const handleSuspendUser = async (userId) => {
    if (window.confirm('Êtes-vous sûr de vouloir suspendre cet utilisateur ?')) {
      try {
        await adminAPI.suspendUser(userId);
        await loadAdminData();
        setError('');
      } catch (err) {
        setError('Erreur lors de la suspension');
        console.error(err);
      }
    }
  };

  const handleActivateUser = async (userId) => {
    try {
      await adminAPI.activateUser(userId);
      await loadAdminData();
      setError('');
    } catch (err) {
      setError('Erreur lors de l\'activation');
      console.error(err);
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
        showNotification('success', 'File Deleted', `${filename} has been successfully deleted from ${folderName} folder`);
      } catch (err) {
        showNotification('error', 'Delete Failed', `Failed to delete ${filename}: ${err.message}`);
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
      <div className="stats-header">
        <div className="stats-title-section">
          <h1>Platform Statistics</h1>
          <p className="stats-date">
            Last updated: {new Date().toLocaleString('fr-FR')}
          </p>
        </div>
        <div className="stats-controls">
          <select
            value={statsTimeframe}
            onChange={(e) => setStatsTimeframe(parseInt(e.target.value))}
            className="stats-timeframe-select"
          >
            <option value={1}>Last Hour</option>
            <option value={24}>Last 24 Hours</option>
            <option value={168}>Last Week</option>
            <option value={720}>Last Month</option>
          </select>
          <button
            onClick={() => loadStatisticsData(statsTimeframe)}
            className="stats-refresh-btn"
            disabled={statsLoading}
          >
            {statsLoading ? 'Loading...' : '🔄 Refresh'}
          </button>
          <button
            onClick={generateSampleData}
            className="stats-sample-data-btn"
            disabled={statsLoading}
          >
            📊 Generate Sample Data
          </button>
          <button
            onClick={async () => {
              try {
                setStatsLoading(true);
                const response = await fetch('http://localhost:8000/admin/statistics/generate-sample-data', {
                  method: 'POST',
                  headers: {
                    'Authorization': `Bearer ${localStorage.getItem('authToken')}`,
                    'Content-Type': 'application/json'
                  }
                });
                if (response.ok) {
                  showNotification('success', 'Success', 'Sample data generated successfully');
                  loadStatisticsData(statsTimeframe);
                } else {
                  throw new Error('Failed to generate sample data');
                }
              } catch (err) {
                showNotification('error', 'Error', 'Failed to generate sample data');
              } finally {
                setStatsLoading(false);
              }
            }}
            className="stats-refresh-btn"
            disabled={statsLoading}
            style={{ background: '#28a745' }}
          >
            🎲 Generate Sample Data
          </button>
        </div>
      </div>

      {statsLoading ? (
        <div className="stats-loading">
          <div className="loading-spinner"></div>
          <p>Loading statistics...</p>
        </div>
      ) : (
        <>
          {/* Platform Overview */}
          <div className="stats-overview">
            <h2>Platform Overview</h2>
            <div className="stats-grid">
              <div className="stat-card primary">
                <div className="stat-icon">👥</div>
                <div className="stat-content">
                  <h3>{platformStats.overview?.total_users || 0}</h3>
                  <p>Total Users</p>
                  <span className="stat-subtext">{platformStats.overview?.active_users_24h || 0} active today</span>
                </div>
              </div>
              <div className="stat-card success">
                <div className="stat-icon">📊</div>
                <div className="stat-content">
                  <h3>{platformStats.overview?.total_requests_24h || 0}</h3>
                  <p>Requests (24h)</p>
                  <span className="stat-subtext">{platformStats.overview?.avg_requests_per_minute || 0}/min</span>
                </div>
              </div>
              <div className="stat-card info">
                <div className="stat-icon">✅</div>
                <div className="stat-content">
                  <h3>{platformStats.overview?.success_rate_24h || 0}%</h3>
                  <p>Success Rate</p>
                  <span className="stat-subtext">Last 24 hours</span>
                </div>
              </div>
              <div className="stat-card warning">
                <div className="stat-icon">🤖</div>
                <div className="stat-content">
                  <h3>{platformStats.overview?.total_gemini_tokens_24h || 0}</h3>
                  <p>AI Tokens Used</p>
                  <span className="stat-subtext">Gemini API</span>
                </div>
              </div>
            </div>
          </div>

          {/* API Usage Statistics */}
          <div className="stats-section-api">
            <h2>API Usage Analytics</h2>
            <div className="stats-cards-row">
              <div className="stats-card-detailed">
                <h3>Request Statistics</h3>
                <div className="stats-table-container">
                  <table className="stats-table">
                    <tbody>
                      <tr>
                        <td>Total Requests</td>
                        <td>{apiUsageStats.total_requests || 0}</td>
                      </tr>
                      <tr>
                        <td>Requests/Minute</td>
                        <td>{apiUsageStats.requests_per_minute || 0}</td>
                      </tr>
                      <tr>
                        <td>Avg Response Time</td>
                        <td>{apiUsageStats.avg_response_time_ms || 0}ms</td>
                      </tr>
                      <tr>
                        <td>Success Rate</td>
                        <td>{apiUsageStats.success_rate || 0}%</td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </div>
              
              <div className="stats-card-detailed">
                <h3>Top Endpoints</h3>
                <div className="stats-list">
                  {apiUsageStats.top_endpoints?.slice(0, 5).map((endpoint, index) => (
                    <div key={index} className="stats-list-item">
                      <span className="endpoint-name">{endpoint.endpoint}</span>
                      <span className="endpoint-count">{endpoint.count}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>

          {/* Rate Limiting Dashboard */}
          <div className="stats-section-rate-limits">
            <h2>Rate Limiting Dashboard</h2>
            <div className="stats-cards-row">
              <div className="stats-card-alert">
                <h3>Rate Limit Events</h3>
                <div className="alert-stat">
                  <span className="alert-number">{rateLimitData.total_events || 0}</span>
                  <span className="alert-text">Events in last {statsTimeframe}h</span>
                </div>
              </div>
              
              <div className="stats-card-detailed">
                <h3>Top Rate-Limited IPs</h3>
                <div className="stats-list">
                  {rateLimitData.top_ips?.slice(0, 5).map((ip, index) => (
                    <div key={index} className="stats-list-item">
                      <span className="ip-address">{ip.ip}</span>
                      <span className="ip-count">{ip.count} events</span>
                    </div>
                  ))}
                </div>
              </div>
              
              <div className="stats-card-detailed">
                <h3>Rate Limit Types</h3>
                <div className="stats-list">
                  {rateLimitData.events_by_type?.map((type, index) => (
                    <div key={index} className="stats-list-item">
                      <span className="limit-type">{type.type}</span>
                      <span className="limit-count">{type.count}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>

          {/* Error Logs */}
          <div className="stats-section-errors">
            <h2>Recent Error Logs</h2>
            <div className="error-logs-container">
              {errorLogs.length === 0 ? (
                <p className="no-errors">No errors in the selected timeframe ✅</p>
              ) : (
                <div className="error-logs-list">
                  {errorLogs.slice(0, 10).map((error, index) => (
                    <div key={error.id} className="error-log-item">
                      <div className="error-header">
                        <span className="error-type">{error.error_type}</span>
                        <span className="error-time">
                          {new Date(error.created_at).toLocaleString('fr-FR')}
                        </span>
                      </div>
                      <div className="error-details">
                        <p className="error-message">{error.error_message}</p>
                        {error.endpoint && (
                          <span className="error-endpoint">Endpoint: {error.endpoint}</span>
                        )}
                        {error.user_email && (
                          <span className="error-user">User: {error.user_email}</span>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Recent Activity */}
          <div className="stats-section-activity">
            <h2>Recent Platform Activity</h2>
            <div className="stats-cards-row">
              <div className="stats-card-detailed">
                <h3>Most Active Users</h3>
                <div className="stats-list">
                  {platformStats.top_users_24h?.map((user, index) => (
                    <div key={index} className="stats-list-item">
                      <span className="user-email">{user.email}</span>
                      <span className="user-requests">{user.count} requests</span>
                    </div>
                  ))}
                </div>
              </div>
              
              <div className="stats-card-detailed">
                <h3>Quick Stats</h3>
                <div className="quick-stats">
                  <div className="quick-stat">
                    <span className="quick-stat-number">{platformStats.overview?.total_requests_1h || 0}</span>
                    <span className="quick-stat-label">Requests (1h)</span>
                  </div>
                  <div className="quick-stat">
                    <span className="quick-stat-number">{platformStats.overview?.total_requests_7d || 0}</span>
                    <span className="quick-stat-label">Requests (7d)</span>
                  </div>
                  <div className="quick-stat">
                    <span className="quick-stat-number">{rateLimitData.total_events || 0}</span>
                    <span className="quick-stat-label">Rate Limits</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );

  const renderUsersSection = () => {
    const displayUsers = filteredUsers.length > 0 ? filteredUsers : users;
    
    return (
      <div className="users-section">
        <div className="overview-header">
          <h1>Users Management</h1>
          <div className="header-actions">
            <button onClick={() => setNewUserOpen(true)} className="add-btn-table">
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
          Advanced user management with search, filtering, and activity tracking
        </div>

        {/* Search and Filter Controls */}
        <div className="user-controls">
          <div className="search-section">
            <div className="search-input-group">
              <input
                type="text"
                placeholder="Search by name or email..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="search-input"
              />
              <button onClick={handleSearch} className="search-btn">
                🔍
              </button>
            </div>
            
            <div className="filter-group">
              <select
                value={roleFilter}
                onChange={(e) => setRoleFilter(e.target.value)}
                className="filter-select"
              >
                <option value="">All Roles</option>
                <option value="admin">Admin</option>
                <option value="user">User</option>
              </select>
              
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                className="filter-select"
              >
                <option value="">All Status</option>
                <option value="active">Active</option>
                <option value="inactive">Inactive</option>
              </select>
            </div>
            
            {(searchQuery || roleFilter || statusFilter) && (
              <button onClick={clearSearch} className="clear-btn">
                Clear Filters
              </button>
            )}
          </div>
        </div>

        <div className="users-table-container">
          <table className="users-table">
            <thead>
              <tr>
                <th>
                  <div className="header-content">User Name</div>
                </th>
                <th>
                  <div className="header-content">Email Address</div>
                </th>
                <th>
                  <div className="header-content">Created At</div>
                </th>
                <th>Role</th>
                <th>Status</th>
                <th>Last Login</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {displayUsers.map((user, index) => (
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
                    <select
                      value={user.role}
                      onChange={(e) => handleRoleChange(user.id, e.target.value)}
                      className={`role-select ${user.role.toLowerCase()}`}
                    >
                      <option value="user">User</option>
                      <option value="admin">Admin</option>
                    </select>
                  </td>
                  <td className="status-cell">
                    <span className={`status-badge ${user.is_active ? 'active' : 'inactive'}`}>
                      {user.is_active ? 'Active' : 'Inactive'}
                    </span>
                  </td>
                  <td className="login-cell">
                    {user.last_login 
                      ? new Date(user.last_login).toLocaleDateString('fr-FR')
                      : 'Never'
                    }
                  </td>
                  <td className="actions-cell">
                    <div className="user-actions">
                      <button
                        onClick={() => handleViewActivity(user.id)}
                        className="action-btn view-activity"
                        title="View Activity"
                      >
                        📊
                      </button>
                      
                      {user.is_active ? (
                        <button
                          onClick={() => handleSuspendUser(user.id)}
                          className="action-btn suspend"
                          title="Suspend User"
                        >
                          ⛔
                        </button>
                      ) : (
                        <button
                          onClick={() => handleActivateUser(user.id)}
                          className="action-btn activate"
                          title="Activate User"
                        >
                          ✅
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          
          {displayUsers.length === 0 && (
            <div className="no-users">
              <p>No users found matching your criteria</p>
            </div>
          )}
        </div>

        {/* User Activity Modal */}
        {userActivityOpen && userActivity && (
          <div className="modal-overlay" onClick={() => setUserActivityOpen(false)}>
            <div className="modal-content activity-modal" onClick={(e) => e.stopPropagation()}>
              <div className="modal-header">
                <h3>User Activity - {userActivity.user.full_name}</h3>
                <button
                  className="modal-close"
                  onClick={() => setUserActivityOpen(false)}
                >
                  ×
                </button>
              </div>
              <div className="modal-body">
                <div className="activity-summary">
                  <h4>Summary ({userActivity.period})</h4>
                  <div className="summary-stats">
                    <div className="stat-item">
                      <span className="stat-label">Chat Sessions:</span>
                      <span className="stat-value">{userActivity.summary.chat_sessions}</span>
                    </div>
                    <div className="stat-item">
                      <span className="stat-label">Messages Sent:</span>
                      <span className="stat-value">{userActivity.summary.messages_sent}</span>
                    </div>
                    <div className="stat-item">
                      <span className="stat-label">Last Login:</span>
                      <span className="stat-value">
                        {userActivity.summary.last_login 
                          ? new Date(userActivity.summary.last_login).toLocaleString('fr-FR')
                          : 'Never'
                        }
                      </span>
                    </div>
                  </div>
                </div>
                
                <div className="recent-sessions">
                  <h4>Recent Sessions</h4>
                  {userActivity.recent_sessions.length > 0 ? (
                    <div className="sessions-list">
                      {userActivity.recent_sessions.map((session, index) => (
                        <div key={index} className="session-item">
                          <div className="session-info">
                            <span className="session-title">{session.title}</span>
                            <span className="session-date">
                              {new Date(session.created_at).toLocaleString('fr-FR')}
                            </span>
                          </div>
                          <div className="session-details">
                            <span className="message-count">{session.message_count} messages</span>
                            {session.has_document_context && <span className="doc-badge">📄</span>}
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p>No recent sessions</p>
                  )}
                </div>
              </div>
              <div className="modal-footer">
                <button
                  className="btn-primary"
                  onClick={() => setUserActivityOpen(false)}
                >
                  Close
                </button>
              </div>
            </div>
          </div>
        )}

        {/* New User Modal */}
        {newUserOpen && (
          <div className="modal-overlay" onClick={() => setNewUserOpen(false)}>
            <div className="modal-content new-user-modal" onClick={(e) => e.stopPropagation()}>
              <div className="modal-header">
                <h3>Create New User</h3>
                <button
                  className="modal-close"
                  onClick={() => setNewUserOpen(false)}
                >
                  ×
                </button>
              </div>
              <div className="modal-body">
                <div className="form-group">
                  <label>Full Name</label>
                  <input
                    type="text"
                    placeholder="Enter full name"
                    value={newUserData.full_name}
                    onChange={(e) => setNewUserData({...newUserData, full_name: e.target.value})}
                    className="form-input"
                  />
                </div>
                <div className="form-group">
                  <label>Email Address</label>
                  <input
                    type="email"
                    placeholder="Enter email address"
                    value={newUserData.email}
                    onChange={(e) => setNewUserData({...newUserData, email: e.target.value})}
                    className="form-input"
                  />
                </div>
                <div className="form-group">
                  <label>Password</label>
                  <input
                    type="password"
                    placeholder="Enter password (min 6 characters)"
                    value={newUserData.password}
                    onChange={(e) => setNewUserData({...newUserData, password: e.target.value})}
                    className="form-input"
                  />
                </div>
                <div className="form-group">
                  <label>Role</label>
                  <select
                    value={newUserData.role}
                    onChange={(e) => setNewUserData({...newUserData, role: e.target.value})}
                    className="form-select"
                  >
                    <option value="user">User</option>
                    <option value="admin">Admin</option>
                  </select>
                </div>
              </div>
              <div className="modal-footer">
                <button
                  className="btn-secondary"
                  onClick={() => setNewUserOpen(false)}
                >
                  Cancel
                </button>
                <button
                  className="btn-primary"
                  onClick={handleCreateUser}
                  disabled={!newUserData.email || !newUserData.full_name || !newUserData.password || newUserData.password.length < 6}
                >
                  Create User
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    );
  };

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
            className="secure-folder-upload-btn"
            onClick={() => setUploadModalOpen(true)}
          >
            � Upload PDF CVs
          </button>
          <button 
            className="secure-folder-permissions-btn"
            onClick={() => setPermissionsModalOpen(true)}
          >
            🔐 Manage User Permissions
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

      {/* Custom Notification */}
      {notification.show && (
        <div className={`notification-toast ${notification.type}`}>
          <div className="notification-content">
            <div className="notification-icon">
              {notification.type === 'success' && '✅'}
              {notification.type === 'error' && '❌'}
              {notification.type === 'info' && 'ℹ️'}
            </div>
            <div className="notification-text">
              <div className="notification-title">{notification.title}</div>
              <div className="notification-message">{notification.message}</div>
            </div>
            <button 
              className="notification-close"
              onClick={() => setNotification(prev => ({ ...prev, show: false }))}
            >
              ×
            </button>
          </div>
        </div>
      )}

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
