import React, { useEffect, useState } from 'react';
import {
  Box, Container, Typography, Button, Card, CardContent,
  CircularProgress, Alert,
} from '@mui/material';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../context_providers/AuthContext';
import apiService from '../../utils/api.service';

const AcceptInvitationPage: React.FC = () => {
  const { token } = useParams<{ token: string }>();
  const navigate = useNavigate();
  const { isAuthenticated, user } = useAuth();
  const [loading, setLoading] = useState(true);
  const [joining, setJoining] = useState(false);
  const [error, setError] = useState('');
  const [inviteData, setInviteData] = useState<{ orgId: string; role: string; email: string } | null>(null);

  useEffect(() => {
    if (!token) {
      setError('Invalid invitation link');
      setLoading(false);
      return;
    }

    // If authenticated, accept invitation immediately to link user to org
    if (isAuthenticated && user) {
      setJoining(true);
      apiService.acceptInvitation(token)
        .then((resp) => {
          const data = resp.data || resp;
          if (data.orgId) {
            localStorage.setItem('currentOrgId', data.orgId);
            // Update stored user with new org info
            const storedUser = localStorage.getItem('user');
            if (storedUser) {
              const parsed = JSON.parse(storedUser);
              parsed.orgId = data.orgId;
              parsed.orgRole = data.role;
              localStorage.setItem('user', JSON.stringify(parsed));
            }
          }
          navigate('/projects');
        })
        .catch((err) => {
          setError(err.message || 'Failed to accept invitation');
          setJoining(false);
        });
      return;
    }

    // Not authenticated — validate token to show org info
    apiService.acceptInvitation(token)
      .then((resp) => {
        const data = resp.data || resp;
        setInviteData(data);
      })
      .catch((err) => {
        setError(err.message || 'Invalid or expired invitation');
      })
      .finally(() => setLoading(false));
  }, [token, isAuthenticated, user, navigate]);

  if (loading || joining) {
    return (
      <Container maxWidth="sm" sx={{ py: 8, textAlign: 'center' }}>
        <CircularProgress />
        <Typography sx={{ mt: 2 }}>
          {joining ? 'Joining organization...' : 'Validating invitation...'}
        </Typography>
      </Container>
    );
  }

  if (error) {
    return (
      <Container maxWidth="sm" sx={{ py: 8 }}>
        <Card>
          <CardContent sx={{ p: 4, textAlign: 'center' }}>
            <Typography variant="h5" gutterBottom>Invitation Error</Typography>
            <Alert severity="error" sx={{ mb: 3 }}>{error}</Alert>
            <Button variant="contained" component={Link} to="/login">Go to Login</Button>
          </CardContent>
        </Card>
      </Container>
    );
  }

  return (
    <Container maxWidth="sm" sx={{ py: 8 }}>
      <Card>
        <CardContent sx={{ p: 4, textAlign: 'center' }}>
          <Typography variant="h4" gutterBottom>You're Invited!</Typography>
          <Typography variant="body1" color="text.secondary" sx={{ mb: 1 }}>
            You've been invited to join an organization as <strong>{inviteData?.role}</strong>.
          </Typography>
          {inviteData?.email && (
            <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
              Invitation sent to: {inviteData.email}
            </Typography>
          )}
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
            <Button
              variant="contained"
              size="large"
              component={Link}
              to={`/register?invitation=${token}`}
            >
              Create Account & Join
            </Button>
            <Button
              variant="outlined"
              size="large"
              component={Link}
              to={`/login?invitation=${token}`}
            >
              Sign In & Join
            </Button>
          </Box>
        </CardContent>
      </Card>
    </Container>
  );
};

export default AcceptInvitationPage;
