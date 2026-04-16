/* eslint-disable import/first, testing-library/no-wait-for-multiple-assertions */
import React from 'react';
import { renderHook, act, waitFor } from '@testing-library/react';

// ---------------------------------------------------------------------------
// Mocks -- must come before importing the module under test
// ---------------------------------------------------------------------------
const mockUseAuth = jest.fn();

jest.mock('../AuthContext', () => ({
  useAuth: () => mockUseAuth(),
  AuthContextProvider: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}));

jest.mock('../../../utils/api.service', () => ({
  __esModule: true,
  default: {
    getCurrentUser: jest.fn(),
    updateUser: jest.fn(),
    updatePreferences: jest.fn(),
  },
}));

// ---------------------------------------------------------------------------
// Imports after mocks
// ---------------------------------------------------------------------------
import { UserContextProvider, useUser } from '../UserContext';
import apiService from '../../../utils/api.service';

// ---------------------------------------------------------------------------
// Fixtures
// ---------------------------------------------------------------------------
const mockUser = {
  id: 'user-1',
  email: 'test@example.com',
  firstName: 'Test',
  lastName: 'User',
  orgId: 'org-1',
  orgRole: 'member' as const,
  isSuperAdmin: false,
  role: 'member' as const,
  isActive: true,
  isVerified: true,
  status: 'active' as const,
  timezone: 'America/New_York',
  createdAt: '2025-01-01T00:00:00Z',
  updatedAt: '2025-01-01T00:00:00Z',
};

const wrapper = ({ children }: { children: React.ReactNode }) => (
  <UserContextProvider>{children}</UserContextProvider>
);

// ---------------------------------------------------------------------------
// Setup
// ---------------------------------------------------------------------------
beforeEach(() => {
  jest.clearAllMocks();
  mockUseAuth.mockReturnValue({ isAuthenticated: false });
});

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------
describe('UserContext', () => {
  it('throws when useUser is called outside UserContextProvider', () => {
    // Suppress expected console.error from React about uncaught errors
    const spy = jest.spyOn(console, 'error').mockImplementation(() => {});
    expect(() => renderHook(() => useUser())).toThrow(
      'useUser must be used within UserContextProvider',
    );
    spy.mockRestore();
  });

  it('has correct initial state when not authenticated', () => {
    const { result } = renderHook(() => useUser(), { wrapper });

    expect(result.current.user).toBeNull();
    expect(result.current.isLoading).toBe(false);
    expect(result.current.error).toBeNull();
  });

  it('fetches the current user when isAuthenticated becomes true', async () => {
    mockUseAuth.mockReturnValue({ isAuthenticated: true });
    (apiService.getCurrentUser as jest.Mock).mockResolvedValue({ data: mockUser });

    const { result } = renderHook(() => useUser(), { wrapper });

    await waitFor(() => {
      expect(result.current.user).toEqual(mockUser);
    });
    expect(apiService.getCurrentUser).toHaveBeenCalledTimes(1);
  });

  it('clears user when isAuthenticated becomes false', async () => {
    // Start authenticated
    mockUseAuth.mockReturnValue({ isAuthenticated: true });
    (apiService.getCurrentUser as jest.Mock).mockResolvedValue({ data: mockUser });

    const { result, rerender } = renderHook(() => useUser(), { wrapper });

    await waitFor(() => {
      expect(result.current.user).toEqual(mockUser);
    });

    // Simulate logout
    mockUseAuth.mockReturnValue({ isAuthenticated: false });
    rerender();

    await waitFor(() => {
      expect(result.current.user).toBeNull();
    });
  });

  it('sets error when fetchCurrentUser fails', async () => {
    mockUseAuth.mockReturnValue({ isAuthenticated: true });
    (apiService.getCurrentUser as jest.Mock).mockRejectedValue(new Error('Network error'));

    const { result } = renderHook(() => useUser(), { wrapper });

    await waitFor(() => {
      expect(result.current.error).toBe('Network error');
    });
    expect(result.current.user).toBeNull();
    expect(result.current.isLoading).toBe(false);
  });

  it('handles response without nested data property', async () => {
    mockUseAuth.mockReturnValue({ isAuthenticated: true });
    // Some API responses come unwrapped (response.data is the user directly)
    (apiService.getCurrentUser as jest.Mock).mockResolvedValue(mockUser);

    const { result } = renderHook(() => useUser(), { wrapper });

    await waitFor(() => {
      expect(result.current.user).toEqual(mockUser);
    });
  });

  it('updates user via updateUser', async () => {
    mockUseAuth.mockReturnValue({ isAuthenticated: true });
    (apiService.getCurrentUser as jest.Mock).mockResolvedValue({ data: mockUser });

    const { result } = renderHook(() => useUser(), { wrapper });

    await waitFor(() => {
      expect(result.current.user).toEqual(mockUser);
    });

    const updatedUser = { ...mockUser, firstName: 'Updated' };
    (apiService.updateUser as jest.Mock).mockResolvedValue({ data: updatedUser });

    await act(async () => {
      await result.current.updateUser({ firstName: 'Updated' });
    });

    expect(apiService.updateUser).toHaveBeenCalledWith('user-1', { firstName: 'Updated' });
    expect(result.current.user).toEqual(updatedUser);
  });

  it('throws when updateUser is called with no current user', async () => {
    mockUseAuth.mockReturnValue({ isAuthenticated: false });

    const { result } = renderHook(() => useUser(), { wrapper });

    await expect(
      act(async () => {
        await result.current.updateUser({ firstName: 'Nope' });
      }),
    ).rejects.toThrow('No authenticated user');
  });

  it('sets user directly via setUser', async () => {
    mockUseAuth.mockReturnValue({ isAuthenticated: false });

    const { result } = renderHook(() => useUser(), { wrapper });

    expect(result.current.user).toBeNull();

    act(() => {
      result.current.setUser(mockUser);
    });

    expect(result.current.user).toEqual(mockUser);
  });

  it('updatePreferences calls API and refetches the user', async () => {
    mockUseAuth.mockReturnValue({ isAuthenticated: true });
    (apiService.getCurrentUser as jest.Mock).mockResolvedValue({ data: mockUser });

    const { result } = renderHook(() => useUser(), { wrapper });

    await waitFor(() => {
      expect(result.current.user).toEqual(mockUser);
    });

    const prefs = { timezone: 'UTC' };
    (apiService.updatePreferences as jest.Mock).mockResolvedValue({ success: true });
    const refetchedUser = { ...mockUser, timezone: 'UTC' };
    (apiService.getCurrentUser as jest.Mock).mockResolvedValue({ data: refetchedUser });

    await act(async () => {
      await result.current.updatePreferences(prefs);
    });

    expect(apiService.updatePreferences).toHaveBeenCalledWith(prefs);
    // fetchCurrentUser should have been called again after preferences update
    expect(apiService.getCurrentUser).toHaveBeenCalledTimes(2);
    expect(result.current.user).toEqual(refetchedUser);
  });

  it('resets isLoading after successful fetch', async () => {
    mockUseAuth.mockReturnValue({ isAuthenticated: true });
    (apiService.getCurrentUser as jest.Mock).mockResolvedValue({ data: mockUser });

    const { result } = renderHook(() => useUser(), { wrapper });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
      expect(result.current.user).toEqual(mockUser);
    });
  });
});
