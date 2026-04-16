import React, { useState } from 'react';
import {
  Container, Typography, Box, Card, CardContent, TextField, Button,
  Alert,
} from '@mui/material';
import { LockReset } from '@mui/icons-material';
import { useNavigate, useSearchParams, useLocation } from 'react-router-dom';
import { useAuth } from '../context_providers/AuthContext';
import { useNotification } from '../context_providers/NotificationContext';
import apiService from '../../utils/api.service';

const ForceResetPasswordPage: React.FC = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const location = useLocation();
  const { setAuthData } = useAuth();
  const { showSuccess, showError } = useNotification();

  const locationState = location.state as { session?: string; email?: string } | null;
  const session = searchParams.get('session') || locationState?.session || '';
  const email = searchParams.get('email') || locationState?.email || '';

  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [validationError, setValidationError] = useState('');

  const validate = (): boolean => {
    if (newPassword.length < 8) {
      setValidationError('Password must be at least 8 characters long.');
      return false;
    }
    if (newPassword !== confirmPassword) {
      setValidationError('Passwords do not match.');
      return false;
    }
    setValidationError('');
    return true;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!validate()) return;

    if (!session || !email) {
      showError('Invalid session. Please log in again.');
      navigate('/login');
      return;
    }

    setIsSubmitting(true);
    try {
      const response = await apiService.respondToChallenge(email, newPassword, session);
      const data = response.data || response;
      setAuthData(data);
      showSuccess('Password updated successfully. Welcome to Zerve Direct.');

      const user = data.user;
      if (user?.role === 'admin') {
        navigate('/projects');
      } else {
        navigate('/my-documents');
      }
    } catch (err: any) {
      showError(err.message || 'Failed to reset password. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Container maxWidth="sm" sx={{ py: 8 }}>
      <Card>
        <CardContent sx={{ p: 4 }}>
          <Box sx={{ textAlign: 'center', mb: 3 }}>
            <LockReset sx={{ fontSize: 48, color: 'primary.main', mb: 1 }} />
            <Typography variant="h4" gutterBottom fontWeight={600}>
              Set New Password
            </Typography>
            <Typography variant="body1" color="text.secondary">
              For security, please create a new password to continue.
            </Typography>
          </Box>

          {!session && (
            <Alert severity="warning" sx={{ mb: 2 }}>
              No active session found. Please log in with your temporary password first.
            </Alert>
          )}

          <Box
            component="form"
            onSubmit={handleSubmit}
            sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}
          >
            <TextField
              label="New Password"
              type="password"
              value={newPassword}
              onChange={(e) => {
                setNewPassword(e.target.value);
                setValidationError('');
              }}
              required
              fullWidth
              helperText="Minimum 8 characters"
              autoFocus
            />
            <TextField
              label="Confirm Password"
              type="password"
              value={confirmPassword}
              onChange={(e) => {
                setConfirmPassword(e.target.value);
                setValidationError('');
              }}
              required
              fullWidth
            />

            {validationError && (
              <Alert severity="error">{validationError}</Alert>
            )}

            <Button
              type="submit"
              variant="contained"
              size="large"
              disabled={isSubmitting || !session}
              fullWidth
              sx={{ mt: 1 }}
            >
              {isSubmitting ? 'Updating Password...' : 'Set Password & Continue'}
            </Button>
          </Box>
        </CardContent>
      </Card>
    </Container>
  );
};

export default ForceResetPasswordPage;
