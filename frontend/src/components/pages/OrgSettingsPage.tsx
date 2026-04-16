import React, { useState, useEffect } from 'react';
import {
  Box, Typography, TextField, Button, Paper, Select, MenuItem,
  FormControl, InputLabel, CircularProgress,
} from '@mui/material';
import {
  Business as BusinessIcon,
} from '@mui/icons-material';
import { useOrganization } from '../context_providers/OrganizationContext';
import { useNotification } from '../context_providers/NotificationContext';

const COMMON_TIMEZONES = [
  'America/New_York', 'America/Chicago', 'America/Denver', 'America/Los_Angeles',
  'America/Phoenix', 'America/Anchorage', 'Pacific/Honolulu', 'America/Toronto',
  'America/Vancouver', 'Europe/London', 'Europe/Paris', 'Europe/Berlin',
  'Asia/Tokyo', 'Asia/Shanghai', 'Asia/Kolkata', 'Australia/Sydney',
  'Pacific/Auckland', 'UTC',
];

const OrgSettingsPage: React.FC = () => {
  const { organization, updateOrganization, isLoading: orgLoading } = useOrganization();
  const { showSuccess, showError } = useNotification();

  // General settings state
  const [name, setName] = useState('');
  const [logoUrl, setLogoUrl] = useState('');
  const [timezone, setTimezone] = useState('America/New_York');
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (!organization) return;
    setName(organization.name || '');
    setLogoUrl(organization.logoUrl || '');
    const s = organization.settings;
    if (s) {
      setTimezone(s.timezone || 'America/New_York');
    }
  }, [organization]);

  const handleSave = async () => {
    setSaving(true);
    try {
      await updateOrganization({
        name,
        logoUrl: logoUrl || undefined,
        settings: { timezone },
      } as any);
      showSuccess('Organization settings updated');
    } catch (err: any) {
      showError(err.message || 'Failed to update organization');
    } finally {
      setSaving(false);
    }
  };

  if (orgLoading && !organization) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', py: 8 }}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3, maxWidth: 900, mx: 'auto' }}>
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, mb: 0.5 }}>
        <BusinessIcon color="primary" />
        <Typography variant="h4" fontWeight={700}>Organization Settings</Typography>
      </Box>
      <Typography color="text.secondary" sx={{ mb: 3 }}>
        Manage your organization details and preferences.
      </Typography>

      <Paper sx={{ borderRadius: 2, p: 3 }}>
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
          <TextField
            label="Organization Name"
            value={name}
            onChange={(e) => setName(e.target.value)}
            fullWidth
          />
          <TextField
            label="Slug"
            value={organization?.slug || ''}
            fullWidth
            disabled
            helperText="The organization slug cannot be changed"
          />
          <TextField
            label="Logo URL"
            value={logoUrl}
            onChange={(e) => setLogoUrl(e.target.value)}
            fullWidth
            placeholder="https://example.com/logo.png"
          />
          <FormControl fullWidth>
            <InputLabel>Timezone</InputLabel>
            <Select value={timezone} label="Timezone" onChange={(e) => setTimezone(e.target.value)}>
              {COMMON_TIMEZONES.map((tz) => (
                <MenuItem key={tz} value={tz}>{tz.replace(/_/g, ' ')}</MenuItem>
              ))}
            </Select>
          </FormControl>
          <Box sx={{ display: 'flex', justifyContent: 'flex-end' }}>
            <Button
              variant="contained"
              onClick={handleSave}
              disabled={saving || !name.trim()}
            >
              {saving ? <CircularProgress size={20} /> : 'Save Changes'}
            </Button>
          </Box>
        </Box>
      </Paper>
    </Box>
  );
};

export default OrgSettingsPage;
