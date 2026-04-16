import React, { useState, useEffect, useCallback, useRef } from 'react';
import {
  Box, Typography, Tabs, Tab, Paper, Table, TableBody, TableCell,
  TableContainer, TableHead, TableRow, Chip, Tooltip, IconButton,
  CircularProgress, Card, CardContent, Grid, Alert, Switch,
  Dialog, DialogTitle, DialogContent, DialogActions, TextField, Button,
} from '@mui/material';
import {
  Business as OrgIcon, People as UsersIcon, BarChart as StatsIcon,
  Shield as AdminBadge, LockReset as LockResetIcon,
} from '@mui/icons-material';
import { useNotification } from '../context_providers/NotificationContext';
import apiService from '../../utils/api.service';

const TIER_COLORS: Record<string, 'default' | 'primary' | 'secondary' | 'success'> = {
  free: 'default', starter: 'primary', professional: 'secondary', enterprise: 'success',
};

interface AdminOrg {
  id: string;
  name: string;
  slug: string;
  planTier: string;
  memberCount: number;
  isActive: boolean;
  createdAt: string;
}

interface AdminUser {
  id: string;
  firstName: string;
  lastName: string;
  email: string;
  orgId?: string;
  orgName?: string;
  orgRole: string;
  isSuperAdmin: boolean;
  isActive: boolean;
  status: string;
  createdAt: string;
}

interface SystemStats {
  totalOrganizations: number;
  totalUsers: number;
  activeUsers: number;
  entriesToday: number;
  totalProjects?: number;
  totalTimeEntries?: number;
}

interface StatCardProps {
  title: string;
  value: string | number;
  color?: string;
}

const StatCard: React.FC<StatCardProps> = ({ title, value, color }) => (
  <Card variant="outlined" sx={{ height: '100%' }}>
    <CardContent sx={{ textAlign: 'center', py: 3 }}>
      <Typography variant="h3" fontWeight={700} sx={{ color: color || 'primary.main', mb: 1 }}>
        {typeof value === 'number' ? value.toLocaleString() : value}
      </Typography>
      <Typography variant="body2" color="text.secondary" fontWeight={500}>
        {title}
      </Typography>
    </CardContent>
  </Card>
);

const GlobalAdminPage: React.FC = () => {
  const { showSuccess, showError } = useNotification();
  const [tab, setTab] = useState(0);

  // Stable refs for notification functions to avoid infinite useCallback/useEffect loops
  const showErrorRef = useRef(showError);
  showErrorRef.current = showError;
  const showSuccessRef = useRef(showSuccess);
  showSuccessRef.current = showSuccess;

  // Organizations
  const [orgs, setOrgs] = useState<AdminOrg[]>([]);
  const [orgsLoading, setOrgsLoading] = useState(false);

  // Users
  const [users, setUsers] = useState<AdminUser[]>([]);
  const [usersLoading, setUsersLoading] = useState(false);

  // Stats
  const [stats, setStats] = useState<SystemStats | null>(null);
  const [statsLoading, setStatsLoading] = useState(false);

  // Reset password dialog
  const [resetDialogOpen, setResetDialogOpen] = useState(false);
  const [resetTarget, setResetTarget] = useState<AdminUser | null>(null);
  const [newPassword, setNewPassword] = useState('');
  const [resetLoading, setResetLoading] = useState(false);

  const handleResetPassword = async () => {
    if (!resetTarget || !newPassword) return;
    setResetLoading(true);
    try {
      await apiService.superAdminResetPassword(resetTarget.id, newPassword);
      showSuccessRef.current(`Password reset for ${resetTarget.email}`);
      setResetDialogOpen(false);
      setNewPassword('');
      setResetTarget(null);
    } catch (err: any) {
      showErrorRef.current(err.message || 'Failed to reset password');
    } finally {
      setResetLoading(false);
    }
  };

  const loadOrgs = useCallback(async () => {
    setOrgsLoading(true);
    try {
      const res = await apiService.superAdminListOrgs();
      const data = res.data || res || [];
      setOrgs(Array.isArray(data) ? data : (data?.organizations || []));
    } catch (err: any) {
      showErrorRef.current('Failed to load organizations');
    } finally {
      setOrgsLoading(false);
    }
  }, []);

  const loadUsers = useCallback(async () => {
    setUsersLoading(true);
    try {
      const res = await apiService.superAdminListUsers();
      const data = res.data || res || [];
      setUsers(Array.isArray(data) ? data : (data?.users || []));
    } catch (err: any) {
      showErrorRef.current('Failed to load users');
    } finally {
      setUsersLoading(false);
    }
  }, []);

  const loadStats = useCallback(async () => {
    setStatsLoading(true);
    try {
      const res = await apiService.superAdminGetStats();
      setStats(res.data || res || null);
    } catch (err: any) {
      showErrorRef.current('Failed to load system stats');
    } finally {
      setStatsLoading(false);
    }
  }, []);

  useEffect(() => {
    loadOrgs();
    loadStats();
  }, [loadOrgs, loadStats]);

  useEffect(() => {
    if (tab === 1 && users.length === 0) loadUsers();
  }, [tab, users.length, loadUsers]);

  const handleToggleOrgActive = async (org: AdminOrg) => {
    try {
      await apiService.superAdminUpdateOrg(org.id, { isActive: !org.isActive });
      showSuccessRef.current(`${org.name} ${org.isActive ? 'deactivated' : 'activated'}`);
      loadOrgs();
    } catch (err: any) {
      showErrorRef.current(err.message || 'Failed to update organization');
    }
  };

  const handleToggleUserActive = async (user: AdminUser) => {
    try {
      await apiService.superAdminToggleUser(user.id);
      showSuccessRef.current(`${user.firstName} ${user.lastName} ${user.isActive ? 'deactivated' : 'activated'}`);
      loadUsers();
    } catch (err: any) {
      showErrorRef.current(err.message || 'Failed to update user');
    }
  };

  return (
    <Box sx={{ p: 3, maxWidth: 1200, mx: 'auto' }}>
      <Box sx={{ mb: 3 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, mb: 0.5 }}>
          <AdminBadge color="warning" />
          <Typography variant="h4" fontWeight={700}>Global Admin</Typography>
        </Box>
        <Typography color="text.secondary">
          Platform-wide organization, user, and system management.
        </Typography>
      </Box>

      <Paper sx={{ borderRadius: 2 }}>
        <Tabs value={tab} onChange={(_, v) => setTab(v)} sx={{ borderBottom: 1, borderColor: 'divider', px: 2 }}>
          <Tab icon={<OrgIcon />} iconPosition="start" label="Organizations" />
          <Tab icon={<UsersIcon />} iconPosition="start" label="Users" />
          <Tab icon={<StatsIcon />} iconPosition="start" label="System Stats" />
        </Tabs>

        {/* Organizations Tab */}
        {tab === 0 && (
          <Box sx={{ p: 2 }}>
            {orgsLoading ? (
              <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
                <CircularProgress />
              </Box>
            ) : orgs.length === 0 ? (
              <Alert severity="info" sx={{ m: 2 }}>No organizations found.</Alert>
            ) : (
              <TableContainer>
                <Table>
                  <TableHead>
                    <TableRow>
                      <TableCell>Name</TableCell>
                      <TableCell>Slug</TableCell>
                      <TableCell>Plan</TableCell>
                      <TableCell align="center">Members</TableCell>
                      <TableCell>Status</TableCell>
                      <TableCell>Created</TableCell>
                      <TableCell align="center">Active</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {orgs.map((org) => (
                      <TableRow key={org.id} hover>
                        <TableCell>
                          <Typography variant="body2" fontWeight={600}>{org.name}</Typography>
                        </TableCell>
                        <TableCell>
                          <Typography variant="body2" color="text.secondary" fontFamily="monospace">
                            {org.slug}
                          </Typography>
                        </TableCell>
                        <TableCell>
                          <Chip
                            label={org.planTier}
                            size="small"
                            color={TIER_COLORS[org.planTier] || 'default'}
                            sx={{ textTransform: 'capitalize' }}
                          />
                        </TableCell>
                        <TableCell align="center">
                          <Typography variant="body2">{org.memberCount}</Typography>
                        </TableCell>
                        <TableCell>
                          <Chip
                            label={org.isActive ? 'Active' : 'Inactive'}
                            size="small"
                            color={org.isActive ? 'success' : 'error'}
                          />
                        </TableCell>
                        <TableCell>
                          <Typography variant="body2" color="text.secondary">
                            {new Date(org.createdAt).toLocaleDateString()}
                          </Typography>
                        </TableCell>
                        <TableCell align="center">
                          <Tooltip title={org.isActive ? 'Deactivate organization' : 'Activate organization'}>
                            <Switch
                              checked={org.isActive}
                              onChange={() => handleToggleOrgActive(org)}
                              size="small"
                            />
                          </Tooltip>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            )}
          </Box>
        )}

        {/* Users Tab */}
        {tab === 1 && (
          <Box sx={{ p: 2 }}>
            {usersLoading ? (
              <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
                <CircularProgress />
              </Box>
            ) : users.length === 0 ? (
              <Alert severity="info" sx={{ m: 2 }}>No users found.</Alert>
            ) : (
              <TableContainer>
                <Table>
                  <TableHead>
                    <TableRow>
                      <TableCell>Name</TableCell>
                      <TableCell>Email</TableCell>
                      <TableCell>Organization</TableCell>
                      <TableCell>Role</TableCell>
                      <TableCell>Status</TableCell>
                      <TableCell>Created</TableCell>
                      <TableCell align="center">Active</TableCell>
                      <TableCell align="center">Actions</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {users.map((u) => (
                      <TableRow key={u.id} hover>
                        <TableCell>
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                            <Typography variant="body2" fontWeight={600}>
                              {u.firstName} {u.lastName}
                            </Typography>
                            {u.isSuperAdmin && (
                              <Tooltip title="Super Admin">
                                <AdminBadge sx={{ fontSize: 16, color: 'warning.main' }} />
                              </Tooltip>
                            )}
                          </Box>
                        </TableCell>
                        <TableCell>
                          <Typography variant="body2">{u.email}</Typography>
                        </TableCell>
                        <TableCell>
                          <Typography variant="body2" color="text.secondary">
                            {u.orgName || u.orgId || '--'}
                          </Typography>
                        </TableCell>
                        <TableCell>
                          <Chip
                            label={u.orgRole}
                            size="small"
                            sx={{ textTransform: 'capitalize' }}
                          />
                        </TableCell>
                        <TableCell>
                          <Chip
                            label={u.status}
                            size="small"
                            color={
                              u.status === 'active' ? 'success' :
                              u.status === 'invited' ? 'warning' : 'error'
                            }
                          />
                        </TableCell>
                        <TableCell>
                          <Typography variant="body2" color="text.secondary">
                            {new Date(u.createdAt).toLocaleDateString()}
                          </Typography>
                        </TableCell>
                        <TableCell align="center">
                          <Tooltip title={u.isActive ? 'Deactivate user' : 'Activate user'}>
                            <Switch
                              checked={u.isActive}
                              onChange={() => handleToggleUserActive(u)}
                              size="small"
                              disabled={u.isSuperAdmin}
                            />
                          </Tooltip>
                        </TableCell>
                        <TableCell align="center">
                          <Tooltip title="Reset password">
                            <IconButton
                              size="small"
                              onClick={() => { setResetTarget(u); setNewPassword(''); setResetDialogOpen(true); }}
                            >
                              <LockResetIcon fontSize="small" />
                            </IconButton>
                          </Tooltip>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            )}
          </Box>
        )}

        {/* System Stats Tab */}
        {tab === 2 && (
          <Box sx={{ p: 3 }}>
            {statsLoading ? (
              <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
                <CircularProgress />
              </Box>
            ) : !stats ? (
              <Alert severity="info">Unable to load system stats.</Alert>
            ) : (
              <Grid container spacing={3}>
                <Grid item xs={12} sm={6} md={3}>
                  <StatCard title="Total Organizations" value={stats.totalOrganizations} />
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                  <StatCard title="Total Users" value={stats.totalUsers} />
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                  <StatCard title="Active Users" value={stats.activeUsers} color="#10b981" />
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                  <StatCard title="Entries Today" value={stats.entriesToday} color="#7b6df6" />
                </Grid>
                {stats.totalProjects !== undefined && (
                  <Grid item xs={12} sm={6} md={3}>
                    <StatCard title="Total Projects" value={stats.totalProjects} />
                  </Grid>
                )}
                {stats.totalTimeEntries !== undefined && (
                  <Grid item xs={12} sm={6} md={3}>
                    <StatCard title="Total Time Entries" value={stats.totalTimeEntries} />
                  </Grid>
                )}
              </Grid>
            )}
          </Box>
        )}
      </Paper>

      {/* Reset Password Dialog */}
      <Dialog open={resetDialogOpen} onClose={() => setResetDialogOpen(false)} maxWidth="xs" fullWidth>
        <DialogTitle>Reset Password</DialogTitle>
        <DialogContent>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            Set a new password for <strong>{resetTarget?.email}</strong>
          </Typography>
          <TextField
            label="New Password"
            type="password"
            value={newPassword}
            onChange={(e) => setNewPassword(e.target.value)}
            fullWidth
            autoFocus
            helperText="Min 8 characters, uppercase, lowercase, number, special char"
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setResetDialogOpen(false)}>Cancel</Button>
          <Button
            variant="contained"
            onClick={handleResetPassword}
            disabled={resetLoading || newPassword.length < 8}
          >
            {resetLoading ? 'Resetting...' : 'Reset Password'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default GlobalAdminPage;
