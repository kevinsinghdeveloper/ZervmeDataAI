import { createTheme, Theme } from '@mui/material/styles';

export const DEFAULT_BG = '#0a1628';
export const DEFAULT_PAPER = '#1a2332';

export function createAppTheme(
  primary = '#7b6df6',
  secondary = '#10b981',
  background = DEFAULT_BG,
  paper = DEFAULT_PAPER,
): Theme {
  return createTheme({
    palette: {
      mode: 'dark',
      primary: {
        main: primary,
        contrastText: '#ffffff',
      },
      secondary: {
        main: secondary,
        contrastText: '#ffffff',
      },
      error: { main: '#ef4444', light: '#f87171', dark: '#dc2626' },
      warning: { main: '#f59e0b', light: '#fbbf24', dark: '#d97706' },
      info: { main: '#3b82f6', light: '#60a5fa', dark: '#2563eb' },
      success: { main: '#10b981', light: '#34d399', dark: '#059669' },
      background: { default: background, paper },
      text: { primary: '#f1f5f9', secondary: '#94a3b8', disabled: '#64748b' },
      divider: 'rgba(148, 163, 184, 0.12)',
    },
    typography: {
      fontFamily: '"Inter", "Roboto", "Helvetica", "Arial", sans-serif',
      h1: { fontSize: '2.5rem', fontWeight: 700, lineHeight: 1.2, letterSpacing: '-0.02em' },
      h2: { fontSize: '2rem', fontWeight: 700, lineHeight: 1.3, letterSpacing: '-0.01em' },
      h3: { fontSize: '1.75rem', fontWeight: 600, lineHeight: 1.4 },
      h4: { fontSize: '1.5rem', fontWeight: 600, lineHeight: 1.4 },
      h5: { fontSize: '1.25rem', fontWeight: 600, lineHeight: 1.5 },
      h6: { fontSize: '1rem', fontWeight: 600, lineHeight: 1.5 },
      button: { textTransform: 'none', fontWeight: 600 },
    },
    shape: { borderRadius: 12 },
    components: {
      MuiButton: {
        styleOverrides: {
          root: {
            borderRadius: 10,
            padding: '10px 22px',
            fontSize: '0.95rem',
            transition: 'all 0.2s ease',
          },
          contained: {
            boxShadow: 'none',
            '&:hover': {
              boxShadow: '0 4px 12px rgba(123, 109, 246, 0.3)',
              transform: 'translateY(-1px)',
            },
          },
          outlined: {
            borderColor: 'rgba(148, 163, 184, 0.2)',
            '&:hover': {
              borderColor: primary,
              backgroundColor: 'rgba(123, 109, 246, 0.08)',
            },
          },
        },
      },
      MuiCard: {
        styleOverrides: {
          root: {
            borderRadius: 16,
            border: '1px solid rgba(148, 163, 184, 0.1)',
            backdropFilter: 'blur(10px)',
            backgroundImage: 'none',
            boxShadow: '0 4px 24px rgba(0, 0, 0, 0.12)',
            transition: 'all 0.3s ease',
          },
        },
      },
      MuiPaper: {
        styleOverrides: {
          root: { backgroundImage: 'none' },
          rounded: { borderRadius: 16 },
        },
      },
      MuiTextField: {
        styleOverrides: {
          root: {
            '& .MuiOutlinedInput-root': {
              borderRadius: 10,
              '& fieldset': { borderColor: 'rgba(148, 163, 184, 0.15)' },
              '&:hover fieldset': { borderColor: 'rgba(123, 109, 246, 0.4)' },
            },
          },
        },
      },
      MuiTableCell: {
        styleOverrides: {
          head: { fontWeight: 600, backgroundColor: paper, borderBottom: '1px solid rgba(148, 163, 184, 0.1)' },
          root: { borderBottom: '1px solid rgba(148, 163, 184, 0.06)' },
        },
      },
      MuiChip: {
        styleOverrides: {
          root: { borderRadius: 8, fontWeight: 500 },
        },
      },
      MuiTab: {
        styleOverrides: {
          root: {
            textTransform: 'none',
            fontWeight: 500,
            '&.Mui-selected': { fontWeight: 600 },
          },
        },
      },
      MuiDialog: {
        styleOverrides: {
          paper: { borderRadius: 16, border: '1px solid rgba(148, 163, 184, 0.1)' },
        },
      },
      MuiAlert: {
        styleOverrides: {
          root: { borderRadius: 12 },
        },
      },
    },
  });
}

// Default static theme for initial render
const theme = createAppTheme();
export default theme;
