import React, { useState, useEffect } from 'react';
import {
  Container, Typography, Grid, Card, CardContent, CardActionArea, Box,
  Button, Chip, Divider, List, ListItemButton, ListItemText, CircularProgress,
} from '@mui/material';
import {
  Assessment, FolderOpen, PlayArrow, Add,
  Visibility, TrendingUp, Storage,
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { useNotification } from '../context_providers/NotificationContext';
import { Project, ReportInfo } from '../../types';
import apiService from '../../utils/api.service';
import LoadingSpinner from '../shared/LoadingSpinner';

const ExplorePage: React.FC = () => {
  const navigate = useNavigate();
  const { showError } = useNotification();
  const [projects, setProjects] = useState<Project[]>([]);
  const [reports, setReports] = useState<ReportInfo[]>([]);
  const [selectedProjectId, setSelectedProjectId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [reportsLoading, setReportsLoading] = useState(false);

  useEffect(() => {
    const fetchData = async () => {
      setIsLoading(true);
      try {
        const [projRes, repRes] = await Promise.all([
          apiService.listProjects(),
          apiService.listReports(),
        ]);
        const projData = projRes?.data?.projects || projRes?.data || projRes?.projects || [];
        setProjects(Array.isArray(projData) ? projData : []);
        const repData = repRes?.data?.reports || repRes?.data || repRes?.reports || [];
        setReports(Array.isArray(repData) ? repData : []);
      } catch (err: any) {
        showError(err.message || 'Failed to load data');
      } finally {
        setIsLoading(false);
      }
    };
    fetchData();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleProjectSelect = async (projectId: string) => {
    setSelectedProjectId(projectId === selectedProjectId ? null : projectId);
    if (projectId !== selectedProjectId) {
      setReportsLoading(true);
      try {
        const res = await apiService.listReports({ project_id: projectId });
        const data = res?.data?.reports || res?.data || res?.reports || [];
        setReports(Array.isArray(data) ? data : []);
      } catch { /* keep existing */ }
      finally { setReportsLoading(false); }
    }
  };

  const filteredReports = selectedProjectId
    ? reports.filter(r => r.projectId === selectedProjectId)
    : reports;

  if (isLoading) return <LoadingSpinner message="Loading workspace..." />;

  return (
    <Container maxWidth="xl" sx={{ py: 4 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 4 }}>
        <Box>
          <Typography variant="h4" fontWeight={700}>Explore</Typography>
          <Typography variant="body1" color="text.secondary">
            Browse projects, reports, and AI-generated insights
          </Typography>
        </Box>
        <Box sx={{ display: 'flex', gap: 1.5 }}>
          <Button variant="outlined" startIcon={<Add />} onClick={() => navigate('/projects')}>
            New Project
          </Button>
          <Button variant="contained" startIcon={<Assessment />} onClick={() => navigate('/models')}>
            Models
          </Button>
        </Box>
      </Box>

      {/* Stats cards */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        {[
          { icon: <FolderOpen />, label: 'Projects', value: projects.length, color: '#7b6df6' },
          { icon: <Assessment />, label: 'Reports', value: reports.length, color: '#3b82f6' },
          { icon: <TrendingUp />, label: 'Active', value: reports.filter(r => r.status === 'active').length, color: '#10b981' },
          { icon: <Storage />, label: 'Completed Runs', value: reports.filter(r => r.lastRunDate).length, color: '#f59e0b' },
        ].map((stat, i) => (
          <Grid item xs={6} md={3} key={i}>
            <Card variant="outlined" sx={{ borderRadius: 3 }}>
              <CardContent sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                <Box sx={{ width: 48, height: 48, borderRadius: 2, bgcolor: `${stat.color}20`, display: 'flex', alignItems: 'center', justifyContent: 'center', color: stat.color }}>
                  {stat.icon}
                </Box>
                <Box>
                  <Typography variant="h5" fontWeight={700}>{stat.value}</Typography>
                  <Typography variant="body2" color="text.secondary">{stat.label}</Typography>
                </Box>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>

      <Grid container spacing={3}>
        {/* Project sidebar */}
        <Grid item xs={12} md={3}>
          <Card variant="outlined" sx={{ borderRadius: 3 }}>
            <CardContent>
              <Typography variant="h6" fontWeight={600} sx={{ mb: 2 }}>Projects</Typography>
              {projects.length === 0 ? (
                <Typography variant="body2" color="text.secondary">No projects yet</Typography>
              ) : (
                <List dense>
                  <ListItemButton
                    selected={!selectedProjectId}
                    onClick={() => { setSelectedProjectId(null); }}
                    sx={{ borderRadius: 1, mb: 0.5 }}
                  >
                    <ListItemText primary="All Reports" />
                    <Chip size="small" label={reports.length} />
                  </ListItemButton>
                  <Divider sx={{ my: 1 }} />
                  {projects.map(p => (
                    <ListItemButton
                      key={p.id}
                      selected={selectedProjectId === p.id}
                      onClick={() => handleProjectSelect(p.id)}
                      sx={{ borderRadius: 1, mb: 0.5 }}
                    >
                      <ListItemText primary={p.name} secondary={p.status} />
                    </ListItemButton>
                  ))}
                </List>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Reports grid */}
        <Grid item xs={12} md={9}>
          {reportsLoading ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', py: 6 }}><CircularProgress /></Box>
          ) : filteredReports.length === 0 ? (
            <Card variant="outlined" sx={{ borderRadius: 3 }}>
              <CardContent sx={{ textAlign: 'center', py: 8 }}>
                <Assessment sx={{ fontSize: 56, color: 'text.disabled', mb: 2 }} />
                <Typography variant="h6" color="text.secondary" gutterBottom>No reports found</Typography>
                <Typography variant="body2" color="text.disabled" sx={{ mb: 3 }}>
                  Create a report to start generating AI insights
                </Typography>
              </CardContent>
            </Card>
          ) : (
            <Grid container spacing={2.5}>
              {filteredReports.map(report => (
                <Grid item xs={12} sm={6} lg={4} key={report.id}>
                  <Card variant="outlined" sx={{
                    height: '100%', borderRadius: 3,
                    transition: 'all 0.2s',
                    '&:hover': { transform: 'translateY(-2px)', boxShadow: '0 8px 24px rgba(0,0,0,0.15)' },
                  }}>
                    <CardActionArea onClick={() => navigate(`/dashboard/${report.id}`)}>
                      <CardContent>
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                          <Chip label={report.status} size="small" color={report.status === 'active' ? 'success' : 'default'} />
                          {report.lastRunDate && (
                            <Typography variant="caption" color="text.secondary">
                              Last run: {new Date(report.lastRunDate).toLocaleDateString()}
                            </Typography>
                          )}
                        </Box>
                        <Typography variant="h6" fontWeight={600} sx={{ mb: 0.5 }}>{report.name}</Typography>
                        <Box sx={{ display: 'flex', gap: 1, mt: 2 }}>
                          <Button size="small" startIcon={<Visibility />} variant="text">View</Button>
                          <Button size="small" startIcon={<PlayArrow />} variant="text" color="success">Run</Button>
                        </Box>
                      </CardContent>
                    </CardActionArea>
                  </Card>
                </Grid>
              ))}
            </Grid>
          )}
        </Grid>
      </Grid>
    </Container>
  );
};

export default ExplorePage;
