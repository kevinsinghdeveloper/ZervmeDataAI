import React from 'react';
import { Box, Container, Grid, Typography, Link, IconButton, Stack } from '@mui/material';
import LinkedInIcon from '@mui/icons-material/LinkedIn';
import TwitterIcon from '@mui/icons-material/Twitter';

const footerSections = [
  {
    title: 'Company',
    links: ['About', 'Careers', 'Contact'],
  },
  {
    title: 'Product',
    links: ['Features', 'Security', 'How It Works'],
  },
  {
    title: 'Legal',
    links: ['Privacy Policy', 'Terms of Service', 'Cookie Policy'],
  },
];

const AppFooter: React.FC = () => {
  const currentYear = new Date().getFullYear();

  return (
    <Box component="footer" sx={{ mt: 'auto' }}>
      {/* Gradient top border */}
      <Box
        sx={{
          height: 2,
          background: 'linear-gradient(90deg, #7b6df6 0%, #10b981 100%)',
        }}
      />

      {/* Main footer content */}
      <Box
        sx={{
          bgcolor: 'rgba(10, 22, 40, 0.6)',
          backdropFilter: 'blur(10px)',
          pt: 6,
          pb: 3,
        }}
      >
        <Container maxWidth="lg">
          <Grid container spacing={4}>
            {/* Brand column */}
            <Grid item xs={12} md={3}>
              <Typography
                variant="h6"
                sx={{
                  fontWeight: 700,
                  background: 'linear-gradient(135deg, #7b6df6, #10b981)',
                  WebkitBackgroundClip: 'text',
                  WebkitTextFillColor: 'transparent',
                  mb: 1.5,
                }}
              >
                Zerve Direct
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ lineHeight: 1.7 }}>
                Connecting businesses with lenders to accelerate growth. Streamlined onboarding,
                document management, and compliance — all in one platform.
              </Typography>
            </Grid>

            {/* Link columns */}
            {footerSections.map((section) => (
              <Grid item xs={6} sm={4} md={2} key={section.title}>
                <Typography
                  variant="subtitle2"
                  color="text.primary"
                  sx={{ fontWeight: 600, mb: 2, letterSpacing: '0.04em', textTransform: 'uppercase', fontSize: '0.75rem' }}
                >
                  {section.title}
                </Typography>
                <Stack spacing={1.2}>
                  {section.links.map((link) => (
                    <Link
                      key={link}
                      href="#"
                      underline="none"
                      sx={{
                        color: 'text.secondary',
                        fontSize: '0.875rem',
                        transition: 'color 0.2s ease',
                        '&:hover': {
                          color: 'primary.main',
                        },
                      }}
                    >
                      {link}
                    </Link>
                  ))}
                </Stack>
              </Grid>
            ))}

            {/* Contact column */}
            <Grid item xs={12} sm={6} md={3}>
              <Typography
                variant="subtitle2"
                color="text.primary"
                sx={{ fontWeight: 600, mb: 2, letterSpacing: '0.04em', textTransform: 'uppercase', fontSize: '0.75rem' }}
              >
                Contact
              </Typography>
              <Stack spacing={1.2}>
                <Link
                  href="mailto:support@zervedirect.com"
                  underline="none"
                  sx={{
                    color: 'text.secondary',
                    fontSize: '0.875rem',
                    transition: 'color 0.2s ease',
                    '&:hover': { color: 'primary.main' },
                  }}
                >
                  support@zervedirect.com
                </Link>
                <Typography variant="body2" color="text.secondary">
                  +1 (555) 000-0000
                </Typography>
              </Stack>
            </Grid>
          </Grid>

          {/* Bottom bar */}
          <Box
            sx={{
              mt: 5,
              pt: 3,
              borderTop: '1px solid',
              borderColor: 'divider',
              display: 'flex',
              flexDirection: { xs: 'column', sm: 'row' },
              alignItems: 'center',
              justifyContent: 'space-between',
              gap: 2,
            }}
          >
            <Typography variant="body2" color="text.secondary">
              &copy; {currentYear} Zerve Direct. All rights reserved.
            </Typography>

            <Stack direction="row" spacing={0.5}>
              <IconButton
                href="#"
                size="small"
                aria-label="LinkedIn"
                sx={{
                  color: 'text.secondary',
                  '&:hover': { color: 'primary.main', bgcolor: 'rgba(123, 109, 246, 0.08)' },
                }}
              >
                <LinkedInIcon fontSize="small" />
              </IconButton>
              <IconButton
                href="#"
                size="small"
                aria-label="Twitter"
                sx={{
                  color: 'text.secondary',
                  '&:hover': { color: 'primary.main', bgcolor: 'rgba(123, 109, 246, 0.08)' },
                }}
              >
                <TwitterIcon fontSize="small" />
              </IconButton>
            </Stack>
          </Box>
        </Container>
      </Box>
    </Box>
  );
};

export default AppFooter;
