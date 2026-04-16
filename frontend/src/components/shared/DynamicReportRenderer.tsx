import React from 'react';
import {
  Box, Card, CardContent, Typography, Grid,
  Table, TableBody, TableCell, TableContainer, TableHead, TableRow,
  Paper, CircularProgress,
} from '@mui/material';
import {
  BarChart, Bar, LineChart, Line, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
} from 'recharts';
import {
  ReportTemplate, ReportData, Section, TextSection,
  TableSection, ChartSection, GridSection,
} from '../../types/reportTemplates';

interface DynamicReportRendererProps {
  template: ReportTemplate;
  data: ReportData;
  loading?: boolean;
  error?: string | null;
}

const CHART_COLORS = ['#7b6df6', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF', '#FF9F40', '#FF6384', '#10b981'];

const formatValue = (value: any, format?: string, prefix?: string, suffix?: string): string => {
  if (value === null || value === undefined) return 'N/A';
  let formatted = value;
  switch (format) {
    case 'currency':
      formatted = new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(Number(value));
      break;
    case 'percentage':
      formatted = `${Number(value).toFixed(2)}%`;
      break;
    case 'number':
      formatted = new Intl.NumberFormat('en-US').format(Number(value));
      break;
    default:
      formatted = String(value);
  }
  return `${prefix || ''}${formatted}${suffix || ''}`;
};

const TextComponent: React.FC<{ section: TextSection; data: ReportData }> = ({ section, data }) => {
  const value = data[section.field];
  const formattedValue = formatValue(value, section.format, section.prefix, section.suffix);
  const colorMap: Record<string, string> = {
    success: 'success.main', warning: 'warning.main', error: 'error.main',
    info: 'info.main', secondary: 'secondary.main', primary: 'primary.main',
  };
  return (
    <Card sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      <CardContent sx={{ flexGrow: 1, textAlign: 'center' }}>
        <Typography variant="h6" color="text.secondary" gutterBottom>{section.title}</Typography>
        <Typography variant="h3" component="div" sx={{ color: colorMap[section.color || 'primary'], fontWeight: 'bold', mb: 1 }}>
          {formattedValue}
        </Typography>
      </CardContent>
    </Card>
  );
};

const TableComponent: React.FC<{ section: TableSection; data: ReportData }> = ({ section, data }) => {
  const tableData = data[section.field] || [];
  return (
    <Card sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      <CardContent sx={{ flexGrow: 1 }}>
        <Typography variant="h6" gutterBottom>{section.title}</Typography>
        <Box sx={{ maxHeight: section.height || 300, overflow: 'auto' }}>
          <TableContainer component={Paper} sx={{ maxHeight: 'unset' }}>
            <Table stickyHeader size="small">
              <TableHead>
                <TableRow>
                  {section.columns.map((col) => (
                    <TableCell key={col.field} align={col.align as any}>{col.label}</TableCell>
                  ))}
                </TableRow>
              </TableHead>
              <TableBody>
                {tableData.map((row: any, i: number) => (
                  <TableRow key={i}>
                    {section.columns.map((col) => (
                      <TableCell key={col.field} align={col.align as any}>
                        {col.format === 'html'
                          ? <span dangerouslySetInnerHTML={{ __html: row[col.field] }} />
                          : formatValue(row[col.field], col.format)}
                      </TableCell>
                    ))}
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </Box>
      </CardContent>
    </Card>
  );
};

const ChartComponent: React.FC<{ section: ChartSection; data: ReportData }> = ({ section, data }) => {
  const chartData = data[section.dataField] || [];
  const xKey = section.xField || 'label';
  const yKey = section.yField || 'value';

  const renderChart = () => {
    switch (section.chartType) {
      case 'bar':
        return (
          <BarChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey={xKey} />
            <YAxis />
            <Tooltip />
            <Legend />
            <Bar dataKey={yKey} fill="#7b6df6" />
          </BarChart>
        );
      case 'line':
      case 'area':
        return (
          <LineChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey={xKey} />
            <YAxis />
            <Tooltip />
            <Legend />
            <Line type="monotone" dataKey={yKey} stroke="#7b6df6" />
          </LineChart>
        );
      case 'pie':
      case 'doughnut':
        return (
          <PieChart>
            <Pie
              data={chartData}
              dataKey={yKey}
              nameKey={xKey}
              cx="50%"
              cy="50%"
              outerRadius={100}
              innerRadius={section.chartType === 'doughnut' ? 60 : 0}
              label
            >
              {chartData.map((_: any, i: number) => (
                <Cell key={i} fill={CHART_COLORS[i % CHART_COLORS.length]} />
              ))}
            </Pie>
            <Tooltip />
            <Legend />
          </PieChart>
        );
      default:
        return <Typography color="error">Unknown chart type: {section.chartType}</Typography>;
    }
  };

  return (
    <Card sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      <CardContent sx={{ flexGrow: 1 }}>
        <Typography variant="h6" gutterBottom>{section.title}</Typography>
        <Box sx={{ height: 300 }}>
          <ResponsiveContainer width="100%" height="100%">
            {renderChart()}
          </ResponsiveContainer>
        </Box>
      </CardContent>
    </Card>
  );
};

const GridComponent: React.FC<{ section: GridSection; data: ReportData }> = ({ section, data }) => {
  const items = data[section.itemsField] || [];
  return (
    <Card sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      <CardContent sx={{ flexGrow: 1 }}>
        <Typography variant="h6" gutterBottom>{section.title}</Typography>
        <Grid container spacing={section.spacing || 2}>
          {items.map((item: any, i: number) => (
            <Grid item xs={12} sm={6} md={4} key={i}>
              <Card variant="outlined">
                <CardContent>
                  <Typography variant="body2" color="text.secondary">{section.itemTemplate.title}</Typography>
                  <Typography variant="h6">{formatValue(item[section.itemTemplate.field], section.itemTemplate.format)}</Typography>
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
      </CardContent>
    </Card>
  );
};

const DynamicReportRenderer: React.FC<DynamicReportRendererProps> = ({ template, data, loading = false, error = null }) => {
  const renderSection = (section: Section) => {
    switch (section.component) {
      case 'Text':
      case 'Metric':
        return <TextComponent section={section as TextSection} data={data} />;
      case 'Table':
        return <TableComponent section={section as TableSection} data={data} />;
      case 'Chart':
        return <ChartComponent section={section as ChartSection} data={data} />;
      case 'Grid':
        return <GridComponent section={section as GridSection} data={data} />;
      default:
        return <Card><CardContent><Typography color="error">Unknown component: {(section as any).component}</Typography></CardContent></Card>;
    }
  };

  const hasRowGrouping = template.sections.some((s: any) => s.row !== undefined);
  let grouped: Record<string, Section[]> = {};
  if (hasRowGrouping) {
    template.sections.forEach((s: any) => {
      const key = s.row !== undefined ? String(s.row) : 'default';
      if (!grouped[key]) grouped[key] = [];
      grouped[key].push(s);
    });
  }

  if (loading) return <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: 400 }}><CircularProgress /></Box>;
  if (error) return <Card><CardContent><Typography color="error" variant="h6">Error: {error}</Typography></CardContent></Card>;

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom>{template.title}</Typography>
      {template.description && <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>{template.description}</Typography>}
      {hasRowGrouping ? (
        Object.keys(grouped).sort().map((key) => (
          <Grid container spacing={3} key={key} sx={{ mb: 1 }}>
            {grouped[key].map((section, i) => (
              <Grid item xs={12} md={typeof section.width === 'number' ? section.width : parseInt(section.width || '12', 10)} key={i}>
                {renderSection(section)}
              </Grid>
            ))}
          </Grid>
        ))
      ) : (
        <Grid container spacing={3}>
          {template.sections.map((section, i) => (
            <Grid item xs={12} md={typeof section.width === 'number' ? section.width : parseInt(section.width || '12', 10)} key={i}>
              {renderSection(section)}
            </Grid>
          ))}
        </Grid>
      )}
    </Box>
  );
};

export default DynamicReportRenderer;
