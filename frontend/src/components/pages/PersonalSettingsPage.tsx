import React, { useState, useEffect } from 'react';
import {
  Box, Typography, Paper, TextField, Button, Switch,
  FormControlLabel, Select, MenuItem, FormControl, InputLabel,
  CircularProgress, Grid, Avatar, Chip, Link,
} from '@mui/material';
import {
  Person as PersonIcon, Notifications as NotifIcon,
  Link as LinkIcon, Security as SecurityIcon,
  Settings as PrefsIcon,
} from '@mui/icons-material';
import { useUser } from '../context_providers/UserContext';
import { useNotification } from '../context_providers/NotificationContext';
import { NotificationPreferences } from '../../types';

const COMMON_TIMEZONES = [
  'America/New_York', 'America/Chicago', 'America/Denver', 'America/Los_Angeles',
  'America/Phoenix', 'America/Anchorage', 'Pacific/Honolulu', 'America/Toronto',
  'America/Vancouver', 'Europe/London', 'Europe/Paris', 'Europe/Berlin',
  'Asia/Tokyo', 'Asia/Shanghai', 'Asia/Kolkata', 'Australia/Sydney',
  'Pacific/Auckland', 'UTC',
];

interface SectionProps {
  icon: React.ReactNode;
  title: string;
  description: string;
  children: React.ReactNode;
}

const Section: React.FC<SectionProps> = ({ icon, title, description, children }) => (
  <Paper sx={{ p: 3, borderRadius: 2 }}>
    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, mb: 0.5 }}>
      {icon}
      <Typography variant="h6" fontWeight={600}>{title}</Typography>
    </Box>
    <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
      {description}
    </Typography>
    {children}
  </Paper>
);

const PersonalSettingsPage: React.FC = () => {
  const { user, updateUser, updatePreferences, isLoading } = useUser();
  const { showSuccess, showError } = useNotification();

  // Profile state
  const [firstName, setFirstName] = useState('');
  const [lastName, setLastName] = useState('');
  const [phone, setPhone] = useState('');
  const [avatarUrl, setAvatarUrl] = useState('');
  const [profileSaving, setProfileSaving] = useState(false);

  // Preferences state
  const [timezone, setTimezone] = useState('America/New_York');
  const [prefsSaving, setPrefsSaving] = useState(false);

  // Notification state
  const [inAppNotifications, setInAppNotifications] = useState(true);
  const [desktopNotifications, setDesktopNotifications] = useState(false);
  const [emailNotifications, setEmailNotifications] = useState(true);
  const [notifSaving, setNotifSaving] = useState(false);

  useEffect(() => {
    if (!user) return;
    setFirstName(user.firstName || '');
    setLastName(user.lastName || '');
    setPhone(user.phone || '');
    setAvatarUrl(user.avatarUrl || '');
    setTimezone(user.timezone || 'America/New_York');
    const np = user.notificationPreferences;
    if (np) {
      setInAppNotifications(np.inAppNotifications ?? true);
      setDesktopNotifications(np.desktopNotifications ?? false);
      setEmailNotifications(np.emailNotifications ?? true);
    }
  }, [user]);

  const handleSaveProfile = async () => {
    setProfileSaving(true);
    try {
      await updateUser({ firstName, lastName, phone: phone || undefined, avatarUrl: avatarUrl || undefined });
      showSuccess('Profile updated');
    } catch (err: any) {
      showError(err.message || 'Failed to update profile');
    } finally {
      setProfileSaving(false);
    }
  };

  const handleSavePreferences = async () => {
    setPrefsSaving(true);
    try {
      await updatePreferences({ timezone });
      showSuccess('Preferences updated');
    } catch (err: any) {
      showError(err.message || 'Failed to update preferences');
    } finally {
      setPrefsSaving(false);
    }
  };

  const handleSaveNotifications = async () => {
    setNotifSaving(true);
    try {
      const notificationPreferences: NotificationPreferences = {
        inAppNotifications,
        desktopNotifications,
        emailNotifications,
      };
      await updatePreferences({ notificationPreferences });
      showSuccess('Notification preferences updated');
    } catch (err: any) {
      showError(err.message || 'Failed to update notifications');
    } finally {
      setNotifSaving(false);
    }
  };

  if (isLoading && !user) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', py: 8 }}>
        <CircularProgress />
      </Box>
    );
  }

  const oauthProviders = user?.oauthProviders || {};
  const providerNames = Object.keys(oauthProviders);

  return (
    <Box sx={{ p: 3, maxWidth: 800, mx: 'auto' }}>
      <Typography variant="h4" fontWeight={700} gutterBottom>
        Personal Settings
      </Typography>
      <Typography color="text.secondary" sx={{ mb: 4 }}>
        Manage your profile, preferences, and notifications.
      </Typography>

      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
        {/* Profile Section */}
        <Section
          icon={<PersonIcon color="primary" />}
          title="Profile"
          description="Your personal information visible to your team."
        >
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 3 }}>
            <Avatar
              src={avatarUrl}
              sx={{ width: 64, height: 64, bgcolor: 'primary.main', fontSize: 24 }}
            >
              {firstName?.[0]}{lastName?.[0]}
            </Avatar>
            <Box>
              <Typography variant="body2" fontWeight={600}>
                {firstName} {lastName}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                {user?.email}
              </Typography>
            </Box>
          </Box>

          <Grid container spacing={2}>
            <Grid item xs={12} sm={6}>
              <TextField
                label="First Name"
                value={firstName}
                onChange={(e) => setFirstName(e.target.value)}
                fullWidth
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                label="Last Name"
                value={lastName}
                onChange={(e) => setLastName(e.target.value)}
                fullWidth
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField label="Email" value={user?.email || ''} fullWidth disabled />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                label="Phone"
                value={phone}
                onChange={(e) => setPhone(e.target.value)}
                fullWidth
                placeholder="+1 (555) 123-4567"
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                label="Avatar URL"
                value={avatarUrl}
                onChange={(e) => setAvatarUrl(e.target.value)}
                fullWidth
                placeholder="https://example.com/avatar.jpg"
              />
            </Grid>
          </Grid>

          <Box sx={{ display: 'flex', justifyContent: 'flex-end', mt: 2 }}>
            <Button
              variant="contained"
              onClick={handleSaveProfile}
              disabled={profileSaving || !firstName.trim() || !lastName.trim()}
            >
              {profileSaving ? <CircularProgress size={20} /> : 'Save Profile'}
            </Button>
          </Box>
        </Section>

        {/* Preferences Section */}
        <Section
          icon={<PrefsIcon color="primary" />}
          title="Preferences"
          description="Customize your account defaults."
        >
          <Grid container spacing={2}>
            <Grid item xs={12} sm={6}>
              <FormControl fullWidth>
                <InputLabel>Timezone</InputLabel>
                <Select value={timezone} label="Timezone" onChange={(e) => setTimezone(e.target.value)}>
                  {COMMON_TIMEZONES.map((tz) => (
                    <MenuItem key={tz} value={tz}>{tz.replace(/_/g, ' ')}</MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
          </Grid>

          <Box sx={{ display: 'flex', justifyContent: 'flex-end', mt: 2 }}>
            <Button variant="contained" onClick={handleSavePreferences} disabled={prefsSaving}>
              {prefsSaving ? <CircularProgress size={20} /> : 'Save Preferences'}
            </Button>
          </Box>
        </Section>

        {/* Notifications Section */}
        <Section
          icon={<NotifIcon color="primary" />}
          title="Notifications"
          description="Control how and when you receive notifications."
        >
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
            <FormControlLabel
              control={
                <Switch
                  checked={emailNotifications}
                  onChange={(e) => setEmailNotifications(e.target.checked)}
                />
              }
              label="Email notifications"
            />
            <FormControlLabel
              control={
                <Switch
                  checked={inAppNotifications}
                  onChange={(e) => setInAppNotifications(e.target.checked)}
                />
              }
              label="In-app notifications"
            />
            <FormControlLabel
              control={
                <Switch
                  checked={desktopNotifications}
                  onChange={(e) => setDesktopNotifications(e.target.checked)}
                />
              }
              label="Desktop notifications"
            />
          </Box>

          <Box sx={{ display: 'flex', justifyContent: 'flex-end', mt: 2 }}>
            <Button variant="contained" onClick={handleSaveNotifications} disabled={notifSaving}>
              {notifSaving ? <CircularProgress size={20} /> : 'Save Notifications'}
            </Button>
          </Box>
        </Section>

        {/* Connected Accounts Section */}
        <Section
          icon={<LinkIcon color="primary" />}
          title="Connected Accounts"
          description="OAuth providers linked to your account."
        >
          {providerNames.length === 0 ? (
            <Typography variant="body2" color="text.secondary">
              No connected accounts. OAuth providers will appear here once linked.
            </Typography>
          ) : (
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
              {providerNames.map((provider) => {
                const data = oauthProviders[provider];
                return (
                  <Box
                    key={provider}
                    sx={{
                      display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                      p: 2, borderRadius: 1, bgcolor: 'action.hover',
                    }}
                  >
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                      <Typography variant="body1" fontWeight={600} sx={{ textTransform: 'capitalize' }}>
                        {provider}
                      </Typography>
                      <Chip label="Connected" size="small" color="success" variant="outlined" />
                    </Box>
                    <Typography variant="caption" color="text.secondary">
                      Linked {new Date(data.linked_at).toLocaleDateString()}
                    </Typography>
                  </Box>
                );
              })}
            </Box>
          )}
        </Section>

        {/* Security Section */}
        <Section
          icon={<SecurityIcon color="primary" />}
          title="Security"
          description="Manage your account security settings."
        >
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <Box>
              <Typography variant="body1" fontWeight={500}>Password</Typography>
              <Typography variant="body2" color="text.secondary">
                Change your account password through the reset flow.
              </Typography>
            </Box>
            <Button
              variant="outlined"
              component={Link}
              href="/forgot-password"
            >
              Change Password
            </Button>
          </Box>
        </Section>
      </Box>
    </Box>
  );
};

export default PersonalSettingsPage;
