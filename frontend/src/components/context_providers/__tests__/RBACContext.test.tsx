/* eslint-disable import/first */
import React from 'react';
import { renderHook } from '@testing-library/react';

// ---------------------------------------------------------------------------
// Mocks -- must come before importing the module under test
// ---------------------------------------------------------------------------
const mockUseAuth = jest.fn();

jest.mock('../AuthContext', () => ({
  useAuth: () => mockUseAuth(),
  AuthContextProvider: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}));

// ---------------------------------------------------------------------------
// Imports after mocks
// ---------------------------------------------------------------------------
import { RBACContextProvider, useRBAC, useIsAdmin, usePermission, useHasOrgPermission } from '../RBACContext';

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------
const wrapper = ({ children }: { children: React.ReactNode }) => (
  <RBACContextProvider>{children}</RBACContextProvider>
);

function buildUser(overrides: Record<string, unknown> = {}) {
  return {
    id: 'user-1',
    email: 'test@example.com',
    firstName: 'Test',
    lastName: 'User',
    orgId: 'org-1',
    orgRole: 'member',
    isSuperAdmin: false,
    role: 'member',
    isActive: true,
    isVerified: true,
    status: 'active',
    timezone: 'America/New_York',
    createdAt: '2025-01-01T00:00:00Z',
    updatedAt: '2025-01-01T00:00:00Z',
    ...overrides,
  };
}

// ---------------------------------------------------------------------------
// Setup
// ---------------------------------------------------------------------------
beforeEach(() => {
  jest.clearAllMocks();
  mockUseAuth.mockReturnValue({ isAuthenticated: false, user: null });
});

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------
describe('RBACContext', () => {
  it('throws when useRBAC is called outside RBACContextProvider', () => {
    const spy = jest.spyOn(console, 'error').mockImplementation(() => {});
    expect(() => renderHook(() => useRBAC())).toThrow(
      'useRBAC must be used within RBACContextProvider',
    );
    spy.mockRestore();
  });

  it('returns default unauthenticated state', () => {
    const { result } = renderHook(() => useRBAC(), { wrapper });

    expect(result.current.role).toBeNull();
    expect(result.current.orgRole).toBeNull();
    expect(result.current.isSuperAdmin).toBe(false);
    expect(result.current.isAdmin).toBe(false);
    expect(result.current.isEditor).toBe(false);
    expect(result.current.isViewer).toBe(false);
    expect(result.current.isLendee).toBe(false);
    expect(result.current.isLoading).toBe(false);
  });

  it('identifies super admin correctly', () => {
    const user = buildUser({ isSuperAdmin: true, role: 'admin', orgRole: 'owner' });
    mockUseAuth.mockReturnValue({ isAuthenticated: true, user });

    const { result } = renderHook(() => useRBAC(), { wrapper });

    expect(result.current.isSuperAdmin).toBe(true);
    expect(result.current.isAdmin).toBe(true);
  });

  it('identifies owner orgRole as admin', () => {
    const user = buildUser({ orgRole: 'owner', role: 'owner' });
    mockUseAuth.mockReturnValue({ isAuthenticated: true, user });

    const { result } = renderHook(() => useRBAC(), { wrapper });

    expect(result.current.orgRole).toBe('owner');
    expect(result.current.isAdmin).toBe(true);
  });

  it('identifies admin orgRole as admin', () => {
    const user = buildUser({ orgRole: 'admin', role: 'admin' });
    mockUseAuth.mockReturnValue({ isAuthenticated: true, user });

    const { result } = renderHook(() => useRBAC(), { wrapper });

    expect(result.current.orgRole).toBe('admin');
    expect(result.current.isAdmin).toBe(true);
  });

  it('identifies manager role as non-admin', () => {
    const user = buildUser({ orgRole: 'manager', role: 'manager' });
    mockUseAuth.mockReturnValue({ isAuthenticated: true, user });

    const { result } = renderHook(() => useRBAC(), { wrapper });

    expect(result.current.orgRole).toBe('manager');
    expect(result.current.role).toBe('manager');
    expect(result.current.isAdmin).toBe(false);
  });

  it('identifies member role as non-admin', () => {
    const user = buildUser({ orgRole: 'member', role: 'member' });
    mockUseAuth.mockReturnValue({ isAuthenticated: true, user });

    const { result } = renderHook(() => useRBAC(), { wrapper });

    expect(result.current.orgRole).toBe('member');
    expect(result.current.isAdmin).toBe(false);
  });

  it('hasPermission grants wildcard access for admin role', () => {
    const user = buildUser({ role: 'admin', orgRole: 'admin' });
    mockUseAuth.mockReturnValue({ isAuthenticated: true, user });

    const { result } = renderHook(() => useRBAC(), { wrapper });

    expect(result.current.hasPermission('projects', 'read')).toBe(true);
    expect(result.current.hasPermission('anything', 'whatever')).toBe(true);
  });

  it('hasPermission restricts member to allowed resources', () => {
    const user = buildUser({ role: 'member', orgRole: 'member' });
    mockUseAuth.mockReturnValue({ isAuthenticated: true, user });

    const { result } = renderHook(() => useRBAC(), { wrapper });

    expect(result.current.hasPermission('projects', 'read')).toBe(true);
    // Members should not have wildcard access
    expect(result.current.hasPermission('anything', 'whatever')).toBe(false);
  });

  it('hasPermission returns false when unauthenticated', () => {
    const { result } = renderHook(() => useRBAC(), { wrapper });
    expect(result.current.hasPermission('anything', 'read')).toBe(false);
  });

  it('hasOrgPermission allows super admin to bypass all checks', () => {
    const user = buildUser({ isSuperAdmin: true, role: 'admin', orgRole: 'owner' });
    mockUseAuth.mockReturnValue({ isAuthenticated: true, user });

    const { result } = renderHook(() => useRBAC(), { wrapper });

    expect(result.current.hasOrgPermission('manage_billing')).toBe(true);
    expect(result.current.hasOrgPermission('manage_org')).toBe(true);
    expect(result.current.hasOrgPermission('nonexistent_perm')).toBe(true);
  });

  it('hasOrgPermission grants member only basic permissions', () => {
    const user = buildUser({ orgRole: 'member', role: 'member' });
    mockUseAuth.mockReturnValue({ isAuthenticated: true, user });

    const { result } = renderHook(() => useRBAC(), { wrapper });

    expect(result.current.hasOrgPermission('view_projects')).toBe(true);
    expect(result.current.hasOrgPermission('manage_projects')).toBe(false);
    expect(result.current.hasOrgPermission('manage_users')).toBe(false);
  });

  it('hasOrgPermission returns false when unauthenticated', () => {
    const { result } = renderHook(() => useRBAC(), { wrapper });
    expect(result.current.hasOrgPermission('view_projects')).toBe(false);
  });

  it('meetsMinOrgRole respects hierarchy ordering', () => {
    // Hierarchy: member(0) < manager(1) < admin(2) < owner(3)
    const user = buildUser({ orgRole: 'admin', role: 'admin' });
    mockUseAuth.mockReturnValue({ isAuthenticated: true, user });

    const { result } = renderHook(() => useRBAC(), { wrapper });

    expect(result.current.meetsMinOrgRole('member')).toBe(true);
    expect(result.current.meetsMinOrgRole('manager')).toBe(true);
    expect(result.current.meetsMinOrgRole('admin')).toBe(true);
    expect(result.current.meetsMinOrgRole('owner')).toBe(false);
  });

  it('meetsMinOrgRole allows super admin to pass any check', () => {
    const user = buildUser({ isSuperAdmin: true, orgRole: 'member', role: 'member' });
    mockUseAuth.mockReturnValue({ isAuthenticated: true, user });

    const { result } = renderHook(() => useRBAC(), { wrapper });

    expect(result.current.meetsMinOrgRole('owner')).toBe(true);
  });

  it('meetsMinOrgRole returns false when unauthenticated', () => {
    const { result } = renderHook(() => useRBAC(), { wrapper });
    expect(result.current.meetsMinOrgRole('member')).toBe(false);
  });

  it('resets roles on logout', () => {
    const user = buildUser({ orgRole: 'admin', role: 'admin' });
    mockUseAuth.mockReturnValue({ isAuthenticated: true, user });

    const { result, rerender } = renderHook(() => useRBAC(), { wrapper });

    expect(result.current.role).toBe('admin');
    expect(result.current.orgRole).toBe('admin');

    // Simulate logout
    mockUseAuth.mockReturnValue({ isAuthenticated: false, user: null });
    rerender();

    expect(result.current.role).toBeNull();
    expect(result.current.orgRole).toBeNull();
    expect(result.current.isSuperAdmin).toBe(false);
    expect(result.current.isAdmin).toBe(false);
  });

  // -----------------------------------------------------------------------
  // Convenience hooks
  // -----------------------------------------------------------------------
  describe('useIsAdmin', () => {
    it('returns true for admin user', () => {
      const user = buildUser({ orgRole: 'admin', role: 'admin' });
      mockUseAuth.mockReturnValue({ isAuthenticated: true, user });

      const { result } = renderHook(() => useIsAdmin(), { wrapper });
      expect(result.current).toBe(true);
    });
  });

  describe('usePermission', () => {
    it('returns permission check result', () => {
      const user = buildUser({ role: 'member', orgRole: 'member' });
      mockUseAuth.mockReturnValue({ isAuthenticated: true, user });

      const { result } = renderHook(() => usePermission('projects', 'read'), { wrapper });
      expect(result.current).toBe(true);
    });
  });

  describe('useHasOrgPermission', () => {
    it('returns org permission check result', () => {
      const user = buildUser({ orgRole: 'manager', role: 'manager' });
      mockUseAuth.mockReturnValue({ isAuthenticated: true, user });

      const { result } = renderHook(() => useHasOrgPermission('manage_projects'), { wrapper });
      expect(result.current).toBe(true);
    });
  });

  // -----------------------------------------------------------------------
  // Multi-role support (orgMemberships)
  // -----------------------------------------------------------------------
  describe('multi-role support', () => {
    beforeEach(() => {
      Storage.prototype.getItem = jest.fn((key: string) => {
        if (key === 'currentOrgId') return 'org-1';
        return null;
      });
    });

    afterEach(() => {
      jest.restoreAllMocks();
    });

    it('sets orgRoles from orgMemberships matching current org', () => {
      const user = buildUser({
        orgMemberships: [
          { orgId: 'org-1', roles: ['member', 'manager'], grantedAt: '2025-01-01T00:00:00Z' },
        ],
      });
      mockUseAuth.mockReturnValue({ isAuthenticated: true, user });

      const { result } = renderHook(() => useRBAC(), { wrapper });

      expect(result.current.orgRoles).toEqual(expect.arrayContaining(['member', 'manager']));
      expect(result.current.orgRoles).toHaveLength(2);
    });

    it('sets orgRole to highest from orgMemberships', () => {
      const user = buildUser({
        orgMemberships: [
          { orgId: 'org-1', roles: ['member', 'admin'], grantedAt: '2025-01-01T00:00:00Z' },
        ],
      });
      mockUseAuth.mockReturnValue({ isAuthenticated: true, user });

      const { result } = renderHook(() => useRBAC(), { wrapper });

      // admin is higher than member in hierarchy
      expect(result.current.orgRole).toBe('admin');
    });

    it('hasOrgPermission aggregates permissions across multiple roles', () => {
      const user = buildUser({
        orgMemberships: [
          { orgId: 'org-1', roles: ['member', 'manager'], grantedAt: '2025-01-01T00:00:00Z' },
        ],
      });
      mockUseAuth.mockReturnValue({ isAuthenticated: true, user });

      const { result } = renderHook(() => useRBAC(), { wrapper });

      // member permissions
      expect(result.current.hasOrgPermission('view_projects')).toBe(true);
      // manager permissions
      expect(result.current.hasOrgPermission('manage_projects')).toBe(true);
      // admin-only permissions should be denied
      expect(result.current.hasOrgPermission('manage_users')).toBe(false);
    });

    it('meetsMinOrgRole with multiple roles uses highest', () => {
      const user = buildUser({
        orgMemberships: [
          { orgId: 'org-1', roles: ['member', 'admin'], grantedAt: '2025-01-01T00:00:00Z' },
        ],
      });
      mockUseAuth.mockReturnValue({ isAuthenticated: true, user });

      const { result } = renderHook(() => useRBAC(), { wrapper });

      expect(result.current.meetsMinOrgRole('member')).toBe(true);
      expect(result.current.meetsMinOrgRole('manager')).toBe(true);
      expect(result.current.meetsMinOrgRole('admin')).toBe(true);
      expect(result.current.meetsMinOrgRole('owner')).toBe(false);
    });

    it('hasAnyOrgRole returns true when any role matches', () => {
      const user = buildUser({
        orgMemberships: [
          { orgId: 'org-1', roles: ['member', 'manager'], grantedAt: '2025-01-01T00:00:00Z' },
        ],
      });
      mockUseAuth.mockReturnValue({ isAuthenticated: true, user });

      const { result } = renderHook(() => useRBAC(), { wrapper });

      expect(result.current.hasAnyOrgRole(['manager', 'admin'])).toBe(true);
      expect(result.current.hasAnyOrgRole(['admin', 'owner'])).toBe(false);
    });

    it('hasAnyOrgRole returns true for super admin regardless', () => {
      const user = buildUser({
        isSuperAdmin: true,
        orgMemberships: [],
      });
      mockUseAuth.mockReturnValue({ isAuthenticated: true, user });

      const { result } = renderHook(() => useRBAC(), { wrapper });

      expect(result.current.hasAnyOrgRole(['owner'])).toBe(true);
    });

    it('falls back to inline orgRole when orgMemberships is empty', () => {
      const user = buildUser({
        orgRole: 'admin',
        role: 'admin',
        orgMemberships: [],
      });
      mockUseAuth.mockReturnValue({ isAuthenticated: true, user });

      const { result } = renderHook(() => useRBAC(), { wrapper });

      expect(result.current.orgRole).toBe('admin');
      expect(result.current.orgRoles).toEqual(['admin']);
    });

    it('falls back to inline orgRole when orgMemberships is undefined', () => {
      const user = buildUser({
        orgRole: 'manager',
        role: 'manager',
      });
      // No orgMemberships property at all
      mockUseAuth.mockReturnValue({ isAuthenticated: true, user });

      const { result } = renderHook(() => useRBAC(), { wrapper });

      expect(result.current.orgRole).toBe('manager');
      expect(result.current.orgRoles).toEqual(['manager']);
    });

    it('orgRoles empty when membership is for a different org', () => {
      Storage.prototype.getItem = jest.fn((key: string) => {
        if (key === 'currentOrgId') return 'org-999';
        return null;
      });

      const user = buildUser({
        orgRole: 'member',
        role: 'member',
        orgMemberships: [
          { orgId: 'org-1', roles: ['admin', 'owner'], grantedAt: '2025-01-01T00:00:00Z' },
        ],
      });
      mockUseAuth.mockReturnValue({ isAuthenticated: true, user });

      const { result } = renderHook(() => useRBAC(), { wrapper });

      // No matching org → falls back to inline orgRole
      expect(result.current.orgRole).toBe('member');
      expect(result.current.orgRoles).toEqual(['member']);
    });
  });
});
