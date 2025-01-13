import { type Writable, writable } from 'svelte/store';

export const companyDetails: Writable<CompanySettings> = writable({});

type CompanySettings = {
    company_name?: string;
    address?: string;
    latitude?: string;
    longitude?: string;
    phone_number?: string;
    category?: string[];
    business_registration_number?: string;
    representative?: string;
    birthDate?: string;
    industry?: string;
    establishmentDate?: string;
    employee_count?: number;
    recent_sales?: number;
    recent_revenue?: number;
    recent_profit?: number;
    website?: string;
    distance_from_user?: number;
    bookmark_id?: string | null;

	
};

