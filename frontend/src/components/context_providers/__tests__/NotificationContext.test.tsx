import React from 'react';
import { renderHook, act } from '@testing-library/react';
import { render, screen } from '@testing-library/react';
import { NotificationProvider, useNotification } from '../NotificationContext';

const wrapper = ({ children }: { children: React.ReactNode }) => (
  <NotificationProvider>{children}</NotificationProvider>
);

// Helper component that triggers notification methods
const NotificationTrigger: React.FC<{
  method: 'showSuccess' | 'showError' | 'showWarning' | 'showInfo';
  message: string;
}> = ({ method, message }) => {
  const notification = useNotification();
  return (
    <button onClick={() => notification[method](message)} data-testid="trigger">
      Trigger
    </button>
  );
};

beforeEach(() => {
  jest.clearAllMocks();
});

describe('NotificationContext', () => {
  describe('useNotification hook', () => {
    it('throws when used outside of NotificationProvider', () => {
      const consoleSpy = jest.spyOn(console, 'error').mockImplementation(() => {});
      expect(() => {
        renderHook(() => useNotification());
      }).toThrow('useNotification must be used within NotificationProvider');
      consoleSpy.mockRestore();
    });
  });

  describe('provides all notification methods', () => {
    it('exposes showSuccess, showError, showWarning, and showInfo', () => {
      const { result } = renderHook(() => useNotification(), { wrapper });

      expect(typeof result.current.showSuccess).toBe('function');
      expect(typeof result.current.showError).toBe('function');
      expect(typeof result.current.showWarning).toBe('function');
      expect(typeof result.current.showInfo).toBe('function');
    });
  });

  describe('showSuccess', () => {
    it('renders a success alert with the given message', () => {
      render(
        <NotificationProvider>
          <NotificationTrigger method="showSuccess" message="Operation completed" />
        </NotificationProvider>
      );

      act(() => {
        screen.getByTestId('trigger').click();
      });

      const alert = screen.getByRole('alert');
      expect(alert).toHaveTextContent('Operation completed');
      expect(alert).toHaveClass('MuiAlert-filledSuccess');
    });
  });

  describe('showError', () => {
    it('renders an error alert with the given message', () => {
      render(
        <NotificationProvider>
          <NotificationTrigger method="showError" message="Something went wrong" />
        </NotificationProvider>
      );

      act(() => {
        screen.getByTestId('trigger').click();
      });

      const alert = screen.getByRole('alert');
      expect(alert).toHaveTextContent('Something went wrong');
      expect(alert).toHaveClass('MuiAlert-filledError');
    });
  });

  describe('showWarning', () => {
    it('renders a warning alert with the given message', () => {
      render(
        <NotificationProvider>
          <NotificationTrigger method="showWarning" message="Proceed with caution" />
        </NotificationProvider>
      );

      act(() => {
        screen.getByTestId('trigger').click();
      });

      const alert = screen.getByRole('alert');
      expect(alert).toHaveTextContent('Proceed with caution');
      expect(alert).toHaveClass('MuiAlert-filledWarning');
    });
  });

  describe('showInfo', () => {
    it('renders an info alert with the given message', () => {
      render(
        <NotificationProvider>
          <NotificationTrigger method="showInfo" message="Here is some info" />
        </NotificationProvider>
      );

      act(() => {
        screen.getByTestId('trigger').click();
      });

      const alert = screen.getByRole('alert');
      expect(alert).toHaveTextContent('Here is some info');
      expect(alert).toHaveClass('MuiAlert-filledInfo');
    });
  });

  describe('replaces previous notification', () => {
    it('shows the latest message when multiple notifications are triggered', () => {
      const MultiTrigger: React.FC = () => {
        const notification = useNotification();
        return (
          <>
            <button onClick={() => notification.showSuccess('First')} data-testid="first">
              First
            </button>
            <button onClick={() => notification.showError('Second')} data-testid="second">
              Second
            </button>
          </>
        );
      };

      render(
        <NotificationProvider>
          <MultiTrigger />
        </NotificationProvider>
      );

      act(() => {
        screen.getByTestId('first').click();
      });

      act(() => {
        screen.getByTestId('second').click();
      });

      const alert = screen.getByRole('alert');
      expect(alert).toHaveTextContent('Second');
      expect(alert).toHaveClass('MuiAlert-filledError');
    });
  });
});
