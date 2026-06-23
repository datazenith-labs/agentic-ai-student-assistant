// src/components/layout/nav-items.ts
//
// Single source of truth for the sidebar nav. Edit labels/routes here, not
// in the Sidebar component. Lucide icon names come from https://lucide.dev/icons.
//
// Adding a new nav item: add an entry here AND create src/app/(app)/<href>/page.tsx
// or it will 404.

import {
  Home,
  MessageSquare,
  BookOpen,
  GraduationCap,
  Sparkles,
  MapPin,
  ListTodo,
  Upload,
  type LucideIcon,
} from "lucide-react";

export type NavItem = {
  label: string;
  href: string;
  icon: LucideIcon;
};

export const NAV_ITEMS: NavItem[] = [
  { label: "Home",                href: "/home",       icon: Home },
  { label: "Chat",                href: "/chat",       icon: MessageSquare },
  { label: "Exam Preparation",    href: "/exam-prep",  icon: BookOpen },
  { label: "Course Advisor",      href: "/advisor",    icon: GraduationCap },
  { label: "Learning & Strategy", href: "/learning",   icon: Sparkles },
  { label: "Campus Automation",   href: "/campus",     icon: MapPin },
  { label: "Tasks & Reminders",   href: "/tasks",      icon: ListTodo },
  { label: "Upload Center",       href: "/uploads",    icon: Upload },
];

// Mock recent chats — replaced with real data in Phase 12.5/12.7.
export type RecentChat = {
  id: string;
  title: string;
  timestamp: string;
};

export const MOCK_RECENT_CHATS: RecentChat[] = [
  { id: "1", title: "Data Structures Quiz",    timestamp: "2 min ago"  },
  { id: "2", title: "Revision Plan for Exam",  timestamp: "1 hour ago" },
  { id: "3", title: "AI Course Recommendation", timestamp: "Yesterday"  },
  { id: "4", title: "Timetable for Next Week", timestamp: "2 days ago" },
  { id: "5", title: "DBMS Mock Exam",          timestamp: "3 days ago" },
];