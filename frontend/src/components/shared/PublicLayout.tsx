import React from 'react';
import { Box } from '@mui/material';
import { Outlet } from 'react-router-dom';
import PublicHeader from './PublicHeader';

const PublicLayout: React.FC = () => (
  <Box sx={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
    <PublicHeader />
    <Box sx={{ flex: 1 }}>
      <Outlet />
    </Box>
  </Box>
);

export default PublicLayout;
