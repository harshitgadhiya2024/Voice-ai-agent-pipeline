"use client";

import {
  Bed,
  Briefcase,
  GraduationCap,
  Home,
  Landmark,
  Plane,
  Receipt,
  ShoppingBag,
  Utensils,
  type LucideIcon,
} from "lucide-react";

const ICONS: Record<string, LucideIcon> = {
  home: Home,
  utensils: Utensils,
  "shopping-bag": ShoppingBag,
  briefcase: Briefcase,
  bed: Bed,
  landmark: Landmark,
  receipt: Receipt,
  plane: Plane,
  "graduation-cap": GraduationCap,
};

interface UseCaseIconProps {
  name: string;
  className?: string;
}

export function UseCaseIcon({ name, className }: UseCaseIconProps) {
  const Icon = ICONS[name] ?? Home;
  return <Icon className={className} />;
}
