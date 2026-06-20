import { LifestyleType } from '@/api/auth'

export interface OccupationConfig {
  id: LifestyleType;
  label: string;
  minAge?: number;
  maxAge?: number;
}

export const OCCUPATIONS: OccupationConfig[] = [
  { id: 'student', label: 'Student', minAge: 0, maxAge: 59 },
  { id: 'professional', label: 'Working Professional', minAge: 18, maxAge: 59 },
  { id: 'homemaker', label: 'Homemaker', minAge: 18, maxAge: 59 },
  { id: 'house_helper', label: 'House Helper', minAge: 18, maxAge: 59 },
  { id: 'self_employed', label: 'Self-Employed', minAge: 18, maxAge: 59 },
  { id: 'business_owner', label: 'Business Owner', minAge: 18, maxAge: 59 },
  { id: 'retired', label: 'Retired', minAge: 60 },
  { id: 'consultant', label: 'Consultant', minAge: 60 },
]

/**
 * Helper to check if an occupation is valid for a given age
 */
export function isOccupationValidForAge(occupationId: LifestyleType, age: number | undefined | ''): boolean {
  if (age === undefined || age === '') return true; // Without age, assume true to let user select
  const config = OCCUPATIONS.find(o => o.id === occupationId);
  if (!config) return false;
  if (config.minAge !== undefined && age < config.minAge) return false;
  if (config.maxAge !== undefined && age > config.maxAge) return false;
  return true;
}

/**
 * Returns a tooltip message explaining why an occupation is locked
 */
export function getOccupationLockReason(occupationId: LifestyleType): string | undefined {
  const config = OCCUPATIONS.find(o => o.id === occupationId);
  if (!config) return undefined;
  if (config.minAge !== undefined && config.maxAge !== undefined) {
    return `Available only for users aged ${config.minAge} to ${config.maxAge}.`;
  }
  if (config.minAge !== undefined) {
    return `Available only for users aged ${config.minAge} and above.`;
  }
  if (config.maxAge !== undefined) {
    return `Available only for users up to age ${config.maxAge}.`;
  }
  return undefined;
}
