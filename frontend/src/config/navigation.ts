import {
  BookOpen,
  Flag,
  LayoutDashboard,
  ListChecks,
  Shield,
  Trophy,
  UserRound,
} from "lucide-react";
import type { NavSection } from "../types/navigation";

/** Same destinations and order as the Jinja sidebar in templates/base.html. */
export const navigation: NavSection[] = [
  {
    items: [
      { label: "Dashboard", href: "/dashboard", icon: LayoutDashboard },
      { label: "Challenges", href: "/challenges", icon: Flag, match: "prefix" },
      { label: "Scoreboard", href: "/leaderboard", icon: Trophy },
      { label: "Profile", href: "/profile", icon: UserRound },
      { label: "Docs", href: "/docs", icon: BookOpen },
    ],
  },
  {
    title: "Admin",
    adminOnly: true,
    items: [
      { label: "Admin Panel", href: "/admin", icon: Shield },
      { label: "Manage Challenges", href: "/admin/challenges", icon: ListChecks, match: "prefix" },
    ],
  },
];
