import React, { useState, useEffect } from 'react';
import {
  Box, Typography, Container, Stepper, Step, StepLabel, TextField, Button,
  Paper, IconButton, Select, MenuItem,
  FormControl, InputLabel, CircularProgress,
} from '@mui/material';
import {
  Business as OrgIcon, Group as TeamIcon,
  CheckCircle as DoneIcon, Add as AddIcon, Delete as DeleteIcon,
  ArrowForward as NextIcon,
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { useNotification } from '../context_providers/NotificationContext';
import { useOrganization } from '../context_providers/OrganizationContext';
import apiService from '../../utils/api.service';
import { OrgRole } from '../../types';

const STEPS = ['Create Organization', 'Invite Team', 'Complete'];

interface InviteRow {
  email: string;
  role: OrgRole;
}

const OrgSetupWizard: React.FC = () => {
  const navigate = useNavigate();
  const { showSuccess, showError } = useNotification();
  const { fetchOrganization, sendInvitation } = useOrganization();

  const [activeStep, setActiveStep] = useState(0);
  const [loading, setLoading] = useState(false);

  // Step 1: Create Org
  const [orgName, setOrgName] = useState('');
  const [slugPreview, setSlugPreview] = useState('');

  // Step 2: Invite Team
  const [invites, setInvites] = useState<InviteRow[]>([{ email: '', role: 'member' }]);

  // Track created org for subsequent steps
  const [, setCreatedOrgId] = useState<string | null>(null);

  useEffect(() => {
    const slug = orgName
      .toLowerCase()
      .replace(/[^a-z0-9\s-]/g, '')
      .replace(/\s+/g, '-')
      .replace(/-+/g, '-')
      .slice(0, 50);
    setSlugPreview(slug);
  }, [orgName]);

  const handleCreateOrg = async () => {
    if (!orgName.trim()) return;
    setLoading(true);
    try {
      const res = await apiService.createOrg({ name: orgName.trim() });
      const org = res.data || res;
      setCreatedOrgId(org.id);
      if (org.id) localStorage.setItem('currentOrgId', org.id);
      await fetchOrganization();
      setActiveStep(1);
    } catch (err: any) {
      showError(err.message || 'Failed to create organization');
    } finally {
      setLoading(false);
    }
  };

  const handleInviteTeam = async () => {
    const validInvites = invites.filter((i) => i.email.trim());
    if (validInvites.length === 0) {
      setActiveStep(2);
      return;
    }
    setLoading(true);
    let successCount = 0;
    for (const invite of validInvites) {
      try {
        await sendInvitation(invite.email.trim(), invite.role);
        successCount++;
      } catch {
        // Continue sending remaining invitations
      }
    }
    if (successCount > 0) {
      showSuccess(`${successCount} invitation${successCount > 1 ? 's' : ''} sent`);
    }
    setLoading(false);
    setActiveStep(2);
  };

  const addInviteRow = () => {
    setInvites([...invites, { email: '', role: 'member' }]);
  };

  const updateInviteRow = (index: number, field: keyof InviteRow, value: string) => {
    const updated = [...invites];
    (updated[index] as any)[field] = value;
    setInvites(updated);
  };

  const removeInviteRow = (index: number) => {
    if (invites.length <= 1) return;
    setInvites(invites.filter((_, i) => i !== index));
  };

  const renderStepContent = () => {
    switch (activeStep) {
      case 0:
        return (
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3, py: 2 }}>
            <Box sx={{ textAlign: 'center', mb: 2 }}>
              <OrgIcon sx={{ fontSize: 48, color: 'primary.main', mb: 1 }} />
              <Typography variant="h5" fontWeight={600}>Name Your Organization</Typography>
              <Typography color="text.secondary">
                This is your team's workspace.
              </Typography>
            </Box>
            <TextField
              label="Organization Name"
              value={orgName}
              onChange={(e) => setOrgName(e.target.value)}
              fullWidth
              autoFocus
              placeholder="Acme Corporation"
            />
            {slugPreview && (
              <Typography variant="body2" color="text.secondary">
                Your workspace URL: <strong>zerve.app/{slugPreview}</strong>
              </Typography>
            )}
            <Box sx={{ display: 'flex', justifyContent: 'flex-end' }}>
              <Button
                variant="contained"
                endIcon={loading ? <CircularProgress size={18} /> : <NextIcon />}
                onClick={handleCreateOrg}
                disabled={loading || !orgName.trim()}
                size="large"
              >
                Create Organization
              </Button>
            </Box>
          </Box>
        );

      case 1:
        return (
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3, py: 2 }}>
            <Box sx={{ textAlign: 'center', mb: 2 }}>
              <TeamIcon sx={{ fontSize: 48, color: 'primary.main', mb: 1 }} />
              <Typography variant="h5" fontWeight={600}>Invite Your Team</Typography>
              <Typography color="text.secondary">
                Add team members by email. You can always invite more later.
              </Typography>
            </Box>

            {invites.map((invite, index) => (
              <Box key={index} sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
                <TextField
                  label="Email"
                  value={invite.email}
                  onChange={(e) => updateInviteRow(index, 'email', e.target.value)}
                  fullWidth
                  placeholder="colleague@company.com"
                  size="small"
                />
                <FormControl sx={{ minWidth: 130 }} size="small">
                  <InputLabel>Role</InputLabel>
                  <Select
                    value={invite.role}
                    label="Role"
                    onChange={(e) => updateInviteRow(index, 'role', e.target.value)}
                  >
                    <MenuItem value="member">Member</MenuItem>
                    <MenuItem value="manager">Manager</MenuItem>
                    <MenuItem value="admin">Admin</MenuItem>
                  </Select>
                </FormControl>
                <IconButton
                  onClick={() => removeInviteRow(index)}
                  disabled={invites.length <= 1}
                  size="small"
                >
                  <DeleteIcon fontSize="small" />
                </IconButton>
              </Box>
            ))}

            <Button startIcon={<AddIcon />} onClick={addInviteRow} variant="text" sx={{ alignSelf: 'flex-start' }}>
              Add Another
            </Button>

            <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
              <Button
                variant="text"
                onClick={() => setActiveStep(2)}
              >
                Skip for Now
              </Button>
              <Button
                variant="contained"
                endIcon={loading ? <CircularProgress size={18} /> : <NextIcon />}
                onClick={handleInviteTeam}
                disabled={loading}
                size="large"
              >
                Send Invitations
              </Button>
            </Box>
          </Box>
        );

      case 2:
        return (
          <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 3, py: 4 }}>
            <DoneIcon sx={{ fontSize: 64, color: 'success.main' }} />
            <Typography variant="h4" fontWeight={700}>You're All Set!</Typography>
            <Typography color="text.secondary" textAlign="center" sx={{ maxWidth: 400 }}>
              Your organization is ready. Create projects and invite more team members from the settings.
            </Typography>
            <Button
              variant="contained"
              size="large"
              onClick={() => navigate('/projects')}
              endIcon={<NextIcon />}
            >
              Go to Projects
            </Button>
          </Box>
        );

      default:
        return null;
    }
  };

  return (
    <Container maxWidth="md" sx={{ py: 6 }}>
      <Paper sx={{ p: 4, borderRadius: 3 }}>
        <Stepper activeStep={activeStep} alternativeLabel sx={{ mb: 4 }}>
          {STEPS.map((label) => (
            <Step key={label}>
              <StepLabel>{label}</StepLabel>
            </Step>
          ))}
        </Stepper>

        {renderStepContent()}
      </Paper>
    </Container>
  );
};

export default OrgSetupWizard;
