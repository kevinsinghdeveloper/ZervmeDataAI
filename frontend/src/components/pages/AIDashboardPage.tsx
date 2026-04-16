import React, { useEffect, useState, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Container, Box, Typography, Card, CardContent, CircularProgress, Button,
} from '@mui/material';
import { ArrowBack, InfoOutlined } from '@mui/icons-material';
import { ReportTemplate, ReportData } from '../../types/reportTemplates';
import apiService from '../../utils/api.service';
import DynamicReportRenderer from '../shared/DynamicReportRenderer';

const AIDashboardPage: React.FC = () => {
  const { reportId } = useParams<{ reportId: string }>();
  const navigate = useNavigate();
  const [template, setTemplate] = useState<ReportTemplate | null>(null);
  const [data, setData] = useState<ReportData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchDashboard = useCallback(async () => {
    if (!reportId) return;
    setLoading(true);
    setError(null);
    try {
      const res = await apiService.getDashboardForReport(reportId);
      const raw = res?.data || res;
      if (raw?.template && raw?.data) {
        setTemplate(typeof raw.template === 'string' ? JSON.parse(raw.template) : raw.template);
        setData(typeof raw.data === 'string' ? JSON.parse(raw.data) : raw.data);
      } else {
        setError('No dashboard data available for this report. Run the report first to generate results.');
      }
    } catch (err: any) {
      setError(err.message || 'Failed to load dashboard');
    } finally {
      setLoading(false);
    }
  }, [reportId]);

  useEffect(() => { fetchDashboard(); }, [fetchDashboard]);

  if (!reportId) {
    return (
      <Container maxWidth="md" sx={{ py: 8 }}>
        <Card variant="outlined" sx={{ borderRadius: 3, textAlign: 'center' }}>
          <CardContent sx={{ py: 8 }}>
            <InfoOutlined sx={{ fontSize: 56, color: 'primary.main', mb: 2 }} />
            <Typography variant="h5" gutterBottom>No Report Selected</Typography>
            <Typography variant="body1" color="text.secondary">
              Select a report from the Explore page to view its dashboard.
            </Typography>
          </CardContent>
        </Card>
      </Container>
    );
  }

  return (
    <Container maxWidth="xl" sx={{ py: 3 }}>
      <Box sx={{ mb: 2 }}>
        <Button startIcon={<ArrowBack />} onClick={() => navigate('/explore')} sx={{ mb: 1 }}>
          Back to Explore
        </Button>
      </Box>

      {loading ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: 400 }}>
          <CircularProgress />
        </Box>
      ) : error ? (
        <Card variant="outlined" sx={{ borderRadius: 3, textAlign: 'center' }}>
          <CardContent sx={{ py: 8 }}>
            <InfoOutlined sx={{ fontSize: 56, color: 'warning.main', mb: 2 }} />
            <Typography variant="h6" gutterBottom>Dashboard Unavailable</Typography>
            <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>{error}</Typography>
            <Button variant="contained" onClick={fetchDashboard}>Retry</Button>
          </CardContent>
        </Card>
      ) : template && data ? (
        <DynamicReportRenderer template={template} data={data} />
      ) : null}
    </Container>
  );
};

export default AIDashboardPage;
