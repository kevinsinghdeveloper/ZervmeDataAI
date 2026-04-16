import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { useAuth } from './AuthContext';
import apiService from '../../utils/api.service';
import { ReportTemplate, ReportData } from '../../types/reportTemplates';
import { Project, ReportInfo, DatasetInfo, ModelConfig } from '../../types';

interface ExplorerContextType {
  // Projects
  projects: Project[];
  projectsLoading: boolean;
  fetchProjects: () => Promise<void>;

  // Reports
  reports: ReportInfo[];
  reportsLoading: boolean;
  fetchReports: (projectId?: string) => Promise<void>;
  focusedReport: ReportInfo | null;
  setFocusedReport: React.Dispatch<React.SetStateAction<ReportInfo | null>>;

  // Datasets
  datasets: DatasetInfo[];
  datasetsLoading: boolean;
  fetchDatasets: () => Promise<void>;

  // Model Configs
  modelConfigs: ModelConfig[];
  modelConfigsLoading: boolean;
  fetchModelConfigs: () => Promise<void>;

  // Dashboard
  dashboardTemplate: ReportTemplate | null;
  dashboardData: ReportData | null;
  dashboardLoading: boolean;
  dashboardError: string | null;
  fetchDashboardForReport: (reportId: string) => Promise<void>;
}

const ExplorerContext = createContext<ExplorerContextType | undefined>(undefined);

export const useExplorer = () => {
  const context = useContext(ExplorerContext);
  if (!context) throw new Error('useExplorer must be used within ExplorerContextProvider');
  return context;
};

export const ExplorerContextProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { isAuthenticated } = useAuth();

  // Projects
  const [projects, setProjects] = useState<Project[]>([]);
  const [projectsLoading, setProjectsLoading] = useState(false);

  // Reports
  const [reports, setReports] = useState<ReportInfo[]>([]);
  const [reportsLoading, setReportsLoading] = useState(false);
  const [focusedReport, setFocusedReport] = useState<ReportInfo | null>(null);

  // Datasets
  const [datasets, setDatasets] = useState<DatasetInfo[]>([]);
  const [datasetsLoading, setDatasetsLoading] = useState(false);

  // Model Configs
  const [modelConfigs, setModelConfigs] = useState<ModelConfig[]>([]);
  const [modelConfigsLoading, setModelConfigsLoading] = useState(false);

  // Dashboard
  const [dashboardTemplate, setDashboardTemplate] = useState<ReportTemplate | null>(null);
  const [dashboardData, setDashboardData] = useState<ReportData | null>(null);
  const [dashboardLoading, setDashboardLoading] = useState(false);
  const [dashboardError, setDashboardError] = useState<string | null>(null);

  const fetchProjects = useCallback(async () => {
    setProjectsLoading(true);
    try {
      const res = await apiService.listProjects();
      const data = res?.data?.projects || res?.data || res?.projects || [];
      setProjects(Array.isArray(data) ? data : []);
    } catch {
      setProjects([]);
    } finally {
      setProjectsLoading(false);
    }
  }, []);

  const fetchReports = useCallback(async (projectId?: string) => {
    setReportsLoading(true);
    try {
      const params = projectId ? { project_id: projectId } : undefined;
      const res = await apiService.listReports(params);
      const data = res?.data?.reports || res?.data || res?.reports || [];
      setReports(Array.isArray(data) ? data : []);
    } catch {
      setReports([]);
    } finally {
      setReportsLoading(false);
    }
  }, []);

  const fetchDatasets = useCallback(async () => {
    setDatasetsLoading(true);
    try {
      const res = await apiService.listDatasets();
      const data = res?.data?.datasets || res?.data || res?.datasets || [];
      setDatasets(Array.isArray(data) ? data : []);
    } catch {
      setDatasets([]);
    } finally {
      setDatasetsLoading(false);
    }
  }, []);

  const fetchModelConfigs = useCallback(async () => {
    setModelConfigsLoading(true);
    try {
      const res = await apiService.listModelConfigs();
      const data = res?.data?.model_configs || res?.data || res?.model_configs || [];
      setModelConfigs(Array.isArray(data) ? data : []);
    } catch {
      setModelConfigs([]);
    } finally {
      setModelConfigsLoading(false);
    }
  }, []);

  const fetchDashboardForReport = useCallback(async (reportId: string) => {
    setDashboardLoading(true);
    setDashboardError(null);
    setDashboardTemplate(null);
    setDashboardData(null);
    try {
      const res = await apiService.getDashboardForReport(reportId);
      const raw = res?.data || res;
      if (raw?.template && raw?.data) {
        setDashboardTemplate(typeof raw.template === 'string' ? JSON.parse(raw.template) : raw.template);
        setDashboardData(typeof raw.data === 'string' ? JSON.parse(raw.data) : raw.data);
      } else {
        throw new Error('Invalid dashboard response');
      }
    } catch (err: any) {
      setDashboardError(err.message || 'Failed to load dashboard');
    } finally {
      setDashboardLoading(false);
    }
  }, []);

  // Load initial data when authenticated
  useEffect(() => {
    if (isAuthenticated) {
      fetchProjects();
      fetchReports();
      fetchDatasets();
      fetchModelConfigs();
    } else {
      setProjects([]);
      setReports([]);
      setDatasets([]);
      setModelConfigs([]);
      setFocusedReport(null);
      setDashboardTemplate(null);
      setDashboardData(null);
    }
  }, [isAuthenticated, fetchProjects, fetchReports, fetchDatasets, fetchModelConfigs]);

  return (
    <ExplorerContext.Provider value={{
      projects, projectsLoading, fetchProjects,
      reports, reportsLoading, fetchReports,
      focusedReport, setFocusedReport,
      datasets, datasetsLoading, fetchDatasets,
      modelConfigs, modelConfigsLoading, fetchModelConfigs,
      dashboardTemplate, dashboardData, dashboardLoading, dashboardError,
      fetchDashboardForReport,
    }}>
      {children}
    </ExplorerContext.Provider>
  );
};
