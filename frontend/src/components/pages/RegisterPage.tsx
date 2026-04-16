import React, { useState } from 'react';
import { Box, Container, Typography, TextField, Button, Card, CardContent, Link as MuiLink, Alert } from '@mui/material';
import { useNavigate, Link, useSearchParams } from 'react-router-dom';
import apiService from '../../utils/api.service';
import { useNotification } from '../context_providers/NotificationContext';
import { useAuth } from '../context_providers/AuthContext';

const RegisterPage: React.FC = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const invitationToken = searchParams.get('invitation') || '';
  const planParam = searchParams.get('plan') || '';
  const billingParam = searchParams.get('billing') || '';
  const { showSuccess, showError } = useNotification();
  const { login } = useAuth();
  const [form, setForm] = useState({ email: '', password: '', firstName: '', lastName: '' });
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    try {
      const registerData: any = { ...form };
      if (invitationToken) {
        registerData.invitationToken = invitationToken;
      }
      await apiService.register(registerData);

      // Auto-login after registration
      try {
        await login(form.email, form.password);
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
      } catch {
        // Auto-login failed, redirect to login
        showSuccess('Registration successful! Please sign in.');
        navigate('/login');
      }
    } catch (err: any) {
      showError(err.message || 'Registration failed');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Container maxWidth="sm" sx={{ py: 8 }}>
      <Card>
        <CardContent sx={{ p: 4 }}>
          <Typography variant="h4" gutterBottom textAlign="center">Create Account</Typography>
          {invitationToken && (
            <Alert severity="info" sx={{ mb: 2 }}>
              You're registering with an invitation. Your account will be automatically linked to the organization.
            </Alert>
          )}
          <Box component="form" onSubmit={handleSubmit} sx={{ display: 'flex', flexDirection: 'column', gap: 2, mt: 2 }}>
            <Box sx={{ display: 'flex', gap: 2 }}>
              <TextField label="First Name" value={form.firstName} onChange={(e) => setForm({ ...form, firstName: e.target.value })} required fullWidth />
              <TextField label="Last Name" value={form.lastName} onChange={(e) => setForm({ ...form, lastName: e.target.value })} required fullWidth />
            </Box>
            <TextField label="Email" type="email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} required fullWidth />
            <TextField label="Password" type="password" value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} required fullWidth helperText="Min 8 characters, uppercase, lowercase, and number" />
            <Button type="submit" variant="contained" size="large" disabled={isLoading} fullWidth>
              {isLoading ? 'Creating account...' : 'Create Account'}
            </Button>
            <Typography variant="body2" textAlign="center">
              Already have an account?{' '}
              <MuiLink component={Link} to={(() => {
                const p = new URLSearchParams();
                if (planParam) p.set('plan', planParam);
                if (billingParam) p.set('billing', billingParam);
                const qs = p.toString();
                return `/login${qs ? `?${qs}` : ''}`;
              })()}>Sign in</MuiLink>
            </Typography>
          </Box>
        </CardContent>
      </Card>
    </Container>
  );
};

export default RegisterPage;
