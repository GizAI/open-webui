// company.ts
import { WEBUI_API_BASE_URL } from '$lib/constants';

export const deleteCompanyBookmark = async (id: string): Promise<{ success: boolean; data?: any; error?: string }> => {
  try {
    const response = await fetch(`${WEBUI_API_BASE_URL}/rooibos/mycompanies/${id}/softdelete`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.token}`
      }
    });

    const data = await response.json();

    if (response.ok) {
      return { success: true, data };
    } else {
      console.error('Delete failed:', data);
      return { success: false, error: data.error || 'Unknown error', data };
    }
  } catch (error) {
    console.error('Error in deleteCompanyBookmark:', error);
    return { success: false, error: 'An unexpected error occurred while deleting the bookmark.' };
  }
};

export const permanentDeleteCompanyBookmark = async (id: string): Promise<{ success: boolean; data?: any; error?: string }> => {
  try {
    const response = await fetch(`${WEBUI_API_BASE_URL}/rooibos/mycompanies/${id}/delete`, {
      method: 'DELETE',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.token}`
      }
    });

    const data = await response.json();

    if (response.ok) {
      return { success: true, data };
    } else {
      console.error('Permanent delete failed:', data);
      return { success: false, error: data.error || 'Unknown error', data };
    }
  } catch (error) {
    console.error('Error in permanentDeleteCompanyBookmark:', error);
    return { success: false, error: 'An unexpected error occurred while permanently deleting the bookmark.' };
  }
};

export const restoreCompanyBookmark = async (id: string): Promise<{ success: boolean; data?: any; error?: string }> => {
  try {
    const response = await fetch(`${WEBUI_API_BASE_URL}/rooibos/mycompanies/${id}/restore`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.token}`
      }
    });

    const data = await response.json();

    if (response.ok) {
      return { success: true, data };
    } else {
      console.error('Restore failed:', data);
      return { success: false, error: data.error || 'Unknown error', data };
    }
  } catch (error) {
    console.error('Error in restoreCompanyBookmark:', error);
    return { success: false, error: 'An unexpected error occurred while restoring the bookmark.' };
  }
};

export const findUserById = async (userId: string): Promise<{ success: boolean; data?: any; error?: string }> => {
  try {
    const response = await fetch(`${WEBUI_API_BASE_URL}/rooibos/mycompanies/user/find-by-id/${userId}`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${localStorage.token}`
      }
    });

    const data = await response.json();

    if (response.ok) {
      return { success: true, data: data.data };
    } else {
      console.error('Find user by ID failed:', data);
      return { success: false, error: data.error || 'Unknown error', data };
    }
  } catch (error) {
    console.error('Error in findUserById:', error);
    return { success: false, error: 'An unexpected error occurred while finding the user by ID.' };
  }
};

export const findUserByEmail = async (email: string): Promise<{ success: boolean; data?: any; error?: string }> => {
  try {
    const response = await fetch(`${WEBUI_API_BASE_URL}/rooibos/mycompanies/user/find-by-email/${encodeURIComponent(email)}`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${localStorage.token}`
      }
    });

    const data = await response.json();

    if (response.ok) {
      return { success: true, data: data.data };
    } else {
      console.error('Find user by email failed:', data);
      return { success: false, error: data.error || 'Unknown error', data };
    }
  } catch (error) {
    console.error('Error in findUserByEmail:', error);
    return { success: false, error: 'An unexpected error occurred while finding the user by email.' };
  }
};




  
