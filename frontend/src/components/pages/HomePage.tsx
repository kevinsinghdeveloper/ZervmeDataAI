import React from 'react';
import { Box, Typography, Button, Container, Grid, alpha, useTheme } from '@mui/material';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context_providers/AuthContext';
import {
  SmartToy, Storage, BarChart, Groups, Security,
  AutoAwesome, CheckCircle, Speed, TrendingUp,
  FormatQuote, ArrowForward, Explore,
} from '@mui/icons-material';

/* ───────────────────────── data ───────────────────────── */

const FEATURES = [
  {
    icon: <SmartToy />,
    title: 'AI-powered conversations',
    desc: 'Chat with your data using natural language. Get insights, charts, and answers instantly.',
  },
  {
    icon: <Storage />,
    title: 'ETL pipelines',
    desc: 'Connect, transform, and load data from any source. Build pipelines that run reliably at scale.',
  },
  {
    icon: <BarChart />,
    title: 'Real-time analytics',
    desc: 'Instant visibility into your data. Build dashboards, run queries, and explore trends.',
  },
  {
    icon: <Groups />,
    title: 'Team collaboration',
    desc: 'Invite your team, assign roles, and share projects. Everyone stays aligned.',
  },
  {
    icon: <Security />,
    title: 'Enterprise security',
    desc: 'SOC 2 compliant with encryption at rest and in transit. Role-based access controls.',
  },
  {
    icon: <AutoAwesome />,
    title: 'Smart automation',
    desc: 'Let AI handle the repetitive work. Auto-categorize, schedule, and optimize your workflows.',
  },
];

const METRICS = [
  { value: '10x', label: 'Faster than manual analysis' },
  { value: '99.9%', label: 'Uptime SLA' },
  { value: '< 2min', label: 'Average setup time' },
  { value: '0', label: 'Credit card required' },
];

const STEPS = [
  { num: '01', title: 'Create your workspace', desc: 'Sign up free and name your organization. Takes under a minute.' },
  { num: '02', title: 'Connect your data', desc: 'Import from databases, APIs, or files. We handle the rest.' },
  { num: '03', title: 'Start exploring', desc: 'Ask questions in plain English and get instant insights from your data.' },
];

const TESTIMONIALS = [
  {
    quote: 'We replaced our entire BI stack with Zerve Data AI. The AI assistant understands our data better than our old dashboards ever could.',
    name: 'Sarah Chen',
    role: 'VP of Engineering',
    company: 'Meridian Digital',
  },
  {
    quote: 'Setting up ETL pipelines used to take weeks. With Zerve, we had production-ready pipelines running in hours.',
    name: 'Marcus Rivera',
    role: 'Data Engineering Lead',
    company: 'Apex Studios',
  },
  {
    quote: 'The natural language interface means our non-technical team members can finally explore data on their own. Huge productivity boost.',
    name: 'Priya Sharma',
    role: 'Founder & CEO',
    company: 'Lightbridge Consulting',
  },
];

const CAPABILITIES = [
  'Natural language queries',
  'Automated ETL pipelines',
  'Real-time dashboards',
  'CSV & PDF exports',
  'Role-based permissions',
  'Multi-source connectors',
  'Team collaboration',
  'AI-powered insights',
];

/* ───────────────────────── component ───────────────────────── */

const HomePage: React.FC = () => {
  const navigate = useNavigate();
  const theme = useTheme();
  const { isAuthenticated } = useAuth();

  const primary = theme.palette.primary.main;
  const secondary = theme.palette.secondary.main;
  const dark = '#0a1628';

  return (
    <Box sx={{ bgcolor: dark, minHeight: '100vh', overflowX: 'hidden' }}>

      {/* HERO */}
      <Box
        sx={{
          position: 'relative',
          pt: { xs: 10, md: 16 },
          pb: { xs: 10, md: 14 },
          px: 3,
          overflow: 'hidden',
        }}
      >
        {/* Gradient orbs */}
        <Box sx={{
          position: 'absolute', top: '-20%', left: '-10%',
          width: 600, height: 600, borderRadius: '50%',
          background: `radial-gradient(circle, ${alpha(primary, 0.15)} 0%, transparent 70%)`,
          filter: 'blur(80px)', pointerEvents: 'none',
        }} />
        <Box sx={{
          position: 'absolute', bottom: '-30%', right: '-10%',
          width: 500, height: 500, borderRadius: '50%',
          background: `radial-gradient(circle, ${alpha(secondary, 0.12)} 0%, transparent 70%)`,
          filter: 'blur(80px)', pointerEvents: 'none',
        }} />

        <Container maxWidth="lg" sx={{ position: 'relative', zIndex: 1 }}>
          <Grid container spacing={6} alignItems="center">
            <Grid item xs={12} md={7}>
              <Box
                sx={{
                  display: 'inline-flex', alignItems: 'center', gap: 1,
                  bgcolor: alpha(primary, 0.1), border: `1px solid ${alpha(primary, 0.2)}`,
                  borderRadius: 5, px: 2, py: 0.5, mb: 3,
                }}
              >
                <Speed sx={{ fontSize: 16, color: secondary }} />
                <Typography variant="caption" sx={{ color: secondary, fontWeight: 600, letterSpacing: 0.5 }}>
                  AI-powered data intelligence
                </Typography>
              </Box>

              <Typography
                variant="h1"
                sx={{
                  fontWeight: 800,
                  fontSize: { xs: '2.4rem', sm: '3.2rem', md: '3.8rem', lg: '4.2rem' },
                  lineHeight: 1.1,
                  color: '#fff',
                  mb: 3,
                }}
              >
                Understand your{' '}
                <Box
                  component="span"
                  sx={{
                    background: `linear-gradient(135deg, ${primary}, ${secondary})`,
                    WebkitBackgroundClip: 'text',
                    WebkitTextFillColor: 'transparent',
                  }}
                >
                  data
                </Box>
                <br />
                like never before.
              </Typography>

              <Typography
                variant="h6"
                sx={{
                  color: 'rgba(255,255,255,0.6)',
                  fontWeight: 400,
                  lineHeight: 1.7,
                  maxWidth: 520,
                  mb: 4,
                  fontSize: { xs: '1rem', md: '1.15rem' },
                }}
              >
                Zerve Data AI helps teams connect data sources, build ETL pipelines, and
                explore insights using AI — all in one platform. Start free.
              </Typography>

              <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap', mb: 2 }}>
                <Button
                  variant="contained"
                  size="large"
                  endIcon={<ArrowForward />}
                  onClick={() => navigate(isAuthenticated ? '/projects' : '/register')}
                  sx={{
                    background: `linear-gradient(135deg, ${primary}, ${alpha(primary, 0.85)})`,
                    fontWeight: 700,
                    px: 4, py: 1.5,
                    borderRadius: 2,
                    fontSize: '1rem',
                    textTransform: 'none',
                    boxShadow: `0 8px 32px ${alpha(primary, 0.35)}`,
                    '&:hover': {
                      transform: 'translateY(-2px)',
                      boxShadow: `0 12px 40px ${alpha(primary, 0.45)}`,
                    },
                    transition: 'all 0.25s ease',
                  }}
                >
                  {isAuthenticated ? 'Go to App' : 'Start for Free'}
                </Button>
                <Button
                  variant="outlined"
                  size="large"
                  startIcon={<Explore />}
                  onClick={() => navigate(isAuthenticated ? '/projects' : '/register')}
                  sx={{
                    borderColor: 'rgba(255,255,255,0.2)',
                    color: 'rgba(255,255,255,0.85)',
                    fontWeight: 600,
                    px: 4, py: 1.5,
                    borderRadius: 2,
                    fontSize: '1rem',
                    textTransform: 'none',
                    '&:hover': {
                      borderColor: 'rgba(255,255,255,0.4)',
                      bgcolor: 'rgba(255,255,255,0.05)',
                      transform: 'translateY(-2px)',
                    },
                    transition: 'all 0.25s ease',
                  }}
                >
                  Explore Features
                </Button>
              </Box>
              <Typography variant="body2" sx={{ color: 'rgba(255,255,255,0.35)' }}>
                Free forever for individuals. No credit card needed.
              </Typography>
            </Grid>

            {/* Hero visual -- stylized app preview */}
            <Grid item xs={12} md={5}>
              <Box
                sx={{
                  position: 'relative',
                  borderRadius: 4,
                  overflow: 'hidden',
                  border: `1px solid ${alpha(primary, 0.2)}`,
                  bgcolor: alpha(primary, 0.04),
                  p: 3,
                  backdropFilter: 'blur(20px)',
                }}
              >
                {/* Mock AI chat card */}
                <Box sx={{
                  bgcolor: alpha(primary, 0.08),
                  borderRadius: 3, p: 2.5, mb: 2,
                  border: `1px solid ${alpha(primary, 0.15)}`,
                }}>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1.5 }}>
                    <Typography variant="overline" sx={{ color: 'rgba(255,255,255,0.5)', letterSpacing: 1 }}>
                      AI Assistant
                    </Typography>
                    <Box sx={{
                      width: 8, height: 8, borderRadius: '50%', bgcolor: secondary,
                      boxShadow: `0 0 8px ${secondary}`,
                      animation: 'pulse 2s ease-in-out infinite',
                    }} />
                  </Box>
                  <Typography variant="body2" sx={{ color: 'rgba(255,255,255,0.6)', mb: 1, fontStyle: 'italic' }}>
                    "Show me revenue trends by region for Q4..."
                  </Typography>
                  <Typography variant="body2" sx={{ color: primary }}>
                    Generating analysis with 3 visualizations...
                  </Typography>
                </Box>

                {/* Mock data pipeline items */}
                {[
                  { name: 'PostgreSQL Sync', status: 'Running', records: '12.4K rows', color: secondary },
                  { name: 'S3 Data Lake', status: 'Complete', records: '847K rows', color: primary },
                  { name: 'API Connector', status: 'Scheduled', records: '2.1K rows', color: '#f59e0b' },
                ].map((item, i) => (
                  <Box
                    key={i}
                    sx={{
                      display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                      py: 1.5, px: 2, borderRadius: 2, mb: 1,
                      bgcolor: 'rgba(255,255,255,0.02)',
                      border: '1px solid rgba(255,255,255,0.05)',
                      transition: 'all 0.2s',
                      '&:hover': { bgcolor: 'rgba(255,255,255,0.04)' },
                    }}
                  >
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
                      <Box sx={{ width: 3, height: 28, borderRadius: 1, bgcolor: item.color }} />
                      <Box>
                        <Typography variant="body2" sx={{ color: '#fff', fontWeight: 500 }}>{item.name}</Typography>
                        <Typography variant="caption" sx={{ color: 'rgba(255,255,255,0.4)' }}>{item.status}</Typography>
                      </Box>
                    </Box>
                    <Typography variant="body2" sx={{ color: 'rgba(255,255,255,0.6)', fontFamily: 'monospace' }}>
                      {item.records}
                    </Typography>
                  </Box>
                ))}
              </Box>
            </Grid>
          </Grid>
        </Container>
      </Box>

      {/* METRICS BAR */}
      <Box sx={{
        borderTop: `1px solid ${alpha(primary, 0.1)}`,
        borderBottom: `1px solid ${alpha(primary, 0.1)}`,
        py: { xs: 4, md: 5 }, px: 3,
        bgcolor: alpha(primary, 0.02),
      }}>
        <Container maxWidth="lg">
          <Grid container spacing={4} justifyContent="center">
            {METRICS.map((m, i) => (
              <Grid item xs={6} sm={3} key={i} sx={{ textAlign: 'center' }}>
                <Typography
                  variant="h3"
                  sx={{
                    fontWeight: 800,
                    fontSize: { xs: '1.6rem', md: '2.2rem' },
                    background: `linear-gradient(135deg, ${primary}, ${secondary})`,
                    WebkitBackgroundClip: 'text',
                    WebkitTextFillColor: 'transparent',
                    mb: 0.5,
                  }}
                >
                  {m.value}
                </Typography>
                <Typography variant="body2" sx={{ color: 'rgba(255,255,255,0.5)', fontWeight: 500 }}>
                  {m.label}
                </Typography>
              </Grid>
            ))}
          </Grid>
        </Container>
      </Box>

      {/* FEATURES -- BENTO GRID */}
      <Box sx={{ py: { xs: 8, md: 14 }, px: 3 }}>
        <Container maxWidth="lg">
          <Box sx={{ textAlign: 'center', mb: { xs: 6, md: 8 } }}>
            <Typography
              variant="h3"
              sx={{ color: '#fff', fontWeight: 700, mb: 2, fontSize: { xs: '1.8rem', md: '2.5rem' } }}
            >
              Everything you need to{' '}
              <Box component="span" sx={{
                background: `linear-gradient(135deg, ${primary}, ${secondary})`,
                WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent',
              }}>
                unlock your data
              </Box>
            </Typography>
            <Typography variant="body1" sx={{ color: 'rgba(255,255,255,0.5)', maxWidth: 560, mx: 'auto' }}>
              From ETL pipelines to AI-powered analytics, Zerve Data AI gives your team the
              tools to turn raw data into actionable insights.
            </Typography>
          </Box>

          <Grid container spacing={3}>
            {FEATURES.map((feat, i) => {
              const isLarge = i < 2;
              return (
                <Grid item xs={12} sm={6} md={isLarge ? 6 : 4} key={i}>
                  <Box
                    sx={{
                      p: { xs: 3, md: 4 },
                      height: '100%',
                      borderRadius: 4,
                      border: `1px solid ${alpha(primary, 0.1)}`,
                      bgcolor: alpha(primary, 0.03),
                      transition: 'all 0.3s ease',
                      '&:hover': {
                        borderColor: alpha(primary, 0.3),
                        bgcolor: alpha(primary, 0.06),
                        transform: 'translateY(-4px)',
                        boxShadow: `0 16px 48px ${alpha(primary, 0.1)}`,
                      },
                    }}
                  >
                    <Box
                      sx={{
                        width: 52, height: 52,
                        borderRadius: 3,
                        display: 'flex', alignItems: 'center', justifyContent: 'center',
                        background: `linear-gradient(135deg, ${alpha(primary, 0.15)}, ${alpha(secondary, 0.15)})`,
                        border: `1px solid ${alpha(primary, 0.2)}`,
                        color: primary,
                        mb: 2.5,
                        '& .MuiSvgIcon-root': { fontSize: 26 },
                      }}
                    >
                      {feat.icon}
                    </Box>
                    <Typography variant="h6" sx={{ color: '#fff', fontWeight: 600, mb: 1 }}>
                      {feat.title}
                    </Typography>
                    <Typography variant="body2" sx={{ color: 'rgba(255,255,255,0.55)', lineHeight: 1.7 }}>
                      {feat.desc}
                    </Typography>
                  </Box>
                </Grid>
              );
            })}
          </Grid>
        </Container>
      </Box>

      {/* HOW IT WORKS */}
      <Box sx={{ py: { xs: 8, md: 14 }, px: 3, bgcolor: alpha(primary, 0.02) }}>
        <Container maxWidth="md">
          <Box sx={{ textAlign: 'center', mb: { xs: 6, md: 8 } }}>
            <Typography
              variant="h3"
              sx={{ color: '#fff', fontWeight: 700, mb: 2, fontSize: { xs: '1.8rem', md: '2.5rem' } }}
            >
              Up and running in minutes
            </Typography>
            <Typography variant="body1" sx={{ color: 'rgba(255,255,255,0.5)', maxWidth: 480, mx: 'auto' }}>
              No training required. No complex setup. Three steps and your team is exploring data.
            </Typography>
          </Box>

          <Grid container spacing={4}>
            {STEPS.map((step, i) => (
              <Grid item xs={12} md={4} key={i}>
                <Box sx={{ textAlign: 'center', position: 'relative' }}>
                  {i < STEPS.length - 1 && (
                    <Box sx={{
                      display: { xs: 'none', md: 'block' },
                      position: 'absolute', top: 36, left: '62%', width: '76%', height: 2,
                      background: `linear-gradient(90deg, ${alpha(primary, 0.4)}, ${alpha(secondary, 0.4)})`,
                      zIndex: 0,
                    }} />
                  )}
                  <Box sx={{
                    width: 72, height: 72, borderRadius: '50%', mx: 'auto', mb: 3,
                    background: `linear-gradient(135deg, ${primary}, ${secondary})`,
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    position: 'relative', zIndex: 1,
                    boxShadow: `0 8px 32px ${alpha(primary, 0.3)}`,
                  }}>
                    <Typography variant="h5" sx={{ color: '#fff', fontWeight: 800 }}>{step.num}</Typography>
                  </Box>
                  <Typography variant="h6" sx={{ color: '#fff', fontWeight: 600, mb: 1 }}>{step.title}</Typography>
                  <Typography variant="body2" sx={{ color: 'rgba(255,255,255,0.5)', lineHeight: 1.7 }}>
                    {step.desc}
                  </Typography>
                </Box>
              </Grid>
            ))}
          </Grid>
        </Container>
      </Box>

      {/* CAPABILITIES STRIP */}
      <Box sx={{ py: { xs: 6, md: 10 }, px: 3 }}>
        <Container maxWidth="lg">
          <Grid container spacing={6} alignItems="center">
            <Grid item xs={12} md={5}>
              <Typography
                variant="h3"
                sx={{ color: '#fff', fontWeight: 700, mb: 2, fontSize: { xs: '1.8rem', md: '2.2rem' } }}
              >
                Built for teams that{' '}
                <Box component="span" sx={{
                  background: `linear-gradient(135deg, ${primary}, ${secondary})`,
                  WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent',
                }}>
                  move fast
                </Box>
              </Typography>
              <Typography variant="body1" sx={{ color: 'rgba(255,255,255,0.5)', lineHeight: 1.7, mb: 3 }}>
                Whether you're a startup or an enterprise, Zerve Data AI scales with your
                data needs. Here's what every workspace includes.
              </Typography>
              <Button
                variant="contained"
                endIcon={<ArrowForward />}
                onClick={() => navigate(isAuthenticated ? '/projects' : '/register')}
                sx={{
                  background: `linear-gradient(135deg, ${primary}, ${alpha(primary, 0.85)})`,
                  fontWeight: 700, px: 4, py: 1.5, borderRadius: 2,
                  textTransform: 'none', fontSize: '0.95rem',
                  boxShadow: `0 8px 32px ${alpha(primary, 0.3)}`,
                  '&:hover': { transform: 'translateY(-2px)', boxShadow: `0 12px 40px ${alpha(primary, 0.4)}` },
                  transition: 'all 0.25s ease',
                }}
              >
                Get Started
              </Button>
            </Grid>
            <Grid item xs={12} md={7}>
              <Grid container spacing={2}>
                {CAPABILITIES.map((cap, i) => (
                  <Grid item xs={12} sm={6} key={i}>
                    <Box sx={{
                      display: 'flex', alignItems: 'center', gap: 1.5,
                      p: 2, borderRadius: 2,
                      bgcolor: alpha(primary, 0.04),
                      border: `1px solid ${alpha(primary, 0.08)}`,
                      transition: 'all 0.2s',
                      '&:hover': { bgcolor: alpha(primary, 0.07), borderColor: alpha(primary, 0.2) },
                    }}>
                      <CheckCircle sx={{ fontSize: 20, color: secondary }} />
                      <Typography variant="body2" sx={{ color: 'rgba(255,255,255,0.75)', fontWeight: 500 }}>
                        {cap}
                      </Typography>
                    </Box>
                  </Grid>
                ))}
              </Grid>
            </Grid>
          </Grid>
        </Container>
      </Box>

      {/* TESTIMONIALS */}
      <Box sx={{ py: { xs: 8, md: 14 }, px: 3, bgcolor: alpha(primary, 0.02) }}>
        <Container maxWidth="lg">
          <Box sx={{ textAlign: 'center', mb: { xs: 6, md: 8 } }}>
            <Typography
              variant="h3"
              sx={{ color: '#fff', fontWeight: 700, mb: 2, fontSize: { xs: '1.8rem', md: '2.5rem' } }}
            >
              Teams love Zerve Data AI
            </Typography>
            <Typography variant="body1" sx={{ color: 'rgba(255,255,255,0.5)', maxWidth: 500, mx: 'auto' }}>
              Don't take our word for it. Here's what our early adopters are saying.
            </Typography>
          </Box>

          <Grid container spacing={4}>
            {TESTIMONIALS.map((t, i) => (
              <Grid item xs={12} md={4} key={i}>
                <Box
                  sx={{
                    p: 4, height: '100%', borderRadius: 4,
                    border: `1px solid ${alpha(primary, 0.1)}`,
                    bgcolor: alpha(primary, 0.03),
                    display: 'flex', flexDirection: 'column',
                    transition: 'all 0.3s ease',
                    '&:hover': {
                      borderColor: alpha(primary, 0.25),
                      transform: 'translateY(-4px)',
                      boxShadow: `0 16px 48px ${alpha(primary, 0.08)}`,
                    },
                  }}
                >
                  <FormatQuote sx={{ fontSize: 32, color: alpha(primary, 0.4), mb: 2, transform: 'scaleX(-1)' }} />
                  <Typography variant="body1" sx={{ color: 'rgba(255,255,255,0.75)', lineHeight: 1.7, flexGrow: 1, mb: 3 }}>
                    "{t.quote}"
                  </Typography>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                    <Box sx={{
                      width: 44, height: 44, borderRadius: '50%',
                      background: `linear-gradient(135deg, ${alpha(primary, 0.3)}, ${alpha(secondary, 0.3)})`,
                      display: 'flex', alignItems: 'center', justifyContent: 'center',
                    }}>
                      <Typography variant="body2" sx={{ color: '#fff', fontWeight: 700 }}>
                        {t.name.split(' ').map(n => n[0]).join('')}
                      </Typography>
                    </Box>
                    <Box>
                      <Typography variant="body2" sx={{ color: '#fff', fontWeight: 600 }}>{t.name}</Typography>
                      <Typography variant="caption" sx={{ color: 'rgba(255,255,255,0.4)' }}>
                        {t.role}, {t.company}
                      </Typography>
                    </Box>
                  </Box>
                </Box>
              </Grid>
            ))}
          </Grid>
        </Container>
      </Box>

      {/* ROI SECTION */}
      <Box sx={{ py: { xs: 8, md: 12 }, px: 3 }}>
        <Container maxWidth="md">
          <Box
            sx={{
              textAlign: 'center',
              p: { xs: 4, md: 6 },
              borderRadius: 4,
              border: `1px solid ${alpha(secondary, 0.15)}`,
              bgcolor: alpha(secondary, 0.03),
              position: 'relative',
              overflow: 'hidden',
            }}
          >
            <Box sx={{
              position: 'absolute', top: -60, right: -60,
              width: 200, height: 200, borderRadius: '50%',
              background: `radial-gradient(circle, ${alpha(secondary, 0.1)}, transparent 70%)`,
              pointerEvents: 'none',
            }} />
            <TrendingUp sx={{ fontSize: 48, color: secondary, mb: 2 }} />
            <Typography variant="h4" sx={{ color: '#fff', fontWeight: 700, mb: 2 }}>
              Teams make decisions 10x faster with AI-powered data
            </Typography>
            <Typography variant="body1" sx={{ color: 'rgba(255,255,255,0.55)', maxWidth: 500, mx: 'auto', lineHeight: 1.7 }}>
              Stop waiting for reports. When anyone on your team can ask questions and get
              instant answers, better decisions happen naturally.
            </Typography>
          </Box>
        </Container>
      </Box>

      {/* FINAL CTA */}
      <Box
        sx={{
          position: 'relative',
          background: `linear-gradient(135deg, ${primary} 0%, ${secondary} 100%)`,
          py: { xs: 8, md: 12 },
          px: 3,
          textAlign: 'center',
          overflow: 'hidden',
        }}
      >
        <Box sx={{
          position: 'absolute', inset: 0, opacity: 0.06, pointerEvents: 'none',
          backgroundImage: 'radial-gradient(circle, rgba(255,255,255,0.8) 1px, transparent 1px)',
          backgroundSize: '24px 24px',
        }} />
        <Container maxWidth="sm" sx={{ position: 'relative', zIndex: 1 }}>
          <Typography
            variant="h3"
            sx={{ color: '#fff', fontWeight: 800, mb: 2, fontSize: { xs: '1.8rem', md: '2.5rem' } }}
          >
            Ready to unlock your data?
          </Typography>
          <Typography variant="body1" sx={{ color: 'rgba(255,255,255,0.85)', mb: 4, lineHeight: 1.7 }}>
            Join teams who've stopped guessing and started understanding their data.
            Free forever for individuals.
          </Typography>
          <Box sx={{ display: 'flex', gap: 2, justifyContent: 'center', flexWrap: 'wrap' }}>
            <Button
              variant="contained"
              size="large"
              endIcon={<ArrowForward />}
              onClick={() => navigate(isAuthenticated ? '/projects' : '/register')}
              sx={{
                bgcolor: '#fff',
                color: primary,
                fontWeight: 700,
                px: 5, py: 1.5,
                borderRadius: 2,
                fontSize: '1.05rem',
                textTransform: 'none',
                '&:hover': { bgcolor: 'rgba(255,255,255,0.92)', transform: 'translateY(-2px)' },
                transition: 'all 0.25s ease',
              }}
            >
              {isAuthenticated ? 'Go to App' : 'Get Started Free'}
            </Button>
          </Box>
          <Typography variant="body2" sx={{ color: 'rgba(255,255,255,0.5)', mt: 2 }}>
            No credit card required. Set up in under 2 minutes.
          </Typography>
        </Container>
      </Box>

      {/* Pulse keyframe */}
      <style>{`
        @keyframes pulse {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.4; }
        }
      `}</style>
    </Box>
  );
};

export default HomePage;
