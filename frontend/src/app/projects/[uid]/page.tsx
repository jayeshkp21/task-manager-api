'use client';

import { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { DashboardNavbar } from '@/components/dashboard-navbar';
import { ProjectHeader } from '@/components/project-header';
import { KanbanBoard } from '@/components/kanban-board';
import { api } from '@/lib/api';

interface Task {
  id: string;
  title: string;
  description?: string;
  priority: 'low' | 'medium' | 'high' | 'critical';
  status: 'todo' | 'in_progress' | 'in_review' | 'done';
  dueDate?: string;
  assignee?: string;
}

export default function ProjectBoardPage() {
  const params = useParams();
  const router = useRouter();
  const uid = params.uid as string;

  const [projectData, setProjectData] = useState<{ name: string; description: string } | null>(null);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [userName, setUserName] = useState('User');
  const [loading, setLoading] = useState(true);
  const [currentUserUid, setCurrentUserUid] = useState<string | null>(null);

  const validateUuid = (str: string) => {
    const regex = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
    return regex.test(str);
  };

  useEffect(() => {
    const token = localStorage.getItem('access_token');
    if (!token) {
      router.push('/login');
      return;
    }

    const loadData = async () => {
      try {
        setLoading(true);

        // Fetch User Info
        const userRes = await api.me();
        if (userRes.ok) {
          const userData = await userRes.json();
          setCurrentUserUid(String(userData.uid));
          const fullName = `${userData.first_name} ${userData.last_name}`.trim();
          setUserName(fullName || userData.username || 'User');
        }

        // Fetch Project Details
        const projectRes = await api.getProject(uid);
        if (projectRes.ok) {
          const project = await projectRes.json();
          setProjectData({
            name: project.name,
            description: project.description || '',
          });
        } else {
          // Redirect to dashboard if project not found
          router.push('/dashboard');
          return;
        }

        // Fetch Project Tasks
        await fetchTasks();
      } catch (err) {
        console.error('Error loading project details:', err);
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, [uid, router]);

  const fetchTasks = async () => {
    try {
      const res = await api.getProjectTasks(uid);
      if (res.ok) {
        const data = await res.json();
        // Map backend tasks to frontend state
        const mapped: Task[] = (data.items || []).map((t: any) => ({
          id: String(t.uid),
          title: t.title,
          description: t.description || '',
          priority: t.priority as any,
          status: t.status as any,
          dueDate: t.due_date || undefined,
          assignee: t.assigned_to || undefined,
        }));
        setTasks(mapped);
      }
    } catch (err) {
      console.error('Error fetching tasks:', err);
    }
  };

  const handleCreateTask = async (taskData: any) => {
    try {
      const assigneeUid = validateUuid(taskData.assignee) 
        ? taskData.assignee 
        : (taskData.assignee === 'me' ? currentUserUid : null);

      const res = await api.createTask(uid, {
        title: taskData.title,
        description: taskData.description || null,
        priority: taskData.priority,
        status: taskData.status,
        due_date: taskData.dueDate || null,
        assigned_to: assigneeUid,
      });

      if (res.ok) {
        await fetchTasks();
      } else {
        const err = await res.json();
        alert(err.message || err.detail || 'Failed to create task');
      }
    } catch (err) {
      console.error('Error creating task:', err);
    }
  };

  const handleUpdateTask = async (taskId: string, taskData: any) => {
    try {
      const assigneeUid = validateUuid(taskData.assignee) 
        ? taskData.assignee 
        : (taskData.assignee === 'me' ? currentUserUid : null);

      const res = await api.updateTask(uid, taskId, {
        title: taskData.title,
        description: taskData.description || null,
        priority: taskData.priority,
        status: taskData.status,
        due_date: taskData.dueDate || null,
        assigned_to: assigneeUid,
      });

      if (res.ok) {
        await fetchTasks();
      } else {
        const err = await res.json();
        alert(err.message || err.detail || 'Failed to update task');
      }
    } catch (err) {
      console.error('Error updating task:', err);
    }
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
    console.log('Settings clicked');
  };

  if (loading || !projectData) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-background">
        <div className="text-center">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent mx-auto"></div>
          <p className="mt-4 text-muted-foreground">Loading project board...</p>
        </div>
      </div>
    );
  }

  // Calculate project stats dynamically
  const stats = {
    totalTasks: tasks.length,
    completedTasks: tasks.filter(t => t.status === 'done').length,
    inProgressTasks: tasks.filter(
      t => t.status === 'in_progress' || t.status === 'in_review'
    ).length,
  };

  return (
    <main className="flex flex-col min-h-screen bg-background">
      <DashboardNavbar
        userName={userName}
        onLogout={handleLogout}
        onSettings={handleSettings}
      />

      <div className="flex-1 p-6 lg:p-8">
        <div className="max-w-7xl mx-auto space-y-8">
          {/* Project Header */}
          <ProjectHeader
            projectName={projectData.name}
            description={projectData.description}
            stats={stats}
          />

          {/* Kanban Board */}
          <KanbanBoard
            tasks={tasks}
            onCreateTask={handleCreateTask}
            onUpdateTask={handleUpdateTask}
          />
        </div>
      </div>
    </main>
  );
}
