import React, { useState } from 'react';
import {
  Box, Container, Typography, TextField, Button, Card, CardContent,
  Link as MuiLink, Divider, Tooltip,
} from '@mui/material';
import { useNavigate, Link, useSearchParams } from 'react-router-dom';
import { useAuth } from '../context_providers/AuthContext';
import { useNotification } from '../context_providers/NotificationContext';
import apiService from '../../utils/api.service';

const GoogleIcon: React.FC = () => (
  <svg width="18" height="18" viewBox="0 0 18 18" xmlns="http://www.w3.org/2000/svg">
    <path d="M17.64 9.2c0-.637-.057-1.251-.164-1.84H9v3.481h4.844a4.14 4.14 0 0 1-1.796 2.716v2.259h2.908c1.702-1.567 2.684-3.875 2.684-6.615z" fill="#4285F4" />
    <path d="M9 18c2.43 0 4.467-.806 5.956-2.18l-2.908-2.259c-.806.54-1.837.86-3.048.86-2.344 0-4.328-1.584-5.036-3.711H.957v2.332A8.997 8.997 0 0 0 9 18z" fill="#34A853" />
    <path d="M3.964 10.71A5.41 5.41 0 0 1 3.682 9c0-.593.102-1.17.282-1.71V4.958H.957A8.997 8.997 0 0 0 0 9c0 1.452.348 2.827.957 4.042l3.007-2.332z" fill="#FBBC05" />
    <path d="M9 3.58c1.321 0 2.508.454 3.44 1.345l2.582-2.58C13.463.891 11.426 0 9 0A8.997 8.997 0 0 0 .957 4.958L3.964 6.29C4.672 4.163 6.656 2.58 9 3.58z" fill="#EA4335" />
  </svg>
);

const MicrosoftIcon: React.FC = () => (
  <svg width="18" height="18" viewBox="0 0 21 21" xmlns="http://www.w3.org/2000/svg">
    <rect x="1" y="1" width="9" height="9" fill="#F25022" />
    <rect x="11" y="1" width="9" height="9" fill="#7FBA00" />
    <rect x="1" y="11" width="9" height="9" fill="#00A4EF" />
    <rect x="11" y="11" width="9" height="9" fill="#FFB900" />
  </svg>
);

const LoginPage: React.FC = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const invitationToken = searchParams.get('invitation') || '';
  const planParam = searchParams.get('plan') || '';
  const billingParam = searchParams.get('billing') || '';
  const { login } = useAuth();
  const { showError } = useNotification();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isGoogleLoading, setIsGoogleLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    try {
      await login(email, password);

      // If user came from an invitation link, redirect to accept it
      if (invitationToken) {
        navigate(`/accept-invitation/${invitationToken}`);
        return;
      }

      const storedUser = localStorage.getItem('user');
      if (storedUser) {
        const user = JSON.parse(storedUser);
        if (user.isSuperAdmin) {
          navigate('/admin');
        } else if (user.orgId) {
          navigate('/projects');
        } else {
          const setupParams = new URLSearchParams();
          if (planParam) setupParams.set('plan', planParam);
          if (billingParam) setupParams.set('billing', billingParam);
          const qs = setupParams.toString();
          navigate(`/setup${qs ? `?${qs}` : ''}`);
        }
      } else {
        const setupParams = new URLSearchParams();
        if (planParam) setupParams.set('plan', planParam);
        if (billingParam) setupParams.set('billing', billingParam);
        const qs = setupParams.toString();
        navigate(`/setup${qs ? `?${qs}` : ''}`);
      }
    } catch (err: any) {
      if (err.message === 'NEW_PASSWORD_REQUIRED') {
        navigate('/force-reset-password');
      } else {
        showError(err.message || 'Login failed');
      }
    } finally {
      setIsLoading(false);
    }
  };

  const handleGoogleLogin = async () => {
    setIsGoogleLoading(true);
    try {
      const redirectUri = `${window.location.origin}/auth/callback/google`;
      const response = await apiService.getOAuthUrl('google', redirectUri);
      const url = response.data?.url || response.url;
      if (url) {
        window.location.href = url;
      } else {
        showError('Google login is not available');
      }
    } catch {
      showError('Google login is not available');
    } finally {
      setIsGoogleLoading(false);
    }
  };

  return (
    <Container maxWidth="sm" sx={{ py: 8 }}>
      <Card>
        <CardContent sx={{ p: 4 }}>
          <Typography variant="h4" gutterBottom textAlign="center">Sign In</Typography>
          <Typography variant="body2" color="text.secondary" textAlign="center" sx={{ mb: 3 }}>
            Log in to your Zerve Data AI account
          </Typography>

          {/* Social Login Buttons */}
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1.5, mb: 3 }}>
            <Button
              variant="outlined"
              size="large"
              fullWidth
              onClick={handleGoogleLogin}
              disabled={isGoogleLoading}
              startIcon={<GoogleIcon />}
              sx={{
                bgcolor: '#fff',
                color: '#3c4043',
                borderColor: '#dadce0',
                textTransform: 'none',
                fontWeight: 500,
                fontSize: '0.95rem',
                py: 1.25,
                '&:hover': {
                  bgcolor: '#f8f9fa',
                  borderColor: '#dadce0',
                },
              }}
            >
              {isGoogleLoading ? 'Redirecting...' : 'Continue with Google'}
            </Button>

            <Tooltip title="Coming soon" arrow>
              <span>
                <Button
                  variant="outlined"
                  size="large"
                  fullWidth
                  disabled
                  startIcon={<MicrosoftIcon />}
                  sx={{
                    textTransform: 'none',
                    fontWeight: 500,
                    fontSize: '0.95rem',
                    py: 1.25,
                  }}
                >
                  Continue with Microsoft
                </Button>
              </span>
            </Tooltip>
          </Box>

          {/* OR Divider */}
          <Divider sx={{ mb: 3 }}>
            <Typography variant="body2" color="text.secondary">
              OR
            </Typography>
          </Divider>

          {/* Email/Password Form */}
          <Box component="form" onSubmit={handleSubmit} sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
            <TextField label="Email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} required fullWidth />
            <TextField label="Password" type="password" value={password} onChange={(e) => setPassword(e.target.value)} required fullWidth />
            <Button type="submit" variant="contained" size="large" disabled={isLoading} fullWidth>
              {isLoading ? 'Signing in...' : 'Sign In'}
            </Button>
            <Box sx={{ textAlign: 'center', mt: 1 }}>
              <MuiLink component={Link} to="/forgot-password" variant="body2">Forgot password?</MuiLink>
            </Box>
          </Box>
        </CardContent>
      </Card>
    </Container>
  );
};

export default LoginPage;
