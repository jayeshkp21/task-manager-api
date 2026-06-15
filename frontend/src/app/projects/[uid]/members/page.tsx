'use client';

import { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { ProjectMembers } from '@/components/project-members';
import { api } from '@/lib/api';

interface Member {
  uid: string;
  user_uid: string;
  role: 'owner' | 'admin' | 'member';
  username?: string;
  email?: string;
  joined_at: string;
}

export default function ProjectMembersPage() {
  const params = useParams();
  const router = useRouter();
  const uid = params.uid as string;

  const [projectName, setProjectName] = useState('Project');
  const [members, setMembers] = useState<Member[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem('access_token');
    if (!token) {
      router.push('/login');
      return;
    }

    const loadData = async () => {
      try {
        setLoading(true);
        // Fetch Project Name
        const projectRes = await api.getProject(uid);
        if (projectRes.ok) {
          const project = await projectRes.json();
          setProjectName(project.name);
        } else {
          router.push('/dashboard');
          return;
        }

        // Fetch Members
        await fetchMembers();
      } catch (err) {
        console.error('Error loading project members:', err);
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, [uid, router]);

  const fetchMembers = async () => {
    try {
      const res = await api.getProjectMembers(uid, 1, 100);
      if (res.ok) {
        const data = await res.json();
        // Map backend members (including loaded user relation) to UI
        const mapped: Member[] = (data.items || []).map((m: any) => ({
          uid: String(m.uid),
          user_uid: String(m.user_uid),
          role: m.role as any,
          username: m.user?.username || '',
          email: m.user?.email || '',
          joined_at: m.joined_at,
        }));
        setMembers(mapped);
      }
    } catch (err) {
      console.error('Error fetching members:', err);
    }
  };

  const handleAddMember = async (searchInput: string, role: 'admin' | 'member') => {
    try {
      // 1. Search for user by email/username
      const searchRes = await api.searchUsers(searchInput);
      if (!searchRes.ok) {
        alert('User search failed');
        return;
      }

      const users = await searchRes.json();
      if (users.length === 0) {
        alert('No user found with that username or email address.');
        return;
      }

      // 2. Select the first matching user
      const userToAdd = users[0];

      // 3. Add user as member to project
      const addRes = await api.addMember(uid, {
        user_uid: userToAdd.uid,
        role: role,
      });

      if (addRes.ok) {
        // Refresh members list
        await fetchMembers();
      } else {
        const err = await addRes.json();
        alert(err.message || err.detail || 'Failed to add member');
      }
    } catch (err) {
      console.error('Error adding member:', err);
    }
  };

  const handleRemoveMember = async (userUid: string) => {
    try {
      const res = await api.removeMember(uid, userUid);
      if (res.ok) {
        // Refresh members list
        await fetchMembers();
      } else {
        const err = await res.json();
        alert(err.message || err.detail || 'Failed to remove member');
      }
    } catch (err) {
      console.error('Error removing member:', err);
    }
  };

  const handleBackToBoard = () => {
    router.push(`/projects/${uid}`);
  };

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-background">
        <div className="text-center">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent mx-auto"></div>
          <p className="mt-4 text-muted-foreground">Loading members list...</p>
        </div>
      </div>
    );
  }

  return (
    <ProjectMembers
      projectName={projectName}
      members={members}
      onAddMember={handleAddMember}
      onRemoveMember={handleRemoveMember}
      onBackToBoard={handleBackToBoard}
    />
  );
}
