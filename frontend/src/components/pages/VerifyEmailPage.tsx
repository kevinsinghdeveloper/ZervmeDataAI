import React, { useState } from 'react';
import { Container, Typography, Box, Card, CardContent, Button, TextField, CircularProgress } from '@mui/material';
import { CheckCircle, Error as ErrorIcon } from '@mui/icons-material';
import { useNavigate, useSearchParams } from 'react-router-dom';
import apiService from '../../utils/api.service';

type VerificationStatus = 'form' | 'loading' | 'success' | 'error';

const VerifyEmailPage: React.FC = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [status, setStatus] = useState<VerificationStatus>('form');
  const [message, setMessage] = useState('');
  const [email, setEmail] = useState(searchParams.get('email') || '');
  const [code, setCode] = useState('');

  const handleVerify = async () => {
    if (!email || !code) {
      setStatus('error');
      setMessage('Email and verification code are required.');
      return;
    }

    setStatus('loading');
    try {
      await apiService.verifyEmail(email, code);
      setStatus('success');
      setMessage('Your email has been verified successfully. You can now sign in to your account.');
    } catch (err: any) {
      setStatus('error');
      setMessage(err.message || 'Email verification failed. The code may have expired or is invalid.');
    }
  };

  return (
    <Container maxWidth="sm" sx={{ py: 8 }}>
      <Card>
        <CardContent sx={{ p: 4, textAlign: 'center' }}>
          {status === 'form' && (
            <Box sx={{ py: 2 }}>
              <Typography variant="h5" gutterBottom>Verify Your Email</Typography>
              <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
                Enter the verification code sent to your email address.
              </Typography>
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                <TextField
                  label="Email"
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  fullWidth
                />
                <TextField
                  label="Verification Code"
                  value={code}
                  onChange={(e) => setCode(e.target.value)}
                  fullWidth
                  autoFocus
                />
                <Button variant="contained" size="large" onClick={handleVerify}>
                  Verify Email
                </Button>
              </Box>
            </Box>
          )}

          {status === 'loading' && (
            <Box sx={{ py: 4 }}>
              <CircularProgress size={64} sx={{ mb: 3 }} />
              <Typography variant="h5" gutterBottom>Verifying your email...</Typography>
              <Typography variant="body1" color="text.secondary">
                Please wait while we verify your email address.
              </Typography>
            </Box>
          )}

          {status === 'success' && (
            <Box sx={{ py: 4 }}>
              <CheckCircle sx={{ fontSize: 64, color: 'success.main', mb: 2 }} />
              <Typography variant="h5" gutterBottom>Email Verified</Typography>
              <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
                {message}
              </Typography>
              <Button variant="contained" size="large" onClick={() => navigate('/login')}>
                Go to Sign In
              </Button>
            </Box>
          )}

          {status === 'error' && (
            <Box sx={{ py: 4 }}>
              <ErrorIcon sx={{ fontSize: 64, color: 'error.main', mb: 2 }} />
              <Typography variant="h5" gutterBottom>Verification Failed</Typography>
              <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
                {message}
              </Typography>
              <Box sx={{ display: 'flex', gap: 2, justifyContent: 'center' }}>
                <Button variant="contained" onClick={() => setStatus('form')}>
                  Try Again
                </Button>
                <Button variant="outlined" onClick={() => navigate('/login')}>
                  Go to Sign In
                </Button>
              </Box>
            </Box>
          )}
        </CardContent>
      </Card>
    </Container>
  );
};

export default VerifyEmailPage;
