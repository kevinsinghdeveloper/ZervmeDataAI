import React from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box, Typography, Card, CardContent, CardActions, Button, Grid, Chip,
  Avatar, CircularProgress,
} from '@mui/material';
import {
  Business as OrgIcon,
  People as MembersIcon,
  SwapHoriz as SwitchIcon,
} from '@mui/icons-material';
import { useOrganization } from '../context_providers/OrganizationContext';
import { useRBAC } from '../context_providers/RBACContext';
import { useAuth } from '../context_providers/AuthContext';
import { Organization } from '../../types';

const OrganizationsPage: React.FC = () => {
  const navigate = useNavigate();
  const { organizations, activeOrgId, switchOrg, isLoading } = useOrganization();
  const { isSuperAdmin } = useRBAC();
  const { user } = useAuth();

  const handleSwitch = (orgId: string) => {
    switchOrg(orgId);
    navigate('/projects');
  };

  const getUserRole = (org: Organization): string | null => {
    const membership = user?.orgMemberships?.find(m => m.orgId === org.id);
    if (membership && membership.roles.length > 0) {
      const roles = membership.roles;
      if (roles.includes('owner')) return 'Owner';
      if (roles.includes('admin')) return 'Admin';
      if (roles.includes('manager')) return 'Manager';
      return 'Member';
    }
    if (org.userRoles && org.userRoles.length > 0) {
      const roles = org.userRoles;
      if (roles.includes('owner')) return 'Owner';
      if (roles.includes('admin')) return 'Admin';
      if (roles.includes('manager')) return 'Manager';
      return 'Member';
    }
    return null;
  };

  const isMember = (org: Organization): boolean => getUserRole(org) !== null;

  if (isLoading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: 400 }}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      <Box sx={{ mb: 3, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <Box>
          <Typography variant="h4" sx={{ fontWeight: 700 }}>Organizations</Typography>
          <Typography variant="body2" color="text.secondary">
            {isSuperAdmin ? 'All organizations in the system' : 'Your organizations'}
          </Typography>
        </Box>
        <Chip
          label={`${organizations.length} organization${organizations.length !== 1 ? 's' : ''}`}
          color="primary"
          variant="outlined"
        />
      </Box>

      {organizations.length === 0 ? (
        <Box sx={{ textAlign: 'center', py: 8 }}>
          <OrgIcon sx={{ fontSize: 64, color: 'text.disabled', mb: 2 }} />
          <Typography variant="h6" color="text.secondary">No organizations found</Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
            You don't belong to any organizations yet.
          </Typography>
        </Box>
      ) : (
        <Grid container spacing={2}>
          {organizations.map((org) => {
            const role = getUserRole(org);
            const isActive = org.id === activeOrgId;
            const memberOfOrg = isMember(org);

            return (
              <Grid item xs={12} sm={6} md={4} key={org.id}>
                <Card
                  variant="outlined"
                  sx={{
                    height: '100%',
                    display: 'flex',
                    flexDirection: 'column',
                    borderColor: isActive ? 'primary.main' : 'divider',
                    borderWidth: isActive ? 2 : 1,
                    transition: 'border-color 0.2s',
                    '&:hover': { borderColor: 'primary.light' },
                  }}
                >
                  <CardContent sx={{ flex: 1 }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', mb: 1.5 }}>
                      <Avatar sx={{ width: 40, height: 40, bgcolor: isActive ? 'primary.main' : 'action.selected', mr: 1.5 }}>
                        {org.name?.[0]?.toUpperCase() || 'O'}
                      </Avatar>
                      <Box sx={{ flex: 1, minWidth: 0 }}>
                        <Typography variant="subtitle1" sx={{ fontWeight: 600 }} noWrap>
                          {org.name}
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          Organization
                        </Typography>
                      </Box>
                      {isActive && <Chip label="Active" color="primary" size="small" />}
                    </Box>

                    <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap', mb: 1 }}>
                      {role && <Chip label={role} size="small" variant="outlined" />}
                      {!memberOfOrg && isSuperAdmin && (
                        <Chip label="Super Admin Access" size="small" color="warning" variant="outlined" />
                      )}
                    </Box>

                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5, color: 'text.secondary' }}>
                      <MembersIcon sx={{ fontSize: 16 }} />
                      <Typography variant="caption">
                        {org.memberCount ?? '—'} member{org.memberCount !== 1 ? 's' : ''}
                      </Typography>
                    </Box>

                    <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 0.5 }}>
                      Created {new Date(org.createdAt).toLocaleDateString()}
                    </Typography>
                  </CardContent>

                  <CardActions sx={{ px: 2, pb: 2 }}>
                    {isActive ? (
                      <Button size="small" disabled variant="outlined">Current</Button>
                    ) : (
                      <Button
                        size="small"
                        variant="contained"
                        startIcon={<SwitchIcon />}
                        onClick={() => handleSwitch(org.id)}
                      >
                        Switch
                      </Button>
                    )}
                  </CardActions>
                </Card>
              </Grid>
            );
          })}
        </Grid>
      )}
    </Box>
  );
};

export default OrganizationsPage;
