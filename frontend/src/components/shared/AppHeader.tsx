import React, { useState } from 'react';
import { AppBar, Toolbar, Typography, Button, Box, IconButton, Menu, MenuItem } from '@mui/material';
import { AccountCircle } from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context_providers/AuthContext';
import { useRBAC } from '../context_providers/RBACContext';
import { useThemeConfig } from '../context_providers/ThemeConfigContext';

const AppHeader: React.FC = () => {
  const navigate = useNavigate();
  const { isAuthenticated, user, logout } = useAuth();
  const { isAdmin, isLendee } = useRBAC();
  const { config } = useThemeConfig();
  const [anchorEl, setAnchorEl] = React.useState<null | HTMLElement>(null);
  const [logoError, setLogoError] = useState(false);

  const handleLogout = () => {
    setAnchorEl(null);
    logout();
    navigate('/');
  };

  return (
    <AppBar position="sticky" sx={{ bgcolor: 'background.paper', borderBottom: 1, borderColor: 'divider' }}>
      <Toolbar>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, cursor: 'pointer' }} onClick={() => navigate('/')}>
          {config.logo && !logoError && (
            <img src={config.logo} alt="Logo" style={{ height: 32, objectFit: 'contain' }} onError={() => setLogoError(true)} />
          )}
          <Typography variant="h6" sx={{ fontWeight: 700 }}>
            {config.appName}
          </Typography>
        </Box>
        <Box sx={{ flexGrow: 1 }} />
        {isAuthenticated ? (
          <>
            {isAdmin && (
              <>
                <Button color="inherit" onClick={() => navigate('/projects')}>Dashboard</Button>
                <Button color="inherit" onClick={() => navigate('/admin/users')}>Lendees</Button>
                <Button color="inherit" onClick={() => navigate('/admin/upload')}>Upload Users</Button>
                <Button color="inherit" onClick={() => navigate('/admin/pipelines')}>Pipelines</Button>
                <Button color="inherit" onClick={() => navigate('/settings')}>Settings</Button>
              </>
            )}
            {isLendee && (
              <Button color="inherit" onClick={() => navigate('/my-documents')}>My Documents</Button>
            )}
            <IconButton color="inherit" onClick={(e) => setAnchorEl(e.currentTarget)}>
              <AccountCircle />
            </IconButton>
            <Menu anchorEl={anchorEl} open={Boolean(anchorEl)} onClose={() => setAnchorEl(null)}>
              <MenuItem disabled>{user?.email}</MenuItem>
              <MenuItem disabled sx={{ fontSize: '0.8rem', opacity: 0.7 }}>
                Role: {user?.role || 'unknown'}
              </MenuItem>
              <MenuItem onClick={handleLogout}>Logout</MenuItem>
            </Menu>
          </>
        ) : (
          <Button color="inherit" onClick={() => navigate('/login')}>Login</Button>
        )}
      </Toolbar>
    </AppBar>
  );
};

export default AppHeader;
