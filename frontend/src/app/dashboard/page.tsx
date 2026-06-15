'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Dashboard } from '@/components/dashboard';
import { Project } from '@/components/dashboard';
import { Button } from '@/components/ui/button';
import { api } from '@/lib/api';

export default function DashboardPage() {
  const router = useRouter();
  const [projects, setProjects] = useState<Project[]>([]);
  const [userName, setUserName] = useState('User');
  const [loading, setLoading] = useState(true);

  // Create Project Modal States
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [projectName, setProjectName] = useState('');
  const [projectDescription, setProjectDescription] = useState('');
  const [createError, setCreateError] = useState<string | null>(null);
  const [isCreating, setIsCreating] = useState(false);

  useEffect(() => {
    // Check if token exists
    const token = localStorage.getItem('access_token');
    if (!token) {
      router.push('/login');
      return;
    }

    // Fetch user details and projects
    const fetchData = async () => {
      try {
        setLoading(true);

        // Fetch User Info
        const userRes = await api.me();
        if (userRes.ok) {
          const userData = await userRes.json();
          const fullName = `${userData.first_name} ${userData.last_name}`.trim();
          setUserName(fullName || userData.username || 'User');
        }

        // Fetch Projects
        await fetchProjects();
      } catch (err) {
        console.error('Error fetching dashboard data:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [router]);

  const fetchProjects = async () => {
    try {
      const res = await api.getMyProjects(1, 100);
      if (res.ok) {
        const data = await res.json();
        // Map backend 'uid' to frontend 'id'
        const mapped: Project[] = (data.items || []).map((p: any) => ({
          id: String(p.uid),
          name: p.name,
          description: p.description || '',
          status: p.status === 'archived' ? 'archived' : 'active',
        }));
        setProjects(mapped);
      }
    } catch (err) {
      console.error('Error fetching projects:', err);
    }
  };

  const handleCreateProject = () => {
    setProjectName('');
    setProjectDescription('');
    setCreateError(null);
    setIsModalOpen(true);
  };

  const handleSubmitProject = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!projectName.trim()) {
      setCreateError('Project name is required');
      return;
    }

    setIsCreating(true);
    setCreateError(null);
    try {
      const res = await api.createProject({
        name: projectName,
        description: projectDescription,
      });

      if (res.ok) {
        // Refresh project list
        await fetchProjects();
        // Close modal
        setIsModalOpen(false);
      } else {
        const errData = await res.json();
        setCreateError(errData.message || errData.detail || 'Failed to create project');
      }
    } catch (err) {
      console.error('Error creating project:', err);
      setCreateError('A connection error occurred. Please try again.');
    } finally {
      setIsCreating(false);
    }
  };

  const handleViewProject = (projectId: string) => {
    router.push(`/projects/${projectId}`);
  };

  const handleLogout = async () => {
    try {
      await api.logout();
    } catch (err) {
      console.error('Logout error:', err);
    } finally {
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      router.push('/login');
    }
  };

  const handleSettings = () => {
    // Optional: Settings navigation or action
    console.log('Settings clicked');
  };

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-background">
        <div className="text-center">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent mx-auto"></div>
          <p className="mt-4 text-muted-foreground">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <>
      <Dashboard
        projects={projects}
        onCreateProject={handleCreateProject}
        onViewProject={handleViewProject}
        onLogout={handleLogout}
        onSettings={handleSettings}
        userName={userName}
      />

      {/* Modal for creating a new project */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
          <div className="bg-card border border-border rounded-lg p-6 max-w-md w-full mx-4 shadow-lg text-card-foreground">
            <h2 className="text-xl font-bold mb-4">Create New Project</h2>
            
            {createError && (
              <div className="p-3 text-sm text-destructive bg-destructive/10 border border-destructive/20 rounded-md mb-4">
                {createError}
              </div>
            )}

            <form onSubmit={handleSubmitProject} className="space-y-4">
              <div>
                <label htmlFor="modalProjectName" className="text-sm font-medium">Project Name</label>
                <input
                  id="modalProjectName"
                  type="text"
                  required
                  disabled={isCreating}
                  className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 mt-1"
                  placeholder="e.g. Website Redesign"
                  value={projectName}
                  onChange={(e) => setProjectName(e.target.value)}
                />
              </div>
              <div>
                <label htmlFor="modalProjectDescription" className="text-sm font-medium">Description</label>
                <textarea
                  id="modalProjectDescription"
                  disabled={isCreating}
                  className="flex min-h-[80px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 mt-1"
                  placeholder="Describe your project"
                  value={projectDescription}
                  onChange={(e) => setProjectDescription(e.target.value)}
                />
              </div>

              <div className="flex justify-end gap-3 mt-6">
                <Button 
                  type="button" 
                  variant="outline" 
                  disabled={isCreating}
                  onClick={() => { setIsModalOpen(false); setCreateError(null); }}
                >
                  Cancel
                </Button>
                <Button type="submit" disabled={isCreating}>
                  {isCreating ? 'Creating...' : 'Create'}
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </>
  );
}
