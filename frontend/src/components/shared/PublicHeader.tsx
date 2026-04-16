import React from 'react';
import { AppBar, Toolbar, Typography, Button, Box, Container } from '@mui/material';
import { useNavigate, useLocation } from 'react-router-dom';
import { SmartToy as AIIcon } from '@mui/icons-material';
import { useAuth } from '../context_providers/AuthContext';

const PublicHeader: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { isAuthenticated } = useAuth();

  const isActive = (path: string) => location.pathname === path;

  return (
    <AppBar
      position="sticky"
      elevation={0}
      sx={{
        backgroundColor: 'background.paper',
        borderBottom: '1px solid',
        borderColor: 'divider',
      }}
    >
      <Container maxWidth="lg">
        <Toolbar disableGutters sx={{ minHeight: 64 }}>
          <Box
            sx={{ display: 'flex', alignItems: 'center', cursor: 'pointer', mr: 4 }}
            onClick={() => navigate('/')}
          >
            <AIIcon sx={{ color: 'primary.main', mr: 1, fontSize: 28 }} />
            <Typography
              variant="h6"
              sx={{ fontWeight: 700, color: 'text.primary', letterSpacing: '-0.5px' }}
            >
              Zerve Data AI
            </Typography>
          </Box>

          <Box sx={{ flexGrow: 1, display: 'flex', gap: 1 }}>
            <Button
              color={isActive('/') ? 'primary' : 'inherit'}
              onClick={() => navigate('/')}
              sx={{ color: isActive('/') ? 'primary.main' : 'text.secondary', textTransform: 'none' }}
            >
              Home
            </Button>
          </Box>

          <Box sx={{ display: 'flex', gap: 1 }}>
            {isAuthenticated ? (
              <Button
                variant="contained"
                onClick={() => navigate('/projects')}
                sx={{ textTransform: 'none', borderRadius: 2 }}
              >
                Go to App
              </Button>
            ) : (
              <>
                <Button
                  onClick={() => navigate('/login')}
                  sx={{ color: 'text.primary', textTransform: 'none' }}
                >
                  Sign In
                </Button>
                <Button
                  variant="contained"
                  onClick={() => navigate('/register')}
                  sx={{ textTransform: 'none', borderRadius: 2 }}
                >
                  Get Started
                </Button>
              </>
            )}
          </Box>
        </Toolbar>
      </Container>
    </AppBar>
  );
};

export default PublicHeader;
