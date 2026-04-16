import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box, Button, Menu, MenuItem, Typography, Chip, Divider, Avatar,
  ListItemIcon, ListItemText,
} from '@mui/material';
import {
  UnfoldMore as SwitchIcon,
  ViewList as AllOrgsIcon,
} from '@mui/icons-material';
import { useOrganization } from '../context_providers/OrganizationContext';
import { useRBAC } from '../context_providers/RBACContext';
import { useAuth } from '../context_providers/AuthContext';
import { Organization } from '../../types';

const OrgSwitcher: React.FC = () => {
  const navigate = useNavigate();
  const { organization, organizations, activeOrgId, switchOrg } = useOrganization();
  const { isSuperAdmin } = useRBAC();
  const { user } = useAuth();
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);

  const handleOpen = (e: React.MouseEvent<HTMLElement>) => setAnchorEl(e.currentTarget);
  const handleClose = () => setAnchorEl(null);

  const handleSwitch = (orgId: string) => {
    switchOrg(orgId);
    handleClose();
  };

  const handleAllOrgs = () => {
    handleClose();
    navigate('/organizations');
  };

  // Determine role badge for an org
  const getRoleBadge = (org: Organization) => {
    // Check if user is a member via orgMemberships
    const membership = user?.orgMemberships?.find(m => m.orgId === org.id);
    if (membership && membership.roles.length > 0) {
      // Show the highest role
      const roles = membership.roles;
      const display = roles.includes('owner') ? 'Owner'
        : roles.includes('admin') ? 'Admin'
        : roles.includes('manager') ? 'Manager'
        : 'Member';
      return <Chip label={display} size="small" sx={{ ml: 1, height: 20, fontSize: '0.7rem' }} />;
    }
    // Check userRoles on the org object (from /me/orgs endpoint)
    if (org.userRoles && org.userRoles.length > 0) {
      const roles = org.userRoles;
      const display = roles.includes('owner') ? 'Owner'
        : roles.includes('admin') ? 'Admin'
        : roles.includes('manager') ? 'Manager'
        : 'Member';
      return <Chip label={display} size="small" sx={{ ml: 1, height: 20, fontSize: '0.7rem' }} />;
    }
    // Super admin accessing non-member org
    if (isSuperAdmin) {
      return <Chip label="SA" size="small" color="warning" sx={{ ml: 1, height: 20, fontSize: '0.7rem' }} />;
    }
    return null;
  };

  const currentName = organization?.name || 'Select Organization';
  const showDropdown = organizations.length > 1 || isSuperAdmin;

  return (
    <Box sx={{ px: 1.5, py: 1 }}>
      <Button
        fullWidth
        onClick={showDropdown ? handleOpen : undefined}
        sx={{
          justifyContent: 'space-between',
          textTransform: 'none',
          color: 'text.primary',
          bgcolor: 'action.hover',
          borderRadius: 1.5,
          px: 1.5,
          py: 0.75,
          '&:hover': { bgcolor: 'action.selected' },
        }}
      >
        <Box sx={{ display: 'flex', alignItems: 'center', overflow: 'hidden' }}>
          <Avatar sx={{ width: 24, height: 24, fontSize: 12, mr: 1, bgcolor: 'primary.main' }}>
            {currentName[0]?.toUpperCase() || 'O'}
          </Avatar>
          <Typography variant="body2" noWrap sx={{ fontWeight: 600, maxWidth: 130 }}>
            {currentName}
          </Typography>
        </Box>
        {showDropdown && <SwitchIcon fontSize="small" sx={{ ml: 0.5, opacity: 0.6 }} />}
      </Button>

      <Menu
        anchorEl={anchorEl}
        open={Boolean(anchorEl)}
        onClose={handleClose}
        slotProps={{ paper: { sx: { minWidth: 240, maxHeight: 400, mt: 0.5 } } }}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'left' }}
        transformOrigin={{ vertical: 'top', horizontal: 'left' }}
      >
        <MenuItem disabled sx={{ opacity: '1 !important', py: 0.5 }}>
          <Typography variant="caption" color="text.secondary" sx={{ fontWeight: 600, textTransform: 'uppercase', letterSpacing: 0.5 }}>
            Organizations
          </Typography>
        </MenuItem>
        {organizations.map((org) => (
          <MenuItem
            key={org.id}
            selected={org.id === activeOrgId}
            onClick={() => handleSwitch(org.id)}
            sx={{ borderRadius: 1, mx: 0.5 }}
          >
            <ListItemIcon>
              <Avatar sx={{ width: 28, height: 28, fontSize: 13, bgcolor: org.id === activeOrgId ? 'primary.main' : 'action.selected' }}>
                {org.name?.[0]?.toUpperCase() || 'O'}
              </Avatar>
            </ListItemIcon>
            <ListItemText
              primary={
                <Box sx={{ display: 'flex', alignItems: 'center' }}>
                  <Typography variant="body2" noWrap sx={{ maxWidth: 120 }}>{org.name}</Typography>
                  {getRoleBadge(org)}
                </Box>
              }
            />
          </MenuItem>
        ))}
        <Divider sx={{ my: 0.5 }} />
        <MenuItem onClick={handleAllOrgs} sx={{ borderRadius: 1, mx: 0.5 }}>
          <ListItemIcon><AllOrgsIcon fontSize="small" /></ListItemIcon>
          <ListItemText primary={<Typography variant="body2">All Organizations</Typography>} />
        </MenuItem>
      </Menu>
    </Box>
  );
};

export default OrgSwitcher;
