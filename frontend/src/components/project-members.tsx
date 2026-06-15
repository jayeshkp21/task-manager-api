'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { ArrowLeft, Trash2 } from 'lucide-react';

interface Member {
  uid: string;
  user_uid: string;
  role: 'owner' | 'admin' | 'member';
  username?: string;
  email?: string;
  joined_at: string;
}

interface ProjectMembersProps {
  projectName: string;
  members: Member[];
  onAddMember?: (userUid: string, role: 'admin' | 'member') => void;
  onRemoveMember?: (userUid: string) => void;
  onBackToBoard?: () => void;
}

export function ProjectMembers({
  projectName,
  members,
  onAddMember,
  onRemoveMember,
  onBackToBoard,
}: ProjectMembersProps) {
  const [searchInput, setSearchInput] = useState('');
  const [selectedRole, setSelectedRole] = useState<'admin' | 'member'>('member');
  const [isAdding, setIsAdding] = useState(false);

  const handleAddMember = () => {
    if (!searchInput.trim()) return;
    setIsAdding(true);
    setTimeout(() => {
      onAddMember?.(searchInput, selectedRole);
      setSearchInput('');
      setSelectedRole('member');
      setIsAdding(false);
    }, 500);
  };

  const handleRemoveMember = (userUid: string) => {
    onRemoveMember?.(userUid);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && searchInput.trim()) {
      handleAddMember();
    }
  };

  const formatDate = (dateString: string) => {
    try {
      const date = new Date(dateString);
      return date.toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric',
        year: 'numeric',
      });
    } catch {
      return dateString;
    }
  };

  const getInitials = (username?: string, email?: string) => {
    if (username) {
      return username
        .split(' ')
        .map((n) => n[0])
        .join('')
        .toUpperCase()
        .slice(0, 2);
    }
    if (email) {
      return email[0].toUpperCase();
    }
    return 'U';
  };

  const getRoleBadgeVariant = (role: string) => {
    switch (role) {
      case 'owner':
        return 'default';
      case 'admin':
        return 'secondary';
      case 'member':
        return 'outline';
      default:
        return 'outline';
    }
  };

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b bg-card">
        <div className="flex items-center justify-between p-6 max-w-6xl mx-auto">
          <div className="flex items-center gap-4">
            <button
              onClick={onBackToBoard}
              className="p-2 hover:bg-muted rounded-md transition-colors"
              aria-label="Back to board"
            >
              <ArrowLeft className="h-5 w-5" />
            </button>
            <div>
              <h1 className="text-2xl font-bold text-foreground">{projectName}</h1>
              <p className="text-sm text-muted-foreground">Manage project members</p>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="p-6 max-w-6xl mx-auto space-y-6">
        {/* Add Member Section */}
        <div className="bg-card rounded-lg border p-6 space-y-4">
          <h2 className="text-lg font-semibold text-foreground">Add Member</h2>
          <div className="flex gap-3 flex-col sm:flex-row">
            <Input
              placeholder="Search by username or email"
              value={searchInput}
              onChange={(e) => setSearchInput(e.target.value)}
              onKeyDown={handleKeyDown}
              className="flex-1 min-w-0"
              disabled={isAdding}
            />
            <Select value={selectedRole} onValueChange={(value: any) => setSelectedRole(value)} disabled={isAdding}>
              <SelectTrigger className="w-full sm:w-32">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="member">Member</SelectItem>
                <SelectItem value="admin">Admin</SelectItem>
              </SelectContent>
            </Select>
            <Button
              onClick={handleAddMember}
              disabled={!searchInput.trim() || isAdding}
              className="w-full sm:w-auto"
            >
              {isAdding ? 'Adding...' : 'Add Member'}
            </Button>
          </div>
        </div>

        {/* Members Table */}
        <div className="bg-card rounded-lg border overflow-hidden">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Member</TableHead>
                <TableHead>Role</TableHead>
                <TableHead>Joined</TableHead>
                <TableHead className="w-12 text-right">Action</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {members.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={4} className="text-center py-8 text-muted-foreground">
                    No members yet
                  </TableCell>
                </TableRow>
              ) : (
                members.map((member) => (
                  <TableRow key={member.uid}>
                    <TableCell>
                      <div className="flex items-center gap-3">
                        <Avatar className="h-8 w-8">
                          <AvatarFallback className="text-xs">
                            {getInitials(member.username, member.email)}
                          </AvatarFallback>
                        </Avatar>
                        <div className="flex flex-col gap-0.5">
                          <p className="text-sm font-medium text-foreground">
                            {member.username || member.email || 'Unknown'}
                          </p>
                          {member.username && member.email && (
                            <p className="text-xs text-muted-foreground">{member.email}</p>
                          )}
                        </div>
                      </div>
                    </TableCell>
                    <TableCell>
                      <Badge variant={getRoleBadgeVariant(member.role)} className="capitalize">
                        {member.role}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-sm text-muted-foreground">
                      {formatDate(member.joined_at)}
                    </TableCell>
                    <TableCell className="text-right">
                      <button
                        onClick={() => handleRemoveMember(member.user_uid)}
                        disabled={member.role === 'owner'}
                        className="p-2 hover:bg-destructive/10 hover:text-destructive disabled:opacity-50 disabled:cursor-not-allowed transition-colors rounded-md"
                        aria-label="Remove member"
                        title={member.role === 'owner' ? 'Cannot remove project owner' : 'Remove member'}
                      >
                        <Trash2 className="h-4 w-4" />
                      </button>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </div>

        {/* Members Count */}
        {members.length > 0 && (
          <div className="text-sm text-muted-foreground">
            Total members: <span className="font-medium text-foreground">{members.length}</span>
          </div>
        )}
      </main>
    </div>
  );
}
