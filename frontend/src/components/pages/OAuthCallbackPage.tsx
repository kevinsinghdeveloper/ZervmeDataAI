import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Box, CircularProgress, Typography } from '@mui/material';
import { useAuth } from '../context_providers/AuthContext';
import { useNotification } from '../context_providers/NotificationContext';
import apiService from '../../utils/api.service';

const OAuthCallbackPage: React.FC = () => {
  const { provider } = useParams<{ provider: string }>();
  const navigate = useNavigate();
  const { setAuthData } = useAuth();
  const { showError } = useNotification();
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const handleCallback = async () => {
      const params = new URLSearchParams(window.location.search);
      const code = params.get('code');
      const errorParam = params.get('error');

      if (errorParam) {
        const description = params.get('error_description') || 'Authentication was cancelled or failed';
        setError(description);
        showError(description);
        setTimeout(() => navigate('/login'), 2000);
        return;
      }

      if (!code || !provider) {
        showError('Missing authentication parameters');
        navigate('/login');
        return;
      }

      try {
        const redirectUri = `${window.location.origin}/auth/callback/${provider}`;
        const res = await apiService.oauthCallback(provider, code, redirectUri);
        // res is the ResponseModel: { success, data: { user, token, accessToken, refreshToken, ... }, message }
        const authData = res.data || res;

        if (authData?.user && authData?.token) {
          setAuthData({
            token: authData.token,
            refreshToken: authData.refreshToken,
            accessToken: authData.accessToken,
            user: authData.user,
          });
          // Navigate based on user role, matching LoginPage behavior
          const role = authData.user.role;
          if (role === 'lendee') {
            navigate('/my-documents');
          } else {
            navigate('/projects');
          }
        } else {
          showError('Invalid authentication response - missing token or user data');
          navigate('/login');
        }
      } catch (err: any) {
        const message = err.message || 'OAuth authentication failed';
        setError(message);
        showError(message);
        setTimeout(() => navigate('/login'), 2000);
      }
    };

    handleCallback();
  }, [provider, navigate, setAuthData, showError]);

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', minHeight: '100vh' }}>
      {error ? (
        <>
          <Typography color="error" variant="h6" gutterBottom>
            Authentication Failed
          </Typography>
          <Typography color="text.secondary" sx={{ mb: 2 }}>
            {error}
          </Typography>
          <Typography variant="body2" color="text.disabled">
            Redirecting to login...
          </Typography>
        </>
      ) : (
        <>
          <CircularProgress size={48} />
          <Typography sx={{ mt: 2 }}>
            Signing in with {provider ? provider.charAt(0).toUpperCase() + provider.slice(1) : ''}...
          </Typography>
        </>
      )}
    </Box>
  );
};

export default OAuthCallbackPage;
