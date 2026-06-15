'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { TaskCard } from '@/components/task-card';
import { TaskDrawer } from '@/components/task-drawer';
import { Plus } from 'lucide-react';

interface Task {
  id: string;
  title: string;
  description?: string;
  priority: 'low' | 'medium' | 'high' | 'critical';
  status: 'todo' | 'in_progress' | 'in_review' | 'done';
  dueDate?: string;
  assignee?: string;
}

interface Comment {
  uid: string;
  content: string;
  author_uid: string;
  created_at: string;
}

interface KanbanBoardProps {
  tasks: Task[];
  onCreateTask?: (taskData: any) => void;
  onTaskClick?: (task: Task) => void;
  onUpdateTask?: (taskId: string, taskData: any) => void;
  currentUserUid?: string;
  comments?: Comment[];
  onAddComment?: (content: string) => void;
  onDeleteComment?: (commentUid: string) => void;
}

const columns = [
  { id: 'todo', title: 'To Do', key: 'todo' },
  { id: 'in_progress', title: 'In Progress', key: 'in_progress' },
  { id: 'in_review', title: 'In Review', key: 'in_review' },
  { id: 'done', title: 'Done', key: 'done' },
];

export function KanbanBoard({
  tasks,
  onCreateTask,
  onTaskClick,
  onUpdateTask,
  currentUserUid = 'user-1',
  comments = [],
  onAddComment,
  onDeleteComment,
}: KanbanBoardProps) {
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [selectedTask, setSelectedTask] = useState<Task | undefined>(undefined);

  const handleTaskCardClick = (task: Task) => {
    setSelectedTask(task);
    setDrawerOpen(true);
    onTaskClick?.(task);
  };

  const handleCreateClick = () => {
    setSelectedTask(undefined);
    setDrawerOpen(true);
  };

  const handleDrawerSubmit = (data: any) => {
    if (selectedTask) {
      onUpdateTask?.(selectedTask.id, data);
    } else {
      onCreateTask?.(data);
    }
  };

  const getTasksByStatus = (status: string) => {
    return tasks.filter(task => task.status === status);
  };

  return (
    <>
      <div className="space-y-6">
        {/* Header with Create Button */}
        <div className="flex items-center justify-between">
          <h2 className="text-2xl font-bold text-foreground">Tasks</h2>
          <Button onClick={handleCreateClick} className="gap-2">
            <Plus className="h-4 w-4" />
            Create Task
          </Button>
        </div>

        {/* Kanban Columns */}
        <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-4 gap-6">
          {columns.map(column => (
            <div key={column.id} className="flex flex-col">
              {/* Column Header */}
              <div className="mb-4">
                <h3 className="font-semibold text-foreground text-lg">
                  {column.title}
                </h3>
                <p className="text-xs text-muted-foreground mt-1">
                  {getTasksByStatus(column.key).length} task
                  {getTasksByStatus(column.key).length !== 1 ? 's' : ''}
                </p>
              </div>

              {/* Tasks Container */}
              <div className="flex-1 space-y-3 min-h-96 rounded-lg bg-muted/30 p-4">
                {getTasksByStatus(column.key).length === 0 ? (
                  <div className="h-full flex items-center justify-center text-center">
                    <p className="text-sm text-muted-foreground">No tasks yet</p>
                  </div>
                ) : (
                  getTasksByStatus(column.key).map(task => (
                    <TaskCard
                      key={task.id}
                      id={task.id}
                      title={task.title}
                      priority={task.priority}
                      dueDate={task.dueDate}
                      assignee={task.assignee}
                      onClick={() => handleTaskCardClick(task)}
                    />
                  ))
                )}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Task Drawer */}
      <TaskDrawer
        open={drawerOpen}
        onOpenChange={setDrawerOpen}
        task={selectedTask}
        onSubmit={handleDrawerSubmit}
        comments={comments}
        currentUserUid={currentUserUid}
        onAddComment={onAddComment}
        onDeleteComment={onDeleteComment}
      />
    </>
  );
}
