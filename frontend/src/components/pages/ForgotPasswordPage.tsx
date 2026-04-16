import React, { useState } from 'react';
import { Container, Typography, Box, Card, CardContent, TextField, Button, Link as MuiLink } from '@mui/material';
import { Email, ArrowBack } from '@mui/icons-material';
import { Link } from 'react-router-dom';
import apiService from '../../utils/api.service';
import { useNotification } from '../context_providers/NotificationContext';

const ForgotPasswordPage: React.FC = () => {
  const { showSuccess, showError } = useNotification();
  const [email, setEmail] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [submitted, setSubmitted] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email.trim()) return;

    setIsLoading(true);
    try {
      await apiService.requestPasswordReset(email);
      setSubmitted(true);
      showSuccess('Password reset instructions have been sent to your email.');
    } catch (err: any) {
      showError(err.message || 'Failed to send reset email. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Container maxWidth="sm" sx={{ py: 8 }}>
      <Card>
        <CardContent sx={{ p: 4 }}>
          {!submitted ? (
            <>
              <Typography variant="h4" gutterBottom textAlign="center">Forgot Password</Typography>
              <Typography variant="body1" color="text.secondary" textAlign="center" sx={{ mb: 3 }}>
                Enter your email address and we will send you instructions to reset your password.
              </Typography>
              <Box component="form" onSubmit={handleSubmit} sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                <TextField
                  label="Email Address"
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                  fullWidth
                  autoFocus
                />
                <Button
                  type="submit"
                  variant="contained"
                  size="large"
                  disabled={isLoading}
                  fullWidth
                  startIcon={<Email />}
                >
                  {isLoading ? 'Sending...' : 'Send Reset Link'}
                </Button>
                <Box sx={{ textAlign: 'center', mt: 1 }}>
                  <MuiLink component={Link} to="/login" variant="body2" sx={{ display: 'inline-flex', alignItems: 'center', gap: 0.5 }}>
                    <ArrowBack fontSize="small" /> Back to Sign In
                  </MuiLink>
                </Box>
              </Box>
            </>
          ) : (
            <Box sx={{ textAlign: 'center', py: 2 }}>
              <Email sx={{ fontSize: 64, color: 'primary.main', mb: 2 }} />
              <Typography variant="h5" gutterBottom>Check Your Email</Typography>
              <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
                We have sent password reset instructions to <strong>{email}</strong>. Please check your inbox and follow the link to reset your password.
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
                Did not receive the email? Check your spam folder or try again.
              </Typography>
              <Box sx={{ display: 'flex', gap: 2, justifyContent: 'center' }}>
                <Button variant="outlined" onClick={() => setSubmitted(false)}>
                  Try Again
                </Button>
                <Button variant="contained" component={Link} to="/login">
                  Back to Sign In
                </Button>
              </Box>
            </Box>
          )}
        </CardContent>
      </Card>
    </Container>
  );
};

export default ForgotPasswordPage;
