/* eslint-disable import/first, testing-library/no-wait-for-multiple-assertions */
import React from 'react';
import { renderHook, act, waitFor } from '@testing-library/react';

// ---------------------------------------------------------------------------
// Mocks -- must come before importing the module under test
// ---------------------------------------------------------------------------
const mockUseAuth = jest.fn();
const mockUseRBAC = jest.fn();

jest.mock('../AuthContext', () => ({
  useAuth: () => mockUseAuth(),
  AuthContextProvider: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}));

jest.mock('../RBACContext', () => ({
  useRBAC: () => mockUseRBAC(),
  RBACContextProvider: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}));

jest.mock('../../../utils/api.service', () => ({
  __esModule: true,
  default: {
    getCurrentOrg: jest.fn(),
    updateOrg: jest.fn(),
    listOrgInvitations: jest.fn(),
    createOrgInvitation: jest.fn(),
    deleteOrgInvitation: jest.fn(),
    listMyOrgs: jest.fn().mockResolvedValue({ data: [] }),
    superAdminListOrgs: jest.fn().mockResolvedValue({ data: [] }),
  },
}));

// ---------------------------------------------------------------------------
// Imports after mocks
// ---------------------------------------------------------------------------
import { OrganizationContextProvider, useOrganization } from '../OrganizationContext';
import apiService from '../../../utils/api.service';

// ---------------------------------------------------------------------------
// Fixtures
// ---------------------------------------------------------------------------
const mockOrg = {
  id: 'org-1',
  name: 'Test Org',
  slug: 'test-org',
  ownerId: 'user-1',
  memberCount: 3,
  isActive: true,
  createdAt: '2025-01-01T00:00:00Z',
  updatedAt: '2025-01-01T00:00:00Z',
};

const mockInvitations = [
  {
    id: 'inv-1',
    orgId: 'org-1',
    email: 'invited@example.com',
    role: 'member' as const,
    status: 'pending' as const,
    invitedBy: 'user-1',
    expiresAt: '2025-12-31T00:00:00Z',
    createdAt: '2025-01-01T00:00:00Z',
  },
];

const wrapper = ({ children }: { children: React.ReactNode }) => (
  <OrganizationContextProvider>{children}</OrganizationContextProvider>
);

// ---------------------------------------------------------------------------
// Setup
// ---------------------------------------------------------------------------
beforeEach(() => {
  jest.clearAllMocks();
  localStorage.setItem('currentOrgId', 'org-1');
  mockUseAuth.mockReturnValue({ isAuthenticated: false });
  mockUseRBAC.mockReturnValue({ isSuperAdmin: false });
});

afterEach(() => {
  localStorage.clear();
});

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------
describe('OrganizationContext', () => {
  it('throws when useOrganization is called outside OrganizationContextProvider', () => {
    const spy = jest.spyOn(console, 'error').mockImplementation(() => {});
    expect(() => renderHook(() => useOrganization())).toThrow(
      'useOrganization must be used within OrganizationContextProvider',
    );
    spy.mockRestore();
  });

  it('has correct initial state when not authenticated', () => {
    const { result } = renderHook(() => useOrganization(), { wrapper });

    expect(result.current.organization).toBeNull();
    expect(result.current.invitations).toEqual([]);
    expect(result.current.isLoading).toBe(false);
    expect(result.current.error).toBeNull();
  });

  it('fetches organization when isAuthenticated becomes true', async () => {
    mockUseAuth.mockReturnValue({ isAuthenticated: true });
    (apiService.getCurrentOrg as jest.Mock).mockResolvedValue({ data: { organization: mockOrg } });

    const { result } = renderHook(() => useOrganization(), { wrapper });

    await waitFor(() => {
      expect(result.current.organization).toEqual(mockOrg);
    });
    expect(apiService.getCurrentOrg).toHaveBeenCalledTimes(1);
  });

  it('skips fetch when user is super admin with no active org', async () => {
    localStorage.removeItem('currentOrgId');
    mockUseAuth.mockReturnValue({ isAuthenticated: true });
    mockUseRBAC.mockReturnValue({ isSuperAdmin: true });

    const { result } = renderHook(() => useOrganization(), { wrapper });

    // Give any potential async operations time to settle
    await act(async () => {
      await new Promise((r) => setTimeout(r, 50));
    });

    expect(result.current.organization).toBeNull();
    expect(apiService.getCurrentOrg).not.toHaveBeenCalled();
  });

  it('sets error when fetchOrganization fails', async () => {
    mockUseAuth.mockReturnValue({ isAuthenticated: true });
    (apiService.getCurrentOrg as jest.Mock).mockRejectedValue(new Error('Server error'));

    const { result } = renderHook(() => useOrganization(), { wrapper });

    await waitFor(() => {
      expect(result.current.error).toBe('Server error');
    });
    expect(result.current.organization).toBeNull();
    expect(result.current.isLoading).toBe(false);
  });

  it('handles response without nested organization property', async () => {
    mockUseAuth.mockReturnValue({ isAuthenticated: true });
    // Some responses come as { data: orgObject } without the .organization wrapper
    (apiService.getCurrentOrg as jest.Mock).mockResolvedValue({ data: mockOrg });

    const { result } = renderHook(() => useOrganization(), { wrapper });

    await waitFor(() => {
      expect(result.current.organization).toEqual(mockOrg);
    });
  });

  it('updateOrganization calls API and refetches', async () => {
    mockUseAuth.mockReturnValue({ isAuthenticated: true });
    (apiService.getCurrentOrg as jest.Mock).mockResolvedValue({ data: { organization: mockOrg } });

    const { result } = renderHook(() => useOrganization(), { wrapper });

    await waitFor(() => {
      expect(result.current.organization).toEqual(mockOrg);
    });

    const updatedOrg = { ...mockOrg, name: 'Updated Org' };
    (apiService.updateOrg as jest.Mock).mockResolvedValue({ success: true });
    (apiService.getCurrentOrg as jest.Mock).mockResolvedValue({ data: { organization: updatedOrg } });

    await act(async () => {
      await result.current.updateOrganization({ name: 'Updated Org' });
    });

    expect(apiService.updateOrg).toHaveBeenCalledWith({ name: 'Updated Org' });
    // getCurrentOrg called once on mount + once after update
    expect(apiService.getCurrentOrg).toHaveBeenCalledTimes(2);
  });

  it('updateOrganization sets error and rethrows on failure', async () => {
    mockUseAuth.mockReturnValue({ isAuthenticated: true });
    (apiService.getCurrentOrg as jest.Mock).mockResolvedValue({ data: { organization: mockOrg } });

    const { result } = renderHook(() => useOrganization(), { wrapper });

    await waitFor(() => {
      expect(result.current.organization).toEqual(mockOrg);
    });

    (apiService.updateOrg as jest.Mock).mockRejectedValue(new Error('Update failed'));

    let thrown: Error | undefined;
    await act(async () => {
      try {
        await result.current.updateOrganization({ name: 'Bad' });
      } catch (e) {
        thrown = e as Error;
      }
    });

    expect(thrown?.message).toBe('Update failed');
    expect(result.current.error).toBe('Update failed');
  });

  it('fetchInvitations populates invitations array', async () => {
    mockUseAuth.mockReturnValue({ isAuthenticated: true });
    (apiService.getCurrentOrg as jest.Mock).mockResolvedValue({ data: { organization: mockOrg } });
    (apiService.listOrgInvitations as jest.Mock).mockResolvedValue({ data: { invitations: mockInvitations } });

    const { result } = renderHook(() => useOrganization(), { wrapper });

    await waitFor(() => {
      expect(result.current.organization).toEqual(mockOrg);
    });

    await act(async () => {
      await result.current.fetchInvitations();
    });

    expect(result.current.invitations).toEqual(mockInvitations);
  });

  it('fetchInvitations handles direct array response', async () => {
    mockUseAuth.mockReturnValue({ isAuthenticated: true });
    (apiService.getCurrentOrg as jest.Mock).mockResolvedValue({ data: { organization: mockOrg } });
    // Response where data is directly an array
    (apiService.listOrgInvitations as jest.Mock).mockResolvedValue({ data: mockInvitations });

    const { result } = renderHook(() => useOrganization(), { wrapper });

    await waitFor(() => {
      expect(result.current.organization).toEqual(mockOrg);
    });

    await act(async () => {
      await result.current.fetchInvitations();
    });

    expect(result.current.invitations).toEqual(mockInvitations);
  });

  it('sendInvitation calls API and refetches invitations', async () => {
    mockUseAuth.mockReturnValue({ isAuthenticated: true });
    (apiService.getCurrentOrg as jest.Mock).mockResolvedValue({ data: { organization: mockOrg } });
    (apiService.createOrgInvitation as jest.Mock).mockResolvedValue({ success: true });
    (apiService.listOrgInvitations as jest.Mock).mockResolvedValue({ data: { invitations: mockInvitations } });

    const { result } = renderHook(() => useOrganization(), { wrapper });

    await waitFor(() => {
      expect(result.current.organization).toEqual(mockOrg);
    });

    await act(async () => {
      await result.current.sendInvitation('new@example.com', 'member');
    });

    expect(apiService.createOrgInvitation).toHaveBeenCalledWith('new@example.com', 'member');
    expect(apiService.listOrgInvitations).toHaveBeenCalled();
  });

  it('sendInvitation sets error and rethrows on failure', async () => {
    mockUseAuth.mockReturnValue({ isAuthenticated: true });
    (apiService.getCurrentOrg as jest.Mock).mockResolvedValue({ data: { organization: mockOrg } });

    const { result } = renderHook(() => useOrganization(), { wrapper });

    await waitFor(() => {
      expect(result.current.organization).toEqual(mockOrg);
    });

    (apiService.createOrgInvitation as jest.Mock).mockRejectedValue(new Error('Invitation failed'));

    let thrown: Error | undefined;
    await act(async () => {
      try {
        await result.current.sendInvitation('bad@example.com', 'member');
      } catch (e) {
        thrown = e as Error;
      }
    });

    expect(thrown?.message).toBe('Invitation failed');
    expect(result.current.error).toBe('Invitation failed');
  });

  it('revokeInvitation calls API and refetches invitations', async () => {
    mockUseAuth.mockReturnValue({ isAuthenticated: true });
    (apiService.getCurrentOrg as jest.Mock).mockResolvedValue({ data: { organization: mockOrg } });
    (apiService.deleteOrgInvitation as jest.Mock).mockResolvedValue({ success: true });
    (apiService.listOrgInvitations as jest.Mock).mockResolvedValue({ data: { invitations: [] } });

    const { result } = renderHook(() => useOrganization(), { wrapper });

    await waitFor(() => {
      expect(result.current.organization).toEqual(mockOrg);
    });

    await act(async () => {
      await result.current.revokeInvitation('inv-1');
    });

    expect(apiService.deleteOrgInvitation).toHaveBeenCalledWith('inv-1');
    expect(apiService.listOrgInvitations).toHaveBeenCalled();
    expect(result.current.invitations).toEqual([]);
  });

  it('clears state when isAuthenticated becomes false', async () => {
    mockUseAuth.mockReturnValue({ isAuthenticated: true });
    (apiService.getCurrentOrg as jest.Mock).mockResolvedValue({ data: { organization: mockOrg } });

    const { result, rerender } = renderHook(() => useOrganization(), { wrapper });

    await waitFor(() => {
      expect(result.current.organization).toEqual(mockOrg);
    });

    // Simulate logout
    mockUseAuth.mockReturnValue({ isAuthenticated: false });
    mockUseRBAC.mockReturnValue({ isSuperAdmin: false });
    rerender();

    await waitFor(() => {
      expect(result.current.organization).toBeNull();
      expect(result.current.invitations).toEqual([]);
    });
  });
});
