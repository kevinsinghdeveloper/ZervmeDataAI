import React, { useState, useEffect, useCallback } from 'react';
import {
  Box, Typography, Tabs, Tab, Button, Paper, Table, TableBody, TableCell,
  TableContainer, TableHead, TableRow, Avatar, Chip, Select, MenuItem,
  Dialog, DialogTitle, DialogContent, DialogActions, TextField, FormControl,
  InputLabel, IconButton, Tooltip, CircularProgress, Alert,
} from '@mui/material';
import {
  PersonAdd as InviteIcon, Delete as DeleteIcon, Cancel as RevokeIcon,
  Group as GroupIcon, Mail as MailIcon,
} from '@mui/icons-material';
import { useOrganization } from '../context_providers/OrganizationContext';
import { useNotification } from '../context_providers/NotificationContext';
import { useUser } from '../context_providers/UserContext';
import apiService from '../../utils/api.service';
import { OrgRole } from '../../types';

const ROLE_COLORS: Record<OrgRole, 'default' | 'primary' | 'secondary' | 'warning'> = {
  owner: 'warning',
  admin: 'primary',
  manager: 'secondary',
  member: 'default',
};

const INVITE_ROLES: OrgRole[] = ['member', 'manager', 'admin'];

interface OrgMember {
  id: string;
  firstName: string;
  lastName: string;
  email: string;
  orgRole: OrgRole;
  status: string;
  avatarUrl?: string;
  createdAt: string;
}

const TeamManagementPage: React.FC = () => {
  const { invitations, fetchInvitations, sendInvitation, revokeInvitation } = useOrganization();
  const { showSuccess, showError } = useNotification();
  const { user: currentUser } = useUser();

  const [tab, setTab] = useState(0);
  const [members, setMembers] = useState<OrgMember[]>([]);
  const [membersLoading, setMembersLoading] = useState(false);
  const [inviteOpen, setInviteOpen] = useState(false);
  const [inviteEmail, setInviteEmail] = useState('');
  const [inviteRole, setInviteRole] = useState<OrgRole>('member');
  const [inviteSending, setInviteSending] = useState(false);
  const [removeDialog, setRemoveDialog] = useState<OrgMember | null>(null);
  const [removing, setRemoving] = useState(false);

  const loadMembers = useCallback(async () => {
    setMembersLoading(true);
    try {
      const res = await apiService.listOrgMembers();
      const data = res.data || res || [];
      setMembers(Array.isArray(data) ? data : (data?.members || []));
    } catch (err: any) {
      showError('Failed to load team members');
    } finally {
      setMembersLoading(false);
    }
  }, [showError]);

  useEffect(() => {
    loadMembers();
    fetchInvitations();
  }, [loadMembers, fetchInvitations]);

  const handleRoleChange = async (memberId: string, newRole: string) => {
    try {
      await apiService.updateMemberRole(memberId, newRole);
      showSuccess('Role updated');
      loadMembers();
    } catch (err: any) {
      showError(err.message || 'Failed to update role');
    }
  };

  const handleRemoveMember = async () => {
    if (!removeDialog) return;
    setRemoving(true);
    try {
      await apiService.removeMember(removeDialog.id);
      showSuccess(`${removeDialog.firstName} ${removeDialog.lastName} removed from team`);
      setRemoveDialog(null);
      loadMembers();
    } catch (err: any) {
      showError(err.message || 'Failed to remove member');
    } finally {
      setRemoving(false);
    }
  };

  const handleSendInvite = async () => {
    if (!inviteEmail.trim()) return;
    setInviteSending(true);
    try {
      await sendInvitation(inviteEmail.trim(), inviteRole);
      showSuccess(`Invitation sent to ${inviteEmail}`);
      setInviteEmail('');
      setInviteRole('member');
      setInviteOpen(false);
    } catch (err: any) {
      showError(err.message || 'Failed to send invitation');
    } finally {
      setInviteSending(false);
    }
  };

  const handleRevokeInvite = async (id: string) => {
    try {
      await revokeInvitation(id);
      showSuccess('Invitation revoked');
    } catch (err: any) {
      showError(err.message || 'Failed to revoke invitation');
    }
  };

  const getStatusChip = (status: string) => {
    const colorMap: Record<string, 'success' | 'warning' | 'error' | 'default'> = {
      active: 'success', invited: 'warning', deactivated: 'error',
    };
    return <Chip label={status} size="small" color={colorMap[status] || 'default'} />;
  };

  const getInviteStatusChip = (status: string) => {
    const colorMap: Record<string, 'warning' | 'success' | 'error' | 'default'> = {
      pending: 'warning', accepted: 'success', expired: 'error', revoked: 'default',
    };
    return <Chip label={status} size="small" color={colorMap[status] || 'default'} />;
  };

  const pendingInvites = invitations.filter((i) => i.status === 'pending');

  return (
    <Box sx={{ p: 3, maxWidth: 1100, mx: 'auto' }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Box>
          <Typography variant="h4" fontWeight={700}>Team Management</Typography>
          <Typography color="text.secondary">
            Manage members, roles, and invitations for your organization.
          </Typography>
        </Box>
        <Button variant="contained" startIcon={<InviteIcon />} onClick={() => setInviteOpen(true)}>
          Invite Member
        </Button>
      </Box>

      <Paper sx={{ borderRadius: 2 }}>
        <Tabs value={tab} onChange={(_, v) => setTab(v)} sx={{ borderBottom: 1, borderColor: 'divider', px: 2 }}>
          <Tab icon={<GroupIcon />} iconPosition="start" label={`Members (${members.length})`} />
          <Tab
            icon={<MailIcon />}
            iconPosition="start"
            label={
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                Invitations
                {pendingInvites.length > 0 && (
                  <Chip label={pendingInvites.length} size="small" color="warning" />
                )}
              </Box>
            }
          />
        </Tabs>

        {/* Members Tab */}
        {tab === 0 && (
          <Box sx={{ p: 2 }}>
            {membersLoading ? (
              <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
                <CircularProgress />
              </Box>
            ) : members.length === 0 ? (
              <Alert severity="info" sx={{ m: 2 }}>
                No team members yet. Send an invitation to get started.
              </Alert>
            ) : (
              <TableContainer>
                <Table>
                  <TableHead>
                    <TableRow>
                      <TableCell>Member</TableCell>
                      <TableCell>Email</TableCell>
                      <TableCell>Role</TableCell>
                      <TableCell>Status</TableCell>
                      <TableCell>Joined</TableCell>
                      <TableCell align="right">Actions</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {members.map((member) => {
                      const isCurrentUser = member.id === currentUser?.id;
                      const isOwner = member.orgRole === 'owner';
                      return (
                        <TableRow key={member.id} hover>
                          <TableCell>
                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
                              <Avatar
                                src={member.avatarUrl}
                                sx={{ width: 36, height: 36, bgcolor: 'primary.main', fontSize: 14 }}
                              >
                                {member.firstName?.[0]}{member.lastName?.[0]}
                              </Avatar>
                              <Box>
                                <Typography variant="body2" fontWeight={600}>
                                  {member.firstName} {member.lastName}
                                  {isCurrentUser && (
                                    <Typography component="span" variant="caption" color="text.secondary"> (you)</Typography>
                                  )}
                                </Typography>
                              </Box>
                            </Box>
                          </TableCell>
                          <TableCell>
                            <Typography variant="body2">{member.email}</Typography>
                          </TableCell>
                          <TableCell>
                            {isOwner ? (
                              <Chip label="Owner" size="small" color="warning" />
                            ) : (
                              <Select
                                value={member.orgRole}
                                size="small"
                                onChange={(e) => handleRoleChange(member.id, e.target.value)}
                                disabled={isCurrentUser}
                                sx={{ minWidth: 110 }}
                              >
                                <MenuItem value="member">Member</MenuItem>
                                <MenuItem value="manager">Manager</MenuItem>
                                <MenuItem value="admin">Admin</MenuItem>
                              </Select>
                            )}
                          </TableCell>
                          <TableCell>{getStatusChip(member.status)}</TableCell>
                          <TableCell>
                            <Typography variant="body2" color="text.secondary">
                              {new Date(member.createdAt).toLocaleDateString()}
                            </Typography>
                          </TableCell>
                          <TableCell align="right">
                            {!isOwner && !isCurrentUser && (
                              <Tooltip title="Remove from organization">
                                <IconButton
                                  size="small"
                                  color="error"
                                  onClick={() => setRemoveDialog(member)}
                                >
                                  <DeleteIcon fontSize="small" />
                                </IconButton>
                              </Tooltip>
                            )}
                          </TableCell>
                        </TableRow>
                      );
                    })}
                  </TableBody>
                </Table>
              </TableContainer>
            )}
          </Box>
        )}

        {/* Invitations Tab */}
        {tab === 1 && (
          <Box sx={{ p: 2 }}>
            {invitations.length === 0 ? (
              <Alert severity="info" sx={{ m: 2 }}>
                No invitations sent yet.
              </Alert>
            ) : (
              <TableContainer>
                <Table>
                  <TableHead>
                    <TableRow>
                      <TableCell>Email</TableCell>
                      <TableCell>Role</TableCell>
                      <TableCell>Status</TableCell>
                      <TableCell>Invited By</TableCell>
                      <TableCell>Expires</TableCell>
                      <TableCell align="right">Actions</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {invitations.map((invite) => (
                      <TableRow key={invite.id} hover>
                        <TableCell>
                          <Typography variant="body2">{invite.email}</Typography>
                        </TableCell>
                        <TableCell>
                          <Chip
                            label={invite.role}
                            size="small"
                            color={ROLE_COLORS[invite.role] || 'default'}
                          />
                        </TableCell>
                        <TableCell>{getInviteStatusChip(invite.status)}</TableCell>
                        <TableCell>
                          <Typography variant="body2" color="text.secondary">
                            {invite.invitedBy}
                          </Typography>
                        </TableCell>
                        <TableCell>
                          <Typography variant="body2" color="text.secondary">
                            {new Date(invite.expiresAt).toLocaleDateString()}
                          </Typography>
                        </TableCell>
                        <TableCell align="right">
                          {invite.status === 'pending' && (
                            <Tooltip title="Revoke invitation">
                              <IconButton
                                size="small"
                                color="error"
                                onClick={() => handleRevokeInvite(invite.id)}
                              >
                                <RevokeIcon fontSize="small" />
                              </IconButton>
                            </Tooltip>
                          )}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            )}
          </Box>
        )}
      </Paper>

      {/* Invite Dialog */}
      <Dialog open={inviteOpen} onClose={() => setInviteOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Invite Team Member</DialogTitle>
        <DialogContent sx={{ display: 'flex', flexDirection: 'column', gap: 2, pt: '16px !important' }}>
          <TextField
            label="Email Address"
            type="email"
            value={inviteEmail}
            onChange={(e) => setInviteEmail(e.target.value)}
            fullWidth
            autoFocus
            placeholder="colleague@company.com"
          />
          <FormControl fullWidth>
            <InputLabel>Role</InputLabel>
            <Select value={inviteRole} label="Role" onChange={(e) => setInviteRole(e.target.value as OrgRole)}>
              {INVITE_ROLES.map((r) => (
                <MenuItem key={r} value={r}>
                  {r.charAt(0).toUpperCase() + r.slice(1)}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        </DialogContent>
        <DialogActions sx={{ px: 3, pb: 2 }}>
          <Button onClick={() => setInviteOpen(false)}>Cancel</Button>
          <Button
            variant="contained"
            onClick={handleSendInvite}
            disabled={inviteSending || !inviteEmail.trim()}
          >
            {inviteSending ? <CircularProgress size={20} /> : 'Send Invitation'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Remove Confirmation Dialog */}
      <Dialog open={!!removeDialog} onClose={() => setRemoveDialog(null)} maxWidth="xs" fullWidth>
        <DialogTitle>Remove Team Member</DialogTitle>
        <DialogContent>
          <Typography>
            Are you sure you want to remove{' '}
            <strong>{removeDialog?.firstName} {removeDialog?.lastName}</strong> from the organization?
            They will lose access to all organization data.
          </Typography>
        </DialogContent>
        <DialogActions sx={{ px: 3, pb: 2 }}>
          <Button onClick={() => setRemoveDialog(null)}>Cancel</Button>
          <Button variant="contained" color="error" onClick={handleRemoveMember} disabled={removing}>
            {removing ? <CircularProgress size={20} /> : 'Remove Member'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default TeamManagementPage;
