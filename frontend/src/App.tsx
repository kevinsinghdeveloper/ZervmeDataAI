import React, { useMemo } from 'react';
import { BrowserRouter, Routes, Route, Navigate, useLocation } from 'react-router-dom';
import { ThemeProvider, CssBaseline, Box } from '@mui/material';
import { ErrorBoundary } from 'react-error-boundary';
import { createAppTheme, DEFAULT_BG, DEFAULT_PAPER } from './theme/theme';
import { AuthContextProvider } from './components/context_providers/AuthContext';
import { UserContextProvider } from './components/context_providers/UserContext';
import { RBACContextProvider } from './components/context_providers/RBACContext';
import { NotificationProvider } from './components/context_providers/NotificationContext';
import { ThemeConfigProvider, useThemeConfig } from './components/context_providers/ThemeConfigContext';
import { OrganizationContextProvider } from './components/context_providers/OrganizationContext';
import { ExplorerContextProvider } from './components/context_providers/ExplorerContext';
import ProtectedRoute from './components/shared/ProtectedRoute';
import { useRBAC } from './components/context_providers/RBACContext';
import { useAuth } from './components/context_providers/AuthContext';

// Public pages
import HomePage from './components/pages/HomePage';
import LoginPage from './components/pages/LoginPage';
import RegisterPage from './components/pages/RegisterPage';
import ForgotPasswordPage from './components/pages/ForgotPasswordPage';
import ResetPasswordPage from './components/pages/ResetPasswordPage';
import ForceResetPasswordPage from './components/pages/ForceResetPasswordPage';
import OAuthCallbackPage from './components/pages/OAuthCallbackPage';
import AcceptInvitationPage from './components/pages/AcceptInvitationPage';
import VerifyEmailPage from './components/pages/VerifyEmailPage';

// App pages
import ProjectsPage from './components/pages/ProjectsPage';
import TeamPage from './components/pages/TeamPage';
import OrgSettingsPage from './components/pages/OrgSettingsPage';
import TeamManagementPage from './components/pages/TeamManagementPage';
import PersonalSettingsPage from './components/pages/PersonalSettingsPage';
import OrgSetupWizard from './components/pages/OrgSetupWizard';
import UsersPage from './components/pages/UsersPage';
import OrganizationsPage from './components/pages/OrganizationsPage';
import ExplorePage from './components/pages/ExplorePage';
import ModelsPage from './components/pages/ModelsPage';
import AIDashboardPage from './components/pages/AIDashboardPage';
import ContactPage from './components/pages/ContactPage';

// Admin pages
import GlobalAdminPage from './components/pages/GlobalAdminPage';
import SettingsPage from './components/pages/SettingsPage';

import AppLayout from './components/shared/AppLayout';
import PublicLayout from './components/shared/PublicLayout';
import './App.css';

/** Redirects authenticated users to the right default route based on role */
const SmartRedirect: React.FC = () => {
  const { isAuthenticated } = useAuth();
  const { isSuperAdmin, orgRoles } = useRBAC();
  const location = useLocation();

  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }
  // Only route to /admin if pure super admin with no org membership
  const hasOrgRoles = orgRoles.length > 0;
  return <Navigate to={isSuperAdmin && !hasOrgRoles ? '/admin' : '/explore'} replace />;
};

const ErrorFallback: React.FC<{ error: Error }> = ({ error }) => (
  <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', minHeight: '100vh', p: 3, textAlign: 'center' }}>
    <h1>Oops! Something went wrong</h1>
    <p>{error.message}</p>
    <button onClick={() => window.location.reload()}>Reload Page</button>
  </Box>
);

const ThemedApp: React.FC = () => {
  const { config } = useThemeConfig();
  const theme = useMemo(
    () => createAppTheme(
      config.colors.primary,
      config.colors.secondary,
      config.colors.background || DEFAULT_BG,
      config.colors.paper || DEFAULT_PAPER,
    ),
    [config.colors.primary, config.colors.secondary, config.colors.background, config.colors.paper]
  );

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <NotificationProvider>
        <ErrorBoundary FallbackComponent={ErrorFallback}>
          <AuthContextProvider>
            <UserContextProvider>
              <RBACContextProvider>
              <OrganizationContextProvider>
              <ExplorerContextProvider>
                <BrowserRouter basename="/">
                  <Routes>
                    {/* Public routes (with public header) */}
                    <Route element={<PublicLayout />}>
                      <Route path="/" element={<HomePage />} />
                      <Route path="/login" element={<LoginPage />} />
                      <Route path="/register" element={<RegisterPage />} />
                      <Route path="/forgot-password" element={<ForgotPasswordPage />} />
                      <Route path="/reset-password/:token" element={<ResetPasswordPage />} />
                      <Route path="/force-reset-password" element={<ForceResetPasswordPage />} />
                      <Route path="/verify-email" element={<VerifyEmailPage />} />
                      <Route path="/contact" element={<ContactPage />} />
                    </Route>
                    <Route path="/auth/callback/:provider" element={<OAuthCallbackPage />} />
                    <Route path="/accept-invitation/:token" element={<AcceptInvitationPage />} />

                    {/* Org setup */}
                    <Route path="/setup" element={<ProtectedRoute><OrgSetupWizard /></ProtectedRoute>} />

                    {/* App routes (with layout) */}
                    <Route element={<ProtectedRoute><AppLayout /></ProtectedRoute>}>
                      <Route path="/explore" element={<ExplorePage />} />
                      <Route path="/projects" element={<ProjectsPage />} />
                      <Route path="/models" element={<ModelsPage />} />
                      <Route path="/dashboard/:reportId" element={<AIDashboardPage />} />
                      <Route path="/team" element={<TeamPage />} />
                      <Route path="/org/settings" element={<OrgSettingsPage />} />
                      <Route path="/org/team" element={<TeamManagementPage />} />
                      <Route path="/org/users" element={<UsersPage />} />
                      <Route path="/settings" element={<PersonalSettingsPage />} />
                      <Route path="/organizations" element={<OrganizationsPage />} />
                      <Route path="/admin" element={<GlobalAdminPage />} />
                      <Route path="/admin/settings" element={<SettingsPage />} />
                    </Route>

                    {/* Catch-all: route to role-appropriate default */}
                    <Route path="*" element={<SmartRedirect />} />
                  </Routes>
                </BrowserRouter>
              </ExplorerContextProvider>
              </OrganizationContextProvider>
              </RBACContextProvider>
            </UserContextProvider>
          </AuthContextProvider>
        </ErrorBoundary>
      </NotificationProvider>
    </ThemeProvider>
  );
};

function App() {
  return (
    <ThemeConfigProvider>
      <ThemedApp />
    </ThemeConfigProvider>
  );
}

export default App;
