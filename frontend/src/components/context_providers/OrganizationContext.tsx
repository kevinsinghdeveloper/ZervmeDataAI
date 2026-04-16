import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { Organization, OrgInvite, OrgRole } from '../../types';
import { useAuth } from './AuthContext';
import apiService from '../../utils/api.service';

interface OrganizationContextType {
  organization: Organization | null;
  organizations: Organization[];
  activeOrgId: string | null;
  isLoading: boolean;
  error: string | null;
  fetchOrganization: () => Promise<void>;
  fetchOrganizations: () => Promise<void>;
  switchOrg: (orgId: string) => void;
  updateOrganization: (data: Partial<Organization>) => Promise<void>;
  invitations: OrgInvite[];
  fetchInvitations: () => Promise<void>;
  sendInvitation: (email: string, role: OrgRole) => Promise<void>;
  revokeInvitation: (id: string) => Promise<void>;
}

const OrganizationContext = createContext<OrganizationContextType | undefined>(undefined);

export const useOrganization = () => {
  const context = useContext(OrganizationContext);
  if (!context) throw new Error('useOrganization must be used within OrganizationContextProvider');
  return context;
};

export const OrganizationContextProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { isAuthenticated, user } = useAuth();
  // Read isSuperAdmin directly from user to avoid RBAC timing delay
  const isSuperAdmin = !!user?.isSuperAdmin;
  const [organization, setOrganization] = useState<Organization | null>(null);
  const [organizations, setOrganizations] = useState<Organization[]>([]);
  const [activeOrgId, setActiveOrgId] = useState<string | null>(
    localStorage.getItem('currentOrgId')
  );
  const [invitations, setInvitations] = useState<OrgInvite[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchOrganization = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await apiService.getCurrentOrg();
      const raw = response.data || response;
      setOrganization(raw?.organization || raw);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const fetchIdRef = React.useRef(0);
  const fetchOrganizations = useCallback(async () => {
    const fetchId = ++fetchIdRef.current;
    try {
      let raw: any;
      if (isSuperAdmin) {
        // Super admins see all orgs in the system
        const response = await apiService.superAdminListOrgs(1, 200);
        raw = response.data || response;
        // superAdminListOrgs returns { organizations: [...] } or array
        raw = Array.isArray(raw) ? raw : (raw?.organizations || []);
      } else {
        const response = await apiService.listMyOrgs();
        raw = response.data || response;
        raw = Array.isArray(raw) ? raw : (raw?.organizations || []);
      }
      // Only apply result if this is still the latest fetch
      if (fetchId === fetchIdRef.current) {
        setOrganizations(raw);
      }
    } catch {
      // Silently fail — user may not have multi-org endpoint yet
    }
  }, [isSuperAdmin]);

  const switchOrg = useCallback((orgId: string) => {
    localStorage.setItem('currentOrgId', orgId);
    setActiveOrgId(orgId);
    // Dispatch event so RBACContext and other contexts re-sync
    window.dispatchEvent(new Event('org-switched'));
    // Re-fetch current org data
    fetchOrganization();
  }, [fetchOrganization]);

  const updateOrganization = useCallback(async (data: Partial<Organization>) => {
    try {
      await apiService.updateOrg(data);
      await fetchOrganization();
    } catch (err: any) {
      setError(err.message);
      throw err;
    }
  }, [fetchOrganization]);

  const fetchInvitations = useCallback(async () => {
    try {
      const response = await apiService.listOrgInvitations();
      const raw = response.data || response;
      setInvitations(Array.isArray(raw) ? raw : (raw?.invitations || []));
    } catch (err: any) {
      setError(err.message);
    }
  }, []);

  const sendInvitation = useCallback(async (email: string, role: OrgRole) => {
    try {
      await apiService.createOrgInvitation(email, role);
      await fetchInvitations();
    } catch (err: any) {
      setError(err.message);
      throw err;
    }
  }, [fetchInvitations]);

  const revokeInvitation = useCallback(async (id: string) => {
    try {
      await apiService.deleteOrgInvitation(id);
      await fetchInvitations();
    } catch (err: any) {
      setError(err.message);
      throw err;
    }
  }, [fetchInvitations]);

  useEffect(() => {
    if (isAuthenticated) {
      fetchOrganizations();
      // Fetch current org if user has an active org (including super admins with an org selected)
      if (activeOrgId) {
        fetchOrganization();
      }
    } else {
      setOrganization(null);
      setOrganizations([]);
      setInvitations([]);
    }
  }, [isAuthenticated, activeOrgId, fetchOrganization, fetchOrganizations]);

  return (
    <OrganizationContext.Provider value={{
      organization, organizations, activeOrgId, isLoading, error,
      fetchOrganization, fetchOrganizations, switchOrg, updateOrganization,
      invitations, fetchInvitations, sendInvitation, revokeInvitation,
    }}>
      {children}
    </OrganizationContext.Provider>
  );
};
