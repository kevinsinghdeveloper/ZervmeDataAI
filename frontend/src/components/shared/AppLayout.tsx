import React, { useState, useEffect, useCallback } from 'react';
import { Outlet, useNavigate, useLocation } from 'react-router-dom';
import {
  Box, Drawer, List, ListItemButton, ListItemIcon, ListItemText,
  AppBar, Toolbar, Typography, IconButton, Avatar, Badge, Tooltip,
  Divider, useMediaQuery, useTheme, Menu, MenuItem,
} from '@mui/material';
import {
  Folder as ProjectIcon,
  People as TeamIcon,
  Settings as SettingsIcon,
  Menu as MenuIcon,
  Notifications as NotifIcon,
  SmartToy as AIIcon,
  Business as OrgIcon,
  Shield as ShieldIcon,
  Logout as LogoutIcon,
  Person as PersonIcon,
  Explore as ExploreIcon,
  Hub as ModelsIcon,
} from '@mui/icons-material';
import AIChatDrawer from './AIChatDrawer';
import NotificationPanel from './NotificationPanel';
import OrgSwitcher from './OrgSwitcher';
import { useBrowserTitle } from '../../hooks/useBrowserTitle';
import { useRBAC } from '../context_providers/RBACContext';
import { useAuth } from '../context_providers/AuthContext';
import { useOrganization } from '../context_providers/OrganizationContext';
import apiService from '../../utils/api.service';

const DRAWER_WIDTH = 240;

const orgNavItems = [
  { label: 'Explore', icon: <ExploreIcon />, path: '/explore' },
  { label: 'Projects', icon: <ProjectIcon />, path: '/projects' },
  { label: 'Models', icon: <ModelsIcon />, path: '/models' },
  { label: 'Team', icon: <TeamIcon />, path: '/org/team' },
];

const orgBottomNavItems = [
  { label: 'Org Settings', icon: <OrgIcon />, path: '/org/settings' },
  { label: 'Settings', icon: <SettingsIcon />, path: '/settings' },
];

const superAdminNavItems = [
  { label: 'Admin', icon: <ShieldIcon />, path: '/admin' },
  { label: 'System Settings', icon: <SettingsIcon />, path: '/admin/settings' },
];

const superAdminBottomNavItems = [
  { label: 'Settings', icon: <SettingsIcon />, path: '/settings' },
];

const AppLayout: React.FC = () => {
  const [mobileOpen, setMobileOpen] = useState(false);
  const [chatOpen, setChatOpen] = useState(false);
  const [profileAnchor, setProfileAnchor] = useState<null | HTMLElement>(null);
  const [notifAnchor, setNotifAnchor] = useState<null | HTMLElement>(null);
  const [unreadCount, setUnreadCount] = useState(0);
  const navigate = useNavigate();
  const location = useLocation();
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));
  const { isSuperAdmin, orgRoles } = useRBAC();
  const { user, logout } = useAuth();
  const { organizations } = useOrganization();
  const hasOrgRoles = orgRoles.length > 0;
  useBrowserTitle();

  const fetchUnreadCount = useCallback(async () => {
    try {
      const res = await apiService.getUnreadNotificationCount();
      const data = res.data || res;
      setUnreadCount(typeof data === 'number' ? data : (data?.count ?? 0));
    } catch {
      // Non-critical
    }
  }, []);

  useEffect(() => {
    fetchUnreadCount();
    const interval = setInterval(fetchUnreadCount, 60000);
    return () => clearInterval(interval);
  }, [fetchUnreadCount]);

  const userInitials = [user?.firstName?.[0], user?.lastName?.[0]].filter(Boolean).join('').toUpperCase() || '?';

  const handleLogout = () => {
    setProfileAnchor(null);
    logout();
    navigate('/login');
  };

  const navItems = [
    ...(hasOrgRoles ? orgNavItems : []),
    ...(isSuperAdmin || organizations.length > 1 ? [{ label: 'Organizations', icon: <OrgIcon />, path: '/organizations' }] : []),
    ...(isSuperAdmin ? superAdminNavItems : []),
  ];
  const bottomItems = hasOrgRoles ? orgBottomNavItems : (isSuperAdmin ? superAdminBottomNavItems : []);

  const drawer = (
    <Box sx={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      <Toolbar sx={{ justifyContent: 'center' }}>
        <Typography variant="h6" sx={{ fontWeight: 700, color: 'primary.main' }}>
          Zerve Data AI
        </Typography>
      </Toolbar>
      <OrgSwitcher />
      <Divider />
      <List sx={{ flex: 1 }}>
        {navItems.map((item) => (
          <ListItemButton
            key={item.path}
            selected={location.pathname === item.path}
            onClick={() => { navigate(item.path); if (isMobile) setMobileOpen(false); }}
            sx={{ borderRadius: 1, mx: 1, mb: 0.5 }}
          >
            <ListItemIcon sx={{ minWidth: 40 }}>{item.icon}</ListItemIcon>
            <ListItemText primary={item.label} />
          </ListItemButton>
        ))}
      </List>
      <Divider />
      <List>
        {bottomItems.map((item) => (
          <ListItemButton
            key={item.path}
            selected={location.pathname === item.path}
            onClick={() => { navigate(item.path); if (isMobile) setMobileOpen(false); }}
            sx={{ borderRadius: 1, mx: 1, mb: 0.5 }}
          >
            <ListItemIcon sx={{ minWidth: 40 }}>{item.icon}</ListItemIcon>
            <ListItemText primary={item.label} />
          </ListItemButton>
        ))}
      </List>
    </Box>
  );

  return (
    <Box sx={{ display: 'flex', minHeight: '100vh' }}>
      {/* Top bar */}
      <AppBar position="fixed" sx={{ zIndex: theme.zIndex.drawer + 1 }}>
        <Toolbar>
          {isMobile && (
            <IconButton color="inherit" edge="start" onClick={() => setMobileOpen(!mobileOpen)} sx={{ mr: 2 }}>
              <MenuIcon />
            </IconButton>
          )}
          <Typography variant="h6" noWrap sx={{ flexGrow: 1, fontWeight: 700 }}>
            Zerve Data AI
          </Typography>
          <Tooltip title="AI Assistant">
            <IconButton color="inherit" onClick={() => setChatOpen(!chatOpen)}><AIIcon /></IconButton>
          </Tooltip>
          <Tooltip title="Notifications">
            <IconButton color="inherit" onClick={(e) => setNotifAnchor(e.currentTarget)}>
              <Badge badgeContent={unreadCount} color="error"><NotifIcon /></Badge>
            </IconButton>
          </Tooltip>
          <Tooltip title="Profile">
            <IconButton sx={{ ml: 1 }} onClick={(e) => setProfileAnchor(e.currentTarget)}>
              <Avatar sx={{ width: 32, height: 32, fontSize: 14, bgcolor: 'primary.main' }}>{userInitials}</Avatar>
            </IconButton>
          </Tooltip>
          <Menu
            anchorEl={profileAnchor}
            open={Boolean(profileAnchor)}
            onClose={() => setProfileAnchor(null)}
            transformOrigin={{ horizontal: 'right', vertical: 'top' }}
            anchorOrigin={{ horizontal: 'right', vertical: 'bottom' }}
            slotProps={{ paper: { sx: { minWidth: 220, mt: 1 } } }}
          >
            <MenuItem disabled sx={{ opacity: '1 !important', flexDirection: 'column', alignItems: 'flex-start', py: 1.5 }}>
              <Typography variant="subtitle2">{user?.firstName} {user?.lastName}</Typography>
              <Typography variant="caption" color="text.secondary">{user?.email}</Typography>
            </MenuItem>
            <Divider />
            <MenuItem onClick={() => { setProfileAnchor(null); navigate('/settings'); }}>
              <ListItemIcon><PersonIcon fontSize="small" /></ListItemIcon>
              Profile
            </MenuItem>
            <Divider />
            <MenuItem onClick={handleLogout}>
              <ListItemIcon><LogoutIcon fontSize="small" /></ListItemIcon>
              Logout
            </MenuItem>
          </Menu>
        </Toolbar>
      </AppBar>

      {/* Sidebar */}
      {isMobile ? (
        <Drawer variant="temporary" open={mobileOpen} onClose={() => setMobileOpen(false)}
          ModalProps={{ keepMounted: true }}
          sx={{ '& .MuiDrawer-paper': { width: DRAWER_WIDTH } }}>
          {drawer}
        </Drawer>
      ) : (
        <Drawer variant="permanent"
          sx={{ width: DRAWER_WIDTH, flexShrink: 0, '& .MuiDrawer-paper': { width: DRAWER_WIDTH, boxSizing: 'border-box' } }}>
          {drawer}
        </Drawer>
      )}

      {/* Main content */}
      <Box component="main" sx={{ flexGrow: 1, pt: 8, minHeight: '100vh' }}>
        <Outlet />
      </Box>

      {/* Notification Panel */}
      <NotificationPanel
        anchorEl={notifAnchor}
        onClose={() => setNotifAnchor(null)}
        onCountChange={setUnreadCount}
      />

      {/* AI Chat Drawer */}
      <AIChatDrawer open={chatOpen} onClose={() => setChatOpen(false)} />
    </Box>
  );
};

export default AppLayout;
